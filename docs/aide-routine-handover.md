# 引き継ぎ資料: AIDE週次チェック → Claude Codeルーチン(API trigger)連携

## 背景とゴール

- ホスト: Ubuntu (eliza-Inspiron-7370)
- 現状: `/etc/cron.weekly/aide-check` が `aide --check | mail root` を直結実行している
- ゴール: AIDEレポートをファイル保存し、Claude Codeルーチンの fire API に POST して
  クラウド側でトリアージ+Gmail送信させる。API失敗時はローカルから生レポートをメール送信する
  (アラートを絶対に落とさないフォールバック構造)

## 前提(人間が用意済みの値)

作業開始前に以下をユーザーに確認すること:

- `ROUTINE_ID`: ルーチンのID(`trig_` プレフィックス)
- `ROUTINE_TOKEN`: Bearerトークン(`sk-ant-oat01-` プレフィックス)
- `MAILTO`: フォールバック送信先(root宛+aliasesか直接Gmailか)
- ローカルMTA(msmtp等)が設定済みで `mail` コマンドが配送可能か。
  未設定なら msmtp-mta の導入もこの作業に含める(Gmailアプリパスワードは人間に入力させる。
  チャット/ファイルに残さない)

## タスク1: シークレットファイルの作成

`/etc/aide/routine.env` を作成:

```bash
ROUTINE_ID="trig_xxxxxxxx"
ROUTINE_TOKEN="sk-ant-oat01-xxxxxxxx"
```

- 所有者 root:root、パーミッション 600
- トークン値はユーザーに対話的に入力してもらう。コマンド履歴に残さないこと
  (`read -rs` で受けるか、エディタで直接編集してもらう)

## タスク2: cron スクリプトの置き換え

`/etc/cron.weekly/aide-check` を以下の内容に置き換える(既存はバックアップ:
`/etc/cron.weekly/aide-check.bak` ではなく `/root/aide-check.bak` に退避。
cron.weekly 内に置くと run-parts が拾う恐れがあるため):

```bash
#!/bin/bash
set -uo pipefail

AIDE_CONFIG="/etc/aide/aide.conf"
LOG_DIR="/var/log/aide"
REPORT="$LOG_DIR/report-$(date +%F).log"
MAILTO="root"

# シークレット読み込み
source /etc/aide/routine.env
FIRE_URL="https://api.anthropic.com/v1/claude_code/routines/${ROUTINE_ID}/fire"

mkdir -p "$LOG_DIR"
chmod 750 "$LOG_DIR"

# 二重実行防止
exec 9>/var/lock/aide-check.lock
if ! flock -n 9; then
    echo "AIDE is already running. Skipping." \
      | mail -s "[AIDE] Weekly Check Skipped" "$MAILTO"
    exit 0
fi

# 1. AIDE実行(変更検出時は非ゼロ終了)
/usr/bin/aide --config "$AIDE_CONFIG" --check > "$REPORT" 2>&1
AIDE_RC=$?
chmod 640 "$REPORT"

# 2. 変更なしなら短報のみ(ルーチンの実行回数を消費しない)
if [ "$AIDE_RC" -eq 0 ]; then
    echo "変更なし (exit 0)" | mail -s "[AIDE] OK $(hostname)" "$MAILTO"
    exit 0
fi

# 3. ペイロード作成: textは65,536文字上限なので60,000文字で切る
#    jq --rawfile で安全にJSONエスケープする(手組みのsedエスケープは禁止)
PAYLOAD=$(jq -n --rawfile r "$REPORT" \
  '{text: ("AIDE週次レポート " + (now|strftime("%Y-%m-%d")) + " rc=" + env.AIDE_RC + "\n\n" + (.r[:60000]))}' \
  2>/dev/null) || PAYLOAD=""
export AIDE_RC

# 4. ルーチンをfire。リトライはしない(冪等性キーが無く多重セッションになるため)
HTTP_CODE=$(curl -s -o "$LOG_DIR/fire-response.json" -w "%{http_code}" \
  --max-time 60 -X POST "$FIRE_URL" \
  -H "Authorization: Bearer $ROUTINE_TOKEN" \
  -H "anthropic-version: 2023-06-01" \
  -H "anthropic-beta: experimental-cc-routine-2026-04-01" \
  -H "Content-Type: application/json" \
  --data "$PAYLOAD")

if [ "$HTTP_CODE" = "200" ] && [ -n "$PAYLOAD" ]; then
    SESSION_URL=$(jq -r '.claude_code_session_url // "n/a"' \
      "$LOG_DIR/fire-response.json")
    {
      echo "クラウドトリアージを起動しました。結果は別メールで届きます。"
      echo "セッション: $SESSION_URL"
      echo "原本: $REPORT"
    } | mail -s "[AIDE] 変更検出 (rc=$AIDE_RC) - トリアージ起動" "$MAILTO"
else
    # フォールバック: 生レポートを必ず送る
    mail -s "[AIDE] 変更検出 (rc=$AIDE_RC) - ルーチン起動失敗 HTTP=$HTTP_CODE" \
      "$MAILTO" < "$REPORT"
fi
```

- パーミッション 755、所有者 root、ファイル名に拡張子を付けない(run-parts の制約)
- 依存: `jq`, `curl`。未導入なら `apt install jq curl`

## タスク3: テスト(この順で)

1. `bash -n /etc/cron.weekly/aide-check` で構文チェック
2. fire API単体テスト: 短いダミーtextでPOSTし、HTTP 200と
   `claude_code_session_url` が返ることを確認。ユーザーにそのURLを開いて
   セッション実行とGmail着信を確認してもらう
3. `sudo run-parts --test /etc/cron.weekly` でスクリプトが列挙されることを確認
4. `sudo /etc/cron.weekly/aide-check` をフル手動実行。
   変更がない場合はテスト用に `touch /etc/test-aide-trigger` で意図的に変更を作り、
   検証後に削除して `aide --update` でDBを更新する
5. フォールバック試験: routine.env のトークンを一時的に壊して実行し、
   生レポートメールが届くことを確認。終わったら戻す

## 注意事項(変更しないこと)

- curlにリトライを足さない(多重セッション化する)
- `--dangerously-skip-permissions` 等は無関係(ローカルでclaudeは実行しない)
- aide --update をこのスクリプトに組み込まない(改ざんの自動正規化になるため、
  DB更新は人間が判断して手動実行する)
- レポートのtext送信はAnthropicクラウドにデータが渡る。ユーザーから
  マスキング要望があれば、curl前に sed でホスト名・特定パスを置換する処理を挟む
- fire APIは実験的(anthropic-betaヘッダー: experimental-cc-routine-2026-04-01)。
  400が返り始めたらヘッダーのバージョン更新を疑う

## 完了条件

- [ ] routine.env が 600/root で存在し、git等に含まれていない
- [ ] 手動フル実行でトリアージメールがGmailに届いた
- [ ] フォールバック経路で生レポートメールが届いた
- [ ] テスト用の改変を掃除し、AIDE DBがクリーンな状態に戻っている
