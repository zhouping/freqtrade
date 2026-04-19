#!/usr/bin/env python3
"""
下载币安BTCUSDT永续合约历史数据 - 优化版
"""
import os
import requests
import pandas as pd
from datetime import datetime, timezone
import time

BASE_FUTURES = "https://fapi.binance.com/fapi/v1/klines"

def dt_to_ms(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

def fetch_klines(symbol, interval, start_ms, end_ms, limit=1000):
    url = BASE_FUTURES
    all_data = []
    batch = 0
    
    while start_ms < end_ms:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "limit": limit,
        }
        if end_ms:
            params["endTime"] = min(end_ms, start_ms + limit * 60000)  # 限制范围
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code != 200:
                print(f"  错误: HTTP {resp.status_code}")
                break
            data = resp.json()
            if not data or not isinstance(data, list):
                break
            all_data.extend(data)
            batch += 1
            # 更新startTime为最后一条K线的时间+1
            start_ms = data[-1][0] + 1
            if batch % 10 == 0:
                print(f"  已获取 {len(all_data)} 条K线...")
        except Exception as e:
            print(f"  错误: {e}")
            break
    
    return all_data

def save_to_csv(data, output_path):
    if not data:
        return False
    
    df = pd.DataFrame(data)
    # Binance API返回12列: Open time, Open, High, Low, Close, Volume, Close time, ...
    df = df.iloc[:, [1, 2, 3, 4, 5]]
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.insert(0, 'timestamp', [d[0] for d in data])
    df.insert(1, 'date', pd.to_datetime([d[0] for d in data], unit='ms').strftime('%Y-%m-%d %H:%M:%S'))
    df.to_csv(output_path, index=False)
    return True

# 按月下载，避免超时
tasks = [
    # 1分钟数据 - 按月下载
    ("1m", "2025-01-01", "2025-02-01"),
    ("1m", "2025-02-01", "2025-03-01"),
    ("1m", "2025-03-01", "2025-04-01"),
    # 1h数据 - 按季度
    ("1h", "2025-01-01", "2025-04-01"),
    ("1h", "2025-04-01", "2025-07-01"),
    ("1h", "2025-07-01", "2025-10-01"),
    ("1h", "2025-10-01", "2026-01-01"),
    # 4h数据 - 半年
    ("4h", "2025-01-01", "2025-07-01"),
    ("4h", "2025-07-01", "2026-01-01"),
    # 12h数据 - 全年一次
    ("12h", "2025-01-01", "2026-01-01"),
    # 15m数据 - 按季度
    ("15m", "2025-01-01", "2025-04-01"),
    ("15m", "2025-04-01", "2025-07-01"),
    ("15m", "2025-07-01", "2025-10-01"),
    ("15m", "2025-10-01", "2026-01-01"),
    # 1d数据 - 全年一次
    ("1d", "2025-01-01", "2026-01-01"),
]

symbol = "BTCUSDT"
base_dir = "/home/kali/Project/freqtrade/user_data/data/binance"

# 创建目录
for tf in ["1m", "1h", "4h", "12h", "15m", "1d"]:
    os.makedirs(os.path.join(base_dir, tf), exist_ok=True)

for interval, start, end in tasks:
    print(f"\n=== 下载 {interval}: {start} -> {end} ===")
    start_ms = dt_to_ms(f"{start} 00:00:00")
    end_ms = dt_to_ms(f"{end} 00:00:00")
    
    data = fetch_klines(symbol, interval, start_ms, end_ms)
    print(f"  共获取 {len(data)} 条K线")
    
    if data:
        filename = f"BTCUSDT_{interval}_{start.replace('-', '')}_T000000_to_{end.replace('-', '')}_T235959.csv"
        output_path = os.path.join(base_dir, interval, filename)
        if save_to_csv(data, output_path):
            print(f"  保存到: {output_path}")
    
    time.sleep(0.5)

print("\n✅ 全部完成!")