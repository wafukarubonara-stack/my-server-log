##初回作成（2026/01/16作成）
##更新（2026/01/31）- ファイル名を改善
import matplotlib.pyplot as plt  # グラフ描画用
import re                         # 文字列解析用
import os                         # ファイル操作用
import datetime                   # 日時取得用

# --- 設定 ---
time_log = "aide_execution_time.txt"
output_image = "aide_execution_trend.png"
script_log = "aide_script_usage.log"  # スクリプトの動作記録

def parse_time_log(path):
    """ログから実行時間を抽出"""
    times = []
    if not os.path.exists(path):
        return times
    with open(path, 'r') as f:
        content = f.read()
        pattern = r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): ([\d:.]+)'
        found = re.findall(pattern, content)
        for t in found:
            parts = list(map(float, t.split(':')))
            sec = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
            times.append(sec)
    return times

# --- 実行 ---
execution_times = parse_time_log(time_log)

if execution_times:
    # グラフ作成
    plt.figure(figsize=(10, 6))
    plt.plot(execution_times, marker='o', color='#2ca02c', linewidth=2)
    plt.title('AIDE Execution Time Trend')
    plt.xlabel('Execution Count')
    plt.ylabel('Seconds')
    plt.grid(True, linestyle='--')
    plt.savefig(output_image)
    
    # 動作記録を追記（エンジニア流の管理）
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(script_log, "a") as f:
        f.write(f"[{now}] Success: Analyzed {len(execution_times)} records.\n")
    print(f"Success! Graph and log updated.")
