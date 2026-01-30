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
  ```bash
  sudo /usr/local/bin/aide-update-git.sh
  ```

---

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
  ```

## 使い方
以下のコマンドを実行すると、execution_time.txt を解析し、aide_execution_trend.png を更新します。
```bash
python3 visualize_aide.py
```

## 自動化について
`/usr/local/bin/aide-update-git.sh` によって、システムアップデート時に自動的にスキャン・可視化・GitHubへのPushが行われるよう設定されています。

## 更新履歴
### 2026/01/30
- README.mdのフォーマットを整理

### 2026/01/16
- **APT連動スクリプトをバックグラウンド実行に変更**
  - `/etc/apt/apt.conf.d/99aide-post-install` の設定を更新
  - `DPkg::Post-Invoke` でスクリプトをバックグラウンド実行（`&`）するよう変更
  - これにより、`apt upgrade` の処理が即座に完了し、AIDEスキャンは裏で実行されます
  - APTのロック待ちを回避し、システム管理作業がスムーズになりました
- 実行時間可視化スクリプト（`visualize_aide.py`）を追加
- スクリプト動作記録（`script_usage.log`）の管理を開始
