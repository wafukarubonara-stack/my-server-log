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

## 自動実行スケジュール

| タイミング | 処理 | 所要時間 |
|---|---|---|
| `apt upgrade` 実行後 | AIDEスキャン + GitHub送信 | 1〜5分 |
| 毎週日曜日 午前1時 | ClamAVスキャン | 10〜30分 |
| 毎週日曜日 午前2時 | ClamAV結果のGitHub送信 | 数秒 |

**注意**: 電源オフ時は実行されません。

## セキュリティレベル

Windows 10/11のデフォルト設定と同等：
- ✅ システムファイル改ざん検知（AIDE）
- ✅ 週1回のウイルススキャン（ClamAV）
- ✅ システム更新時の整合性チェック（AIDE）

## 関連スクリプト

### AIDE
- `/usr/local/bin/aide-update-git.sh` - メインスクリプト
- `/etc/apt/apt.conf.d/99aide-post-install` - APT連動設定

### ClamAV
- `/usr/local/bin/clamav-scan.sh` - スキャンスクリプト（最適化済み）
- `/usr/local/bin/clamscan-update-git.sh` - GitHub送信スクリプト

## スキャン最適化

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
- **必要パッケージ**: `python3-matplotlib`

```bash
sudo apt install python3-matplotlib
```

## 手動実行

### AIDE
```bash
# スキャン実行
sudo /usr/local/bin/aide-update-git.sh

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
他のAIDEプロセスが実行中です。
```bash
# プロセス確認
ps aux | grep aide

# 完了を待ってから再実行
sudo /usr/local/bin/aide-update-git.sh
```

### ClamAVスキャンが遅い
現在の設定は最適化済み（10〜30分）です。さらに高速化したい場合：
```bash
# スキャン対象を主要ディレクトリのみに限定
# /usr/local/bin/clamav-scan.sh を編集
```

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
