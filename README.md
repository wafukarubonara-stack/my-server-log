# サーバーセキュリティ監視システム

このリポジトリは、Inspiron 7370（Ubuntu 24.04）のセキュリティ監視結果を自動記録する場所です。

## 監視内容

- **AIDE**: ファイル改ざん検知（システムファイルの変更を検出）
- **ClamAV**: ウイルス・マルウェアスキャン（Windows Defender相当）

## 構成ファイル

### AIDE関連
- `aide_report.txt` - 最新のスキャン結果
- `execution_time.txt` - 実行時間の履歴
- `visualize_aide.py` - 実行時間グラフ化スクリプト
- `aide_execution_trend.png` - 推移グラフ
- `script_usage.log` - 動作記録

### ClamAV関連
- `clamscan_report.txt` - 最新のスキャン結果サマリー
- `clamscan_time.txt` - 実行時間の履歴

### ドキュメント
- `SECURITY_CONFIG.md` - セキュリティ設定詳細
- `docs/aide-routine-handover.md` - AIDE → Claude Code Routine 連携設計書
- `docs/aide-routine-implementation.md` - 実装記録（Phase 1〜4 完了）

## 自動実行スケジュール

| タイミング | 処理 | 所要時間 |
|---|---|---|
| `apt upgrade` 実行後 30分遅延 | AIDE `--update` + GitHub送信（path unit 経由） | 5〜15分（背景実行） |
| 毎週日曜日 6:25頃 | AIDE `--check` + Routine 通知 / フォールバックメール | 10〜15分（低優先度） |
| 毎週日曜日 午前1時 | ClamAVスキャン | 10〜30分 |
| 毎週日曜日 午前2時 | ClamAV結果のGitHub送信 | 数秒 |

**注意**: 電源オフ時は実行されません。

## セキュリティレベル

Windows 10/11 のデフォルト設定と同等以上：
- ✅ システムファイル改ざん検知（AIDE）
- ✅ 週1回のウイルススキャン（ClamAV）
- ✅ システム更新時の整合性チェック（AIDE）
- ✅ 週次 AIDE 結果の AI トリアージ通知（Claude Code Routine）

## 関連スクリプト

### AIDE
- `/usr/local/bin/aide-update-git.sh` - apt連動 update スクリプト（flock + 6時間デバウンス + nice/ionice）
- `/etc/apt/apt.conf.d/99aide-post-install` - APT連動設定（マーカー touch のみ）
- `/etc/systemd/system/aide-apt-trigger.path` - マーカー監視
- `/etc/systemd/system/aide-apt-trigger.service` - 30分遅延 + 低優先度実行
- `/etc/cron.weekly/aide-check` - 週次 check + Claude Code Routine fire API 連携
- `/etc/aide/routine.env` - Routine ID / Token（**git に含めない、600 root:root**）

### ClamAV
- `/usr/local/bin/clamav-scan.sh` - スキャンスクリプト（最適化済み）
- `/usr/local/bin/clamscan-update-git.sh` - GitHub送信スクリプト

## スキャン最適化

### AIDE 軽量化（2026-06-11 完了）
- ハッシュ: 全ハッシュ方式 → **sha256+sha512** のみ
- 並列化: `num_workers=6`（8コア中6本）
- 除外: `.cache`, `.gradle`, `.npm`, Firefox/Chrome キャッシュ, `node_modules`, `build`, AIDE 自身の DB 等
- 結果: フルチェック 62分 → **5〜11分**、apt 後ロック解消

### AIDE ノイズ抑制（2026-06-14 完了）
- 追加除外: `/run`, `/home/eliza/.claude`, `/home/eliza/.config/google-chrome`, デーモン state（postfix, snap, fwupd, gdm3, upower, ubuntu-advantage, AccountsService）
- 結果: 検出件数 2,494 → **5 件**（-99.8%）、ステータス CRITICAL → OK

### ClamAVで除外されるディレクトリ
スキャン時間短縮のため、以下を除外しています：
- キャッシュファイル (`.cache`, `.npm`, `node_modules`)
- ブラウザデータ (`.mozilla`, `.config/google-chrome`)
- 開発ツール (`.vscode`, `.cargo`, `.rustup`)
- システムパッケージ (`snap`, `.var`)

**重要**: ダウンロードフォルダ、ドキュメント、デスクトップは**スキャンされます**。

## 動作環境

- **OS**: Ubuntu 24.04 LTS
- **言語**: Python 3.12+
- **必要パッケージ**: `python3-matplotlib`, `jq`, `curl`

```bash
sudo apt install python3-matplotlib jq curl
```

## 手動実行

### AIDE
```bash
# apt連動の update スクリプト（DB 更新含む）
sudo /usr/local/bin/aide-update-git.sh

# 週次 check（DB 更新せず、Routine 通知のみ）
sudo /etc/cron.weekly/aide-check

# グラフ生成のみ
python3 visualize_aide.py
```

### ClamAV
```bash
# スキャン実行
sudo /usr/local/bin/clamav-scan.sh

# GitHub送信
sudo /usr/local/bin/clamscan-update-git.sh
```

## トラブルシューティング

### AIDEエラー: "Resource temporarily unavailable"
他のAIDEプロセスが実行中です。flock で排他されているので、終わるまで待ちます。
```bash
# プロセス確認
ps aux | grep aide

# 進捗確認
journalctl -t aide-update -f
```

### ClamAVスキャンが遅い
現在の設定は最適化済み（10〜30分）です。さらに高速化したい場合：
```bash
# スキャン対象を主要ディレクトリのみに限定
# /usr/local/bin/clamav-scan.sh を編集
```

### Routine 連携が動かない / Gmail 下書きが届かない
詳細は `docs/aide-routine-implementation.md` 参照。
- HTTP 401: ROUTINE_TOKEN 失効 → Routine 再作成
- HTTP 400: `anthropic-beta` ヘッダ古いかも → バージョン更新を疑う
- 失敗時は自動的に生レポートが /var/mail/eliza にフォールバック送信される

## カスタマイズ

### スキャン頻度の変更
```bash
# cron設定を編集
sudo crontab -e

# 例: 毎日実行したい場合
0 1 * * * /usr/local/bin/clamav-scan.sh  # 毎日午前1時

# 例: 月1回のみ
0 1 1 * * /usr/local/bin/clamav-scan.sh  # 毎月1日午前1時
```

## 更新履歴

### 2026/06/14
- **AIDE Phase 4 ノイズ抑制**: 検出件数 2,494 → 5（-99.8%）、ステータス OK で運用開始
- **Claude Code Routine 連携完了**: 週次 fire API → Gmail 下書きで AI トリアージ
- 引き継ぎ資料を `docs/` に追加

### 2026/06/11
- **AIDE 軽量化**: 62分 → 5〜11分（ハッシュ sha256+sha512、並列化 num_workers=6、除外追加）
- **APT 連動再設計**: path unit + 30分遅延 + 6時間デバウンス、apt 後ロック解消
- flock / nice / ionice / git push 失敗時のロガー追加

### 2026/01/31
- **ClamAVスキャンの自動記録機能を追加**
  - 週1回（日曜日）の自動スキャンを設定
  - 不要なディレクトリを除外し、スキャン時間を短縮（20時間 → 10〜30分）
  - スキャン結果をGitHubに自動記録
- **README改善**: プライベート利用に最適化した説明を追加

### 2026/01/30
- README.mdのフォーマットを整理

### 2026/01/16
- **APT連動スクリプトをバックグラウンド実行に変更**
  - `apt upgrade`の処理が即座に完了するよう改善
  - APTロック待ちを回避
- 実行時間可視化スクリプト（`visualize_aide.py`）を追加
- スクリプト動作記録の管理を開始
