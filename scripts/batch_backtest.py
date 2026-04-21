#!/usr/bin/env python3
"""
批量回测脚本 - 从策略汇总CSV读取策略，执行期货5m回测
定时cronjob触发，每次处理一个策略，不管成功失败都继续下一个
"""
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE = Path("/home/kali/Project/freqtrade")
CSV_FILE = BASE / "user_data/notebooks/策略汇总.csv"
CHECKPOINT_FILE = BASE / "backtest_checkpoint.json"
RESULT_DIR = BASE / "user_data/backtest_results"
CONFIG_FILE = BASE / "config_backtest.json"
LOG_DIR = BASE / "user_data/logs"

# 确保目录存在
RESULT_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 交易所配置 - testnet期货
EXCHANGE = "binance"
TIMEFRAME = "5m"
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"


def load_strategies():
    """从CSV加载所有策略"""
    strategies = []
    with open(CSV_FILE, 'r', encoding='gbk') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过表头
        for row in reader:
            if row and row[0]:
                strategies.append({
                    'name': row[0],
                    'path': row[1] if len(row) > 1 else ''
                })
    return strategies


def load_checkpoint():
    """加载断点"""
    if CHECKPOINT_FILE.exists():
        return json.loads(CHECKPOINT_FILE.read_text())
    return {'current_idx': 0, 'failed': [], 'completed': []}


def save_checkpoint(state):
    """保存断点"""
    CHECKPOINT_FILE.write_text(json.dumps(state, indent=2))


def run_backtest(strategy_name, strategy_path):
    """执行单个策略回测"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = RESULT_DIR / f"{strategy_name}_回测结果_{timestamp}.json"
    log_file = LOG_DIR / f"{strategy_name}_{timestamp}.log"
    
    # 构造freqtrade命令
    cmd = [
        "freqtrade", "backtesting",
        "--strategy", strategy_name,
        "--config", str(CONFIG_FILE),
        "--timeframe", TIMEFRAME,
        "--timerange", f"{START_DATE}-{END_DATE}",
        "--export", "json",
        "--export-filename", str(result_file)
    ]
    
    print(f"执行: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(BASE)
    )
    
    log_file.write_text(result.stdout + "\n" + result.stderr)
    
    if result.returncode == 0:
        print(f"✓ {strategy_name} 成功")
        return True, result_file
    else:
        error_msg = result.stderr[:500] if result.stderr else result.stdout[:500]
        print(f"✗ {strategy_name} 失败: {error_msg[:100]}")
        return False, log_file


def main():
    strategies = load_strategies()
    if not strategies:
        print("未找到策略!")
        return
    
    print(f"加载了 {len(strategies)} 个策略")
    
    # 加载断点
    state = load_checkpoint()
    current_idx = state['current_idx']
    
    if current_idx >= len(strategies):
        print("所有策略已完成!")
        # 重置从头开始
        state = {'current_idx': 0, 'failed': [], 'completed': []}
        save_checkpoint(state)
        current_idx = 0
    
    # 处理当前策略
    strategy = strategies[current_idx]
    print(f"正在处理 [{current_idx+1}/{len(strategies)}] {strategy['name']}")
    
    success, output = run_backtest(strategy['name'], strategy['path'])
    
    if success:
        state['completed'].append(strategy['name'])
    else:
        state['failed'].append(strategy['name'])
    
    # 不管成功失败，都进入下一个
    state['current_idx'] = current_idx + 1
    save_checkpoint(state)
    
    print(f"完成. 已完成: {len(state['completed'])}, 失败: {len(state['failed'])}")


if __name__ == "__main__":
    main()
