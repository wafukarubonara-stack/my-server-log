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

### AIDE関連
- `aide_report.txt`: AIDEの最新スキャン結果
- `execution_time.txt`: 実行にかかった時間の履歴データ
- `visualize_aide.py`: 実行時間をグラフ化するPythonスクリプト
- `aide_execution_trend.png`: 生成された推移グラフ
- `script_usage.log`: スクリプトの動作記録

### ClamAV関連（ウイルススキャン）
- `clamscan_report.txt`: ClamAVの最新スキャン結果サマリー
- `clamscan_time.txt`: スキャン実行時間の履歴データ

## 動作環境
- **OS**: Ubuntu 24.04 LTS (または Python 3.12 が動作する環境)
- **言語**: Python 3.12+
- **必要パッケージ**: 
  - `python3-matplotlib` (システムの安定性のため、APT経由でのインストールを推奨)
  ```bash
  sudo apt install python3-matplotlib
  ```

## 使い方

### AIDE可視化
以下のコマンドを実行すると、execution_time.txt を解析し、aide_execution_trend.png を更新します。
```bash
python3 visualize_aide.py
```

## 自動化について

### AIDE
`/usr/local/bin/aide-update-git.sh` によって、システムアップデート時に自動的にスキャン・可視化・GitHubへのPushが行われるよう設定されています。

### ClamAV
毎日自動でウイルススキャンを実行し、結果をGitHubに記録します：
- **午前1時**: スキャン実行（`/usr/local/bin/clamav-scan.sh`）
  - スキャン対象: `/home/eliza`
  - 除外ディレクトリ: キャッシュ、ブラウザデータ、開発ツール等
  - 実行時間: 約10〜30分（最適化済み）
- **午前2時**: GitHub自動送信（`/usr/local/bin/clamscan-update-git.sh`）

## セキュリティレベル
- **AIDE**: ファイル改ざん検知（インテグリティチェック）
- **ClamAV**: ウイルス・マルウェアスキャン（Windows Defender相当）

## 更新履歴

### 2026/01/31
- **ClamAVスキャンの自動記録機能を追加**
  - 毎日午前1時に最適化されたスキャンを実行
  - 不要なディレクトリを除外し、スキャン時間を大幅短縮（20時間 → 10〜30分）
  - スキャン結果をGitHubに自動送信
  - Windows並みのセキュリティレベルを維持

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
