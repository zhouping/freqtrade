#!/usr/bin/env python3
"""
简单测试: 用freqtrade内置示例策略测试回测
"""
import subprocess
import sys

cmd = [
    sys.executable, "-m", "freqtrade", "backtesting",
    "-c", "user_data/config_binance_futures_testnet.json",
    "-s", "Strategy",  # 尝试内置策略
    "--timerange", "20240101-20240131"
]

result = subprocess.run(
    cmd,
    cwd="/home/kali/Project/freqtrade",
    capture_output=True,
    text=True,
    timeout=120
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)