#!/usr/bin/env python3
"""
Binance 历史K线数据下载脚本

功能：
- 支持现货和合约（USDT 永续）两种模式
- 通过命令行参数指定交易对、周期、时间范围、保存目录
- 自动分页下载，最大单次请求 1000 根K线
- 输出符合 freqtrade CSV 格式的文件：timestamp,open,high,low,close,volume
  （timestamp 为 UTC 毫秒时间戳）

用法示例：
    python binance_klines_download.py \
        --symbol BTCUSDT \
        --interval 5m \
        --start "2024-01-01 00:00:00" \
        --end "2024-01-07 23:59:59" \
        --output-dir /home/kali/Project/freqtrade/data \
        --futures
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone, timedelta
import requests
import pandas as pd

# ---------- 配置 ----------
BASE_SPOT = "https://api.binance.com/api/v3/klines"
BASE_FUTURES = "https://fapi.binance.com/fapi/v1/klines"

INTERVAL_MS = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
    "3d": 259_200_000,
    "1w": 604_800_000,
    "1M": 2_592_000_000,
}

# ---------- 工具函数 ----------
def parse_args():
    parser = argparse.ArgumentParser(description="下载 Binance K线并保存为 freqtrade CSV")
    parser.add_argument("--symbol", required=True, help="交易对，例如 BTCUSDT")
    parser.add_argument("--interval", required=True, help="K线周期，例如 5m, 1h, 1d")
    parser.add_argument("--start", required=True, help="起始时间，格式 YYYY-MM-DD HH:MM:SS（UTC）")
    parser.add_argument("--end", required=False, help="结束时间，格式同上，默认当前时间")
    parser.add_argument("--output-dir", required=True, help="保存 CSV 文件的目录")
    parser.add_argument("--futures", action="store_true", help="使用合约（USDT 永续）接口，默认使用现货接口")
    return parser.parse_args()

def dt_to_ms(dt_str):
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)

def fetch_batch(url, symbol, interval, start_ms, end_ms=None, limit=1000):
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_ms,
        "limit": limit,
    }
    if end_ms:
        params["endTime"] = end_ms
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def rows_to_df(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_base", "taker_buy_quote", "ignore",
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df[["timestamp", "open", "high", "low", "close", "volume"]]
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = df[col].astype(float)
    df = df.drop_duplicates("timestamp").sort_values("timestamp").reset_index(drop=True)
    return df

def main():
    args = parse_args()
    url = BASE_FUTURES if args.futures else BASE_SPOT
    start_ms = dt_to_ms(args.start)
    end_ms = dt_to_ms(args.end) if args.end else int(time.time() * 1000)

    step_ms = INTERVAL_MS.get(args.interval)
    if not step_ms:
        print(f"不支持的周期: {args.interval}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(args.output_dir, exist_ok=True)
    filename = f"{args.symbol}_{args.interval}_{args.start.replace(' ', 'T').replace(':', '-')}_to_{(args.end or datetime.utcfromtimestamp(end_ms/1000).strftime('%Y-%m-%d %H:%M:%S')).replace(' ', 'T').replace(':', '-')}.csv"
    out_path = os.path.join(args.output_dir, filename)

    all_rows = []
    cur_ms = start_ms
    batch = 0
    total_batches_est = max(1, (end_ms - start_ms) // (step_ms * 1000))
    print("开始下载 Binance K线数据")
    while cur_ms < end_ms:
        try:
            batch_rows = fetch_batch(url, args.symbol, args.interval, cur_ms, end_ms, limit=1000)
            if not batch_rows:
                break
            all_rows.extend(batch_rows)
            cur_ms = batch_rows[-1][0] + step_ms
            batch += 1
            pct = min(100, (batch / total_batches_est) * 100)
            latest = datetime.utcfromtimestamp(batch_rows[-1][0] / 1000).strftime("%Y-%m-%d %H:%M")
            print(f"[{pct:5.1f}%] 批次 {batch:4d} | 最新: {latest} | 累计: {len(all_rows):,} 根")
            time.sleep(0.08)
        except requests.HTTPError as e:
            print(f"HTTP 错误: {e}，等待 5 秒后重试...", file=sys.stderr)
            time.sleep(5)
        except Exception as e:
            print(f"下载出错: {e}", file=sys.stderr)
            break

    df = rows_to_df(all_rows)
    if df.empty:
        print("未下载到任何数据")
        sys.exit(1)

    # 转为 freqtrade 所需的 CSV（timestamp 为毫秒整数）
    df_freq = df.copy()
    df_freq["timestamp"] = (df_freq["timestamp"].astype('int64') // 10**6)
    df_freq = df_freq[["timestamp", "open", "high", "low", "close", "volume"]]
    df_freq.to_csv(out_path, index=False)
    print(f"已保存 {len(df_freq)} 条记录至 {out_path}")

if __name__ == "__main__":
    main()
