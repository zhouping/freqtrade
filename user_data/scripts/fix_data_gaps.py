#!/usr/bin/env python3
"""
补全缺失的K线数据 - 修正版
- 检测数据缺失时间段
- 下载并插入缺失数据（不重复）
"""
import os
import glob
import requests
import pandas as pd
from datetime import datetime, timezone
import time

BASE_FUTURES = "https://fapi.binance.com/fapi/v1/klines"

def dt_to_ms(dt_str):
    """支持带时间或不带时间的格式"""
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    except:
        dt = datetime.strptime(dt_str, "%Y-%m-%d")
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

def fetch_klines(symbol, interval, start_ms, end_ms, limit=1000):
    url = BASE_FUTURES
    all_data = []
    retry = 0
    max_retries = 3
    
    while start_ms < end_ms and retry < max_retries:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "limit": limit,
        }
        if end_ms:
            params["endTime"] = end_ms
        
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 418:
                retry += 1
                print(f"  [限流] 重试 {retry}/{max_retries}...")
                time.sleep(3)
                continue
            if resp.status_code != 200:
                print(f"  [错误] HTTP {resp.status_code}")
                break
            data = resp.json()
            if not data or not isinstance(data, list):
                break
            all_data.extend(data)
            start_ms = data[-1][0] + 1
            print(f"  已获取 {len(all_data)} 条...")
            time.sleep(0.2)
            retry = 0  # 成功则重置重试计数
        except Exception as e:
            print(f"  [错误] {e}")
            break
    
    return all_data

def klines_to_df(data):
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df = df.iloc[:, [1, 2, 3, 4, 5]]
    df.columns = ['open', 'high', 'low', 'close', 'volume']
    df.insert(0, 'timestamp', [d[0] for d in data])
    df.insert(1, 'date', pd.to_datetime([d[0] for d in data], unit='ms').strftime('%Y-%m-%d %H:%M:%S'))
    return df

def check_and_fill_gaps(interval, expected_start, expected_end):
    """检查并补全数据缺口"""
    base_dir = "/home/kali/Project/freqtrade/user_data/data/binance"
    dir_path = os.path.join(base_dir, interval)
    os.makedirs(dir_path, exist_ok=True)
    
    # 获取现有文件
    files = sorted(glob.glob(os.path.join(dir_path, 'BTCUSDT_*.csv')))
    
    # 加载所有现有数据
    all_data = pd.DataFrame()
    for f in files:
        df = pd.read_csv(f)
        all_data = pd.concat([all_data, df], ignore_index=True)
    
    if len(all_data) > 0:
        all_data = all_data.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        existing_start = pd.to_datetime(all_data['date'].min())
        existing_end = pd.to_datetime(all_data['date'].max())
    else:
        existing_start = None
        existing_end = None
    
    print(f"\n=== {interval} ===")
    print(f"预期范围: {expected_start} ~ {expected_end}")
    if existing_start:
        print(f"现有范围: {existing_start} ~ {existing_end} ({len(all_data)}条)")
    else:
        print("现有范围: 无数据")
    
    # 确定需要下载的时间段
    exp_start = pd.to_datetime(expected_start)
    exp_end = pd.to_datetime(expected_end)
    
    # 分析缺失
    if existing_start is None:
        # 完全无数据，全部下载
        print(f"  需要下载完整数据...")
        start_ms = dt_to_ms(expected_start)
        end_ms = dt_to_ms(expected_end)
        data = fetch_klines("BTCUSDT", interval, start_ms, end_ms)
        if data:
            all_data = klines_to_df(data)
            print(f"  获取 {len(all_data)} 条")
        else:
            print("  无数据")
            return
    else:
        # 检查缺失的时间段
        gaps = []
        
        # 开头缺失
        if existing_start > exp_start:
            print(f"  开头缺失: {exp_start} ~ {existing_start}")
            gaps.append((expected_start, str(existing_start)[:10]))
        
        # 结尾缺失
        if existing_end < exp_end:
            print(f"  结尾缺失: {existing_end} ~ {exp_end}")
            gaps.append((str(existing_end)[:10], expected_end))
        
        if not gaps:
            print("  无缺失")
            return
        
        # 逐个下载缺失部分
        for i, (start_str, end_str) in enumerate(gaps):
            print(f"  下载缺失段 {i+1}: {start_str} ~ {end_str}")
            start_ms = dt_to_ms(start_str + " 00:00:00")
            end_ms = dt_to_ms(end_str + " 00:00:00")
            
            data = fetch_klines("BTCUSDT", interval, start_ms, end_ms)
            if not data:
                print(f"    无数据")
                continue
            
            new_df = klines_to_df(data)
            print(f"    获取 {len(new_df)} 条")
            
            # 合并并去重
            all_data = pd.concat([all_data, new_df], ignore_index=True)
            all_data = all_data.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
    
    # 保存为单个文件
    start_str = expected_start.replace("-", "")[:6]
    end_str = expected_end.replace("-", "")[:6]
    filename = f"BTCUSDT_{interval}_{start_str}01_T000000_to_{end_str}01_T235959.csv"
    output_path = os.path.join(dir_path, filename)
    all_data.to_csv(output_path, index=False)
    print(f"  保存到: {output_path}")
    print(f"  总计 {len(all_data)} 条")

# 修复任务
tasks = [
    ("1m", "2025-01-01", "2025-04-01"),
    ("5m", "2025-01-01", "2026-01-01"),
    ("15m", "2025-01-01", "2026-01-01"),
    ("30m", "2025-01-01", "2026-01-01"),
    ("1h", "2025-01-01", "2026-01-01"),
    ("4h", "2025-01-01", "2026-01-01"),
    ("12h", "2025-01-01", "2026-01-01"),
]

for interval, start, end in tasks:
    try:
        check_and_fill_gaps(interval, start, end)
    except Exception as e:
        print(f"\n{interval} 出错: {e}")
    time.sleep(2)

print("\n✅ 完成!")