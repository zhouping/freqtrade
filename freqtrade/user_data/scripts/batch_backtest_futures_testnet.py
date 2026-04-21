# ⚠️ 此脚本内容有误！仅供参考，待重新编写
# 错误：引用了不存在的 config_binance_futures_testnet.json
# 错误：数据目录应为 user_data/data/Testnet/ (现货) 或 user_data/data/Testnet/futures/ (期货)
# 正确用法见 freqtrade-exchange-guides skill

#!/usr/bin/env python3
"""
批量期货回测脚本 - 使用 Binance Testnet
从策略汇总.csv读取所有策略，执行期货5m回测
⚠️ 此脚本有误，内容仅供参考！
"""
import os
import sys
import csv
import subprocess
import json
from pathlib import Path
from datetime import datetime

# 配置（⚠️ 以下配置有误，待修正）
FREQTRADE_DIR = Path("/home/kali/Project/freqtrade")
USER_DATA = FREQTRADE_DIR / "user_data"
CONFIG_FILE = "config_testnet_spot.json"  # ⚠️ 现货配置，混用期货数据是错误的！
STRATEGY_CSV = USER_DATA / "notebooks/策略汇总.csv"
RESULTS_DIR = USER_DATA / "backtest_results"
# ⚠️ 现货数据应放在 datadir 根目录（不要放在 spot/ 子目录）
DATA_DIR = USER_DATA / "data" / "Testnet"

# 回测参数
TIMEFRAME = "5m"
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

def load_strategies():
    """从CSV加载策略列表"""
    strategies = []
    # 用GBK编码读取
    import codecs
    with codecs.open(STRATEGY_CSV, 'r', encoding='GBK') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        for row in reader:
            if len(row) >= 2:
                name = row[0].strip()
                path = row[1].strip()
                strategies.append((name, path))
    return strategies

def run_backtest(strategy_name, strategy_path):
    """执行单个策略回测"""
    # 创建结果子目录
    result_subdir = RESULTS_DIR / f"{strategy_name}_testnet_5m_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    result_subdir.mkdir(parents=True, exist_ok=True)
    
    # 命令
    cmd = [
        sys.executable, "-m", "freqtrade", "backtesting",
        "-c", f"user_data/{CONFIG_FILE}",
        "-s", strategy_name,
        "--export", "trades",
        "--export-filename", str(result_subdir / "trades.csv")
    ]
    
    # 环境变量
    env = os.environ.copy()
    env['FREQTRADE_USER_DATA'] = str(USER_DATA)
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=FREQTRADE_DIR,
            capture_output=True,
            text=True,
            timeout=600,
            env=env
        )
        
        output = result.stdout + result.stderr
        
        # 提取关键指标
        metrics = {
            'strategy': strategy_name,
            'pair': 'BTCUSDT',
            'timeframe': TIMEFRAME,
            'exit_code': result.returncode
        }
        
        # 解析输出
        for line in output.split('\n'):
            if 'Best:' in line and 'profit' in line.lower():
                # 提取收益
                pass
        
        # 保存完整输出
        (result_subdir / "output.log").write_text(output)
        
        return result_subdir, result.returncode, output
        
    except subprocess.TimeoutExpired:
        return result_subdir, -1, "Timeout"
    except Exception as e:
        return result_subdir, -2, str(e)

def main():
    """主函数"""
    # 创建结果目录
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 加载策略
    strategies = load_strategies()
    print(f"Loaded {len(strategies)} strategies")
    
    # 汇总结果
    summary = []
    success = 0
    failed = 0
    
    for i, (name, path) in enumerate(strategies):
        print(f"[{i+1}/{len(strategies)}] {name}")
        
        result_dir, code, output = run_backtest(name, path)
        
        if code == 0:
            success += 1
            status = "SUCCESS"
        else:
            failed += 1
            status = f"FAILED ({code})"
        
        summary.append({
            'strategy': name,
            'path': path,
            'status': status,
            'result_dir': str(result_dir)
        })
        
        # 进度
        print(f"  -> {status}")
        
        # 每10个保存一次
        if (i + 1) % 10 == 0:
            save_summary(summary, i + 1)
            print(f"Progress: {i+1}/{len(strategies)}")
    
    # 保存最终汇总
    save_summary(summary, len(strategies))
    
    print(f"\n=== DONE ===")
    print(f"Success: {success}, Failed: {failed}")

def save_summary(summary, total):
    """保存汇总CSV"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_path = RESULTS_DIR / f"回测汇总_testnet_5m_{timestamp}.csv"
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['strategy', 'path', 'status', 'result_dir'])
        writer.writeheader()
        writer.writerows(summary)
    
    print(f"Summary saved: {csv_path}")

if __name__ == "__main__":
    main()