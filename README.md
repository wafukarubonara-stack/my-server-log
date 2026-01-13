# AIDE 監査ログ管理システム
このリポジトリは、Inspiron 7370 のファイル改ざん検知（AIDE）の結果を自動保存する場所です。

## 仕組み
1. `apt upgrade` 実行後に `/usr/local/bin/aide-update-git.sh` が自動発動。
2. AIDEがスキャンを実行し、データベースを更新。
3. 実行結果（`aide_report.txt`）と計測時間（`execution_time.txt`）をこのリポジトリに送信。

## 関連ファイル
- **スクリプト本体:** `/usr/local/bin/aide-update-git.sh`
- **APT連動設定:** `/etc/apt/apt.conf.d/99aide-post-install`

## トラブルシューティング
- **Status 21 (Resource temporarily unavailable):**
  他のAIDEプロセスが動いているため失敗。`ps aux | grep aide` で確認し、終わるのを待ってから手動実行：
  `sudo /usr/local/bin/aide-update-git.sh`
