# AIDE Routine 連携 — 実装記録（完了）

## 状態（2026-06-14 完了）

AIDE 軽量化 + Claude Code Routine 連携プロジェクト完了。週次 fire API → Gmail 下書きに AI トリアージ通知という運用形態を確立。

設計の出典: `aide-routine-handover.md`

---

## 達成内容

- 検出件数: 2,494 → **5 件**（**-99.8%**）
- ステータス: CRITICAL → **OK**
- レポートサイズ: 60,000 字切り捨て → 3,231 バイト（実質全件分析可能）
- aideinit 時間: 5:36 / DB 73MB（Phase 3 前 91MB から 20% 減）

## 完了したステップ

- [x] **Step 1**: `/etc/aide/routine.env` 作成（600 root:root）
- [x] **Step 2**: 旧 `aide-check` を `/root/aide-check.bak.20260613` に退避
- [x] **Step 3**: 新版 cron.weekly/aide-check 設置（64 行、`export AIDE_RC` バグ修正済み）
- [x] **Step 4**: fire API スモークテスト → HTTP 200 + session_url
- [x] **Step 5**: 本番手動フル実行（Phase 4 前）→ 2,494 件 / CRITICAL（誤判定）
- [x] **Phase 4**: 追加除外 + aideinit による新ベースライン生成
- [x] **Phase 4 後検証**: 手動実行 → 5 件 / OK / 推奨アクション「対応不要」

## Phase 4 で追加した除外（aide.conf 末尾、2026-06-14 適用）

```
!/run                                 # 最大ノイズ源（!/var/run だけでは /run 実体が漏れる）
!/dev/disk/by-loop-ref
!/dev/disk/by-loop-inode
!/home/eliza/\.claude                 # Claude Code セッション
!/home/eliza/\.local/share
!/home/eliza/\.config/google-chrome   # Profile X/Service Worker のスペース問題ごと回避
!/var/spool/postfix
!/var/snap
!/var/lib/AccountsService
!/var/lib/fwupd
!/var/lib/gdm3
!/var/lib/upower
!/var/lib/ubuntu-advantage
```

## 残った 5 件の benign LOW

毎週変わるが対応不要：

- `/home/eliza/.local/state/wireplumber` — 音声セッション状態
- `/home/eliza/.local/state/wireplumber/restore-stream` — 同上、再生成あり
- `/home/eliza/my-server-log/aide_report.txt` — AIDE 自身のレポート出力
- `/home/eliza/my-server-log/execution_time.txt` — AIDE 実行時間ログ
- `/home/eliza/security/port-monitor.log` — ポート監視ログの追記

完全に消したい場合は Phase 5 候補：

```
!/home/eliza/\.local/state
!/home/eliza/my-server-log
!/home/eliza/security/.*\.log
```

## 重要な制約（変更しない）

- curl にリトライ追加禁止（多重セッション化）
- `aide --update` をスクリプトに組み込まない（改ざんの自動正規化リスク）
- jq エスケープは `--rawfile` 必須（sed エスケープ禁止）
- ROUTINE_TOKEN は chat に貼らない・git に含めない
- `anthropic-beta: experimental-cc-routine-2026-04-01` は実験版ヘッダ。400 が返り始めたらバージョン更新を疑う

## 既知の Gmail MCP 仕様

- Routine は `create_draft` のみ可能。直接 send はできない
- 通知は Gmail の「下書き」フォルダに作成される（受信トレイには来ない）
- スマホ Push なし。週次運用なので大きな問題ではない

## 任意の Step 6: フォールバック試験

routine.env の TOKEN を一時的に壊して実行 → 生レポートメールが /var/mail/eliza に届くことを確認。

```bash
sudo sed -i.tmp 's/ROUTINE_TOKEN="sk-/ROUTINE_TOKEN="BROKEN-sk-/' /etc/aide/routine.env
sudo touch /etc/test-aide-trigger
sudo /etc/cron.weekly/aide-check
grep -E '^Subject:' /var/mail/eliza | tail -3
# 期待: "[AIDE] 変更検出 (rc=非ゼロ) - ルーチン起動失敗 HTTP=..."

# 後始末
sudo mv /etc/aide/routine.env.tmp /etc/aide/routine.env
sudo rm /etc/test-aide-trigger
sudo -u _aide aide --config /etc/aide/aide.conf --update
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
sudo chown _aide:_aide /var/lib/aide/aide.db
```

## 関連ファイル

- 設計書: `aide-routine-handover.md`（同ディレクトリ）
- AIDE 軽量化プラン: `/home/eliza/.claude/plans/pc-aide-pc-goofy-trinket.md`
- AIDE 軽量化メモリ: `/home/eliza/.claude/projects/-home-eliza/memory/project_aide.md`
- 本プロジェクトメモリ: `/home/eliza/.claude/projects/-home-eliza/memory/project_aide_routine.md`
- 新スクリプト: `/etc/cron.weekly/aide-check`（64 行、設置済み）
- シークレット: `/etc/aide/routine.env`（600 root:root、設置済み）
- 旧スクリプト退避: `/root/aide-check.bak.20260613`
- AIDE 設定: `/etc/aide/aide.conf`（sha256+sha512, num_workers=6, Phase 3/4 除外 適用済み）
- レポート出力: `/var/log/aide/report-YYYY-MM-DD.log`
- API レスポンス: `/var/log/aide/fire-response.json`
- DB バックアップ: `/var/lib/aide/aide.db.bak.{phase3.20260611,phase4.20260614}`
- aide.conf バックアップ: `/etc/aide/aide.conf.bak.{20260611,phase3.20260611,phase4.20260614}`
