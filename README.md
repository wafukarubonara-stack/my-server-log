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


#2026/01/16更新
# My Server AIDE Logs
このリポジトリは、Ubuntuサーバーの完全性チェックツール（AIDE）の実行ログと、その実行時間を可視化するためのツールを管理しています。

## 構成ファイル
- `aide_report.txt`: AIDEの最新スキャン結果
- `execution_time.txt`: 実行にかかった時間の履歴データ
- `visualize_aide.py`: 実行時間をグラフ化するPythonスクリプト
- `aide_execution_trend.png`: 生成された推移グラフ
- `script_usage.log`: スクリプトの動作記録

## 動作環境
- **OS**: Ubuntu 24.04 LTS (または Python 3.12 が動作する環境)
- **言語**: Python 3.12+
- **必要パッケージ**: 
  - `python3-matplotlib` (システムの安定性のため、APT経由でのインストールを推奨)
  ```bash
  sudo apt install python3-matplotlib

##使い方
以下のマンドを実行すると、execution_time.txt を解析し、aide_execution_trend.png を更新します。
  python3 visualize_aide.py

##自動化について
/usr/local/bin/aide-update-git.sh によって、システムアップデート時に自動的にスキャン・可視化・GitHubへのPushが行われるよう設定されています。
