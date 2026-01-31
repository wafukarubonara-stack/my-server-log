# セキュリティ設定ドキュメント

**最終更新**: 2026/01/31  
**対象システム**: Inspiron 7370 (Ubuntu 24.04 LTS)

---

## 概要

このドキュメントは、システムのセキュリティ設定を記録したものです。
Windowsレベル以上のセキュリティを、軽量な負荷で実現しています。

---

## 実装済みセキュリティ機能

### 1. ファイアウォール (ufw)

**状態**: アクティブ

#### 設定内容
```bash
# 確認コマンド
sudo ufw status

# 現在の設定
80/tcp    LIMIT    Anywhere        # HTTP (制限付き)
443/tcp   LIMIT    Anywhere        # HTTPS (制限付き)
53        ALLOW OUT Anywhere       # DNS
80        ALLOW OUT Anywhere       # HTTP送信
443       ALLOW OUT Anywhere       # HTTPS送信
```

#### 設定の意味
- **LIMIT**: 短時間に大量の接続を拒否（DDoS対策）
- **ALLOW OUT**: 外部への通信を許可
- 不要なポートは全てブロック

#### 復元方法
```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw limit 80/tcp
sudo ufw limit 443/tcp
```

---

### 2. 自動セキュリティアップデート

**状態**: 有効（毎日実行）

#### 設定ファイル
`/etc/apt/apt.conf.d/20auto-upgrades`
```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

#### 動作内容
- 毎日自動でパッケージリストを更新
- セキュリティアップデートを自動インストール

#### 確認方法
```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
```

---

### 3. ウイルススキャン (ClamAV)

#### 3-1. スキャンスクリプト

**場所**: `/usr/local/bin/clamav-scan.sh`

**内容**:
```bash
#!/bin/bash
# ClamAV 日次スキャンスクリプト（高速化版）
# 作成日: 2026/01/30

SCAN_DIR="/home/eliza"
LOG_FILE="/var/log/clamav/daily_scan.log"

# スキャン実行
# -r: 再帰的スキャン, -i: 感染ファイルのみ記録
clamscan -r -i \
  --exclude-dir="$SCAN_DIR/.cache" \
  --exclude-dir="$SCAN_DIR/.local/share/Trash" \
  --exclude-dir="$SCAN_DIR/.mozilla" \
  --exclude-dir="$SCAN_DIR/.config/google-chrome" \
  --exclude-dir="$SCAN_DIR/.config/chromium" \
  --exclude-dir="$SCAN_DIR/.vscode" \
  --exclude-dir="$SCAN_DIR/.vscode-server" \
  --exclude-dir="$SCAN_DIR/snap" \
  --exclude-dir="$SCAN_DIR/.npm" \
  --exclude-dir="$SCAN_DIR/.yarn" \
  --exclude-dir="$SCAN_DIR/node_modules" \
  --exclude-dir="$SCAN_DIR/.cargo" \
  --exclude-dir="$SCAN_DIR/.rustup" \
  --exclude-dir="$SCAN_DIR/.local/share/virtualenv" \
  --exclude-dir="$SCAN_DIR/.thunderbird" \
  --exclude-dir="$SCAN_DIR/.evolution" \
  --exclude-dir="$SCAN_DIR/.var" \
  "$SCAN_DIR" >> "$LOG_FILE"

echo "Scan completed at $(date)" >> "$LOG_FILE"
```

**実行権限**: `chmod +x /usr/local/bin/clamav-scan.sh`

#### 3-2. GitHub連動スクリプト

**場所**: `/usr/local/bin/clamscan-update-git.sh`

**内容**:
```bash
#!/bin/bash
# ClamAV結果をGitHubに自動送信するスクリプト
# 作成日: 2026/01/30

REPO_DIR="/home/eliza/my-server-log"
SCAN_LOG="/var/log/clamav/daily_scan.log"
CLAMSCAN_REPORT="$REPO_DIR/clamscan_report.txt"
CLAMSCAN_TIME="$REPO_DIR/clamscan_time.txt"

# リポジトリディレクトリに移動
cd "$REPO_DIR" || exit 1

# 最新のスキャン結果からサマリー部分のみ抽出
if [ -f "$SCAN_LOG" ]; then
    # 最後のSCAN SUMMARYセクションを抽出
    tail -n 100 "$SCAN_LOG" | sed -n '/----------- SCAN SUMMARY -----------/,$p' > "$CLAMSCAN_REPORT"
    
    # 実行時間も抽出（Time:行を探す）
    grep "Time:" "$CLAMSCAN_REPORT" >> "$CLAMSCAN_TIME"
fi

# Gitにコミット
git add clamscan_report.txt clamscan_time.txt
git commit -m "Update: ClamAV scan results ($(date +%Y/%m/%d))"

# GitHubにプッシュ
git push origin main

echo "ClamAV results pushed to GitHub successfully."
```

**実行権限**: `chmod +x /usr/local/bin/clamscan-update-git.sh`

#### 3-3. ClamAVデーモン

**状態**: 稼働中（待機状態）

```bash
# 状態確認
systemctl status clamav-daemon
systemctl status clamav-freshclam

# リソース使用状況（2026/01/31時点）
Memory: 959.3M (peak: 1.2G)
CPU: 14.544s (31分間で累計)
```

**注意**: リアルタイムスキャンは**無効**（パフォーマンス重視）

#### 3-4. ウイルス定義更新

**サービス**: clamav-freshclam  
**更新頻度**: 1時間ごと  
**最新バージョン**: daily.cld version: 27897 (2026/01/31時点)

#### 3-5. 自動実行スケジュール (cron)

```bash
# cron設定を確認
sudo crontab -l

# 現在の設定（2026/01/31時点）
0 1 * * 0 /usr/local/bin/clamav-scan.sh           # 毎週日曜日 午前1時
0 2 * * 0 /usr/local/bin/clamscan-update-git.sh   # 毎週日曜日 午前2時
```

---

### 4. ファイル改ざん検知 (AIDE)

#### 4-1. 自動実行スクリプト

**場所**: `/usr/local/bin/aide-update-git.sh`

**トリガー**: `apt upgrade` 実行後（バックグラウンド実行）

#### 4-2. APT連動設定

**場所**: `/etc/apt/apt.conf.d/99aide-post-install`

**内容**:
```bash
#// OSのパッケージ更新(apt upgrade)完了後に、AIDEのスキャンとGitHubへのログ出力を自動実行する
#DPkg::Post-Invoke {"/usr/local/bin/aide-update-git.sh"};

#2026/01/16更新
// スクリプトをバックグラウンド(&)で実行し、APTプロセスを即座に解放する
DPkg::Post-Invoke {"/usr/local/bin/aide-update-git.sh &"};
```

#### 4-3. GitHub連動

スキャン結果は自動的に `/home/eliza/my-server-log` にコミット・プッシュされます。

---

## GitHubリポジトリ構成

**リポジトリ**: `wafukarubonara-stack/my-server-log`  
**ブランチ**: main

### ファイル構成
```
my-server-log/
├── README.md                    # リポジトリの説明
├── SECURITY_CONFIG.md           # このファイル
├── aide_report.txt              # AIDE最新結果
├── execution_time.txt           # AIDE実行時間履歴
├── visualize_aide.py            # AIDE可視化スクリプト
├── aide_execution_trend.png     # AIDEグラフ
├── script_usage.log             # 動作ログ
├── clamscan_report.txt          # ClamAV最新結果
└── clamscan_time.txt            # ClamAV実行時間履歴
```

---

## システムリソース使用状況

### メモリ使用量（概算）

| プロセス | 使用量 |
|---|---|
| clamav-daemon | 約1GB |
| clamav-freshclam | 約5MB |
| AIDE | 0（実行時のみ） |
| **合計** | **約1GB** |

### CPU使用量

通常時: ほぼ0%（待機状態）  
スキャン実行時: 10〜30%（10〜30分間）

---

## パフォーマンス最適化オプション

### もしシステムが重い場合

#### オプション1: ClamAVデーモンを停止（推奨）

```bash
# デーモンを停止
sudo systemctl stop clamav-daemon
sudo systemctl disable clamav-daemon

# メリット: メモリ1GB削減
# デメリット: なし（週1回スキャンは継続）
```

#### オプション2: freshclam更新頻度を下げる

```bash
# /etc/clamav/freshclam.conf を編集
sudo nano /etc/clamav/freshclam.conf

# 以下の行を変更
Checks 24  # 1時間ごと → 毎日1回
```

---

## トラブルシューティング

### AIDEエラー: "Resource temporarily unavailable"

**原因**: 他のAIDEプロセスが実行中

**対処法**:
```bash
# プロセス確認
ps aux | grep aide

# 完了を待ってから再実行
sudo /usr/local/bin/aide-update-git.sh
```

### ClamAVスキャンが遅い

**原因**: 除外設定が不十分

**対処法**:
- 現在の設定は既に最適化済み（10〜30分）
- さらに高速化したい場合は除外ディレクトリを追加

### GitHubへのpushが失敗する

**原因**: 認証エラーまたはネットワークエラー

**対処法**:
```bash
# 手動でpush
cd /home/eliza/my-server-log
git push origin main

# 認証情報を再設定
git config --global user.name "your-username"
git config --global user.email "your-email"
```

---

## 設定の復元手順

システムを再インストールした場合や、別のマシンに同じ設定を適用する場合：

### 1. 基本パッケージのインストール

```bash
sudo apt update
sudo apt install ufw clamav clamav-daemon aide unattended-upgrades
```

### 2. ファイアウォール設定

```bash
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw limit 80/tcp
sudo ufw limit 443/tcp
```

### 3. 自動アップデート有効化

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 4. スクリプトの配置

このリポジトリから以下をコピー：
- `/usr/local/bin/clamav-scan.sh`
- `/usr/local/bin/clamscan-update-git.sh`
- `/usr/local/bin/aide-update-git.sh`

実行権限を付与：
```bash
sudo chmod +x /usr/local/bin/*.sh
```

### 5. cron設定

```bash
sudo crontab -e

# 以下を追加
0 1 * * 0 /usr/local/bin/clamav-scan.sh
0 2 * * 0 /usr/local/bin/clamscan-update-git.sh
```

### 6. APT連動設定

```bash
sudo nano /etc/apt/apt.conf.d/99aide-post-install

# 内容を貼り付け
DPkg::Post-Invoke {"/usr/local/bin/aide-update-git.sh &"};
```

---

## セキュリティレベル比較

| 機能 | Windows 10/11 | このシステム |
|---|---|---|
| ファイアウォール | ✅ | ✅ |
| 自動セキュリティ更新 | ✅ | ✅ |
| ウイルススキャン | ✅ 週1回 | ✅ 週1回 |
| ウイルス定義更新 | ✅ | ✅ 1時間ごと |
| ファイル改ざん検知 | ❌ | ✅ AIDE |
| リアルタイム保護 | ✅ | ⚠️ 待機中 |

**結論**: Windows以上のセキュリティレベルを実現しています。

---

## 参考リンク

- [ClamAV公式ドキュメント](https://docs.clamav.net/)
- [AIDE公式サイト](https://aide.github.io/)
- [Ubuntu UFW ガイド](https://help.ubuntu.com/community/UFW)
- [GitHubリポジトリ](https://github.com/wafukarubonara-stack/my-server-log)

---

## 変更履歴

### 2026/01/31
- 初版作成
- 全セキュリティ設定を文書化
- トラブルシューティングセクション追加
