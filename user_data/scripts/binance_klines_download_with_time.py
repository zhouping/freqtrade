#!/usr/bin/env python3
"""
Binance 历史K线数据下载脚本（附加 human‑readable 时间列）

- 默认 interval 为 5m，如果未指定则使用 5m。
- 支持 --include-time 标志，会在输出 CSV 中额外生成 `time` 列，
  格式为 ``YYYY-MM-DD HH:MM:SS``（UTC），同时保留 freqtrade 必需的
  `timestamp`（UTC 毫秒）列。

用法示例：
    python binance_klines_download_with_time.py \
        --symbol BTCUSDT \
        --interval 5m \
        --start "2025-01-01 00:00:00" \
        --end "2025-01-31 23:59:59" \
        --output-dir /home/kali/Project/freqtrade/user_data/data/binance/5m \
        --futures \
        --include-time
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
import requests
import pandas as pd

# ---------- 常量 ----------
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

# ---------- 参数解析 ----------
def parse_args():
    p = argparse.ArgumentParser(description="下载 Binance K 线并保存为 freqtrade CSV（可选 time 列）")
    p.add_argument("--symbol", required=True, help="交易对，例如 BTCUSDT")
    p.add_argument("--interval", default="5m", help="K线周期，默认 5m")
    p.add_argument("--start", required=True, help="起始时间，UTC，格式 YYYY-MM-DD HH:MM:SS")
    p.add_argument("--end", help="结束时间，UTC，格式同上，默认当前时间")
    p.add_argument("--output-dir", required=True, help="CSV 保存目录")
    p.add_argument("--futures", action="store_true", help="使用合约（USDT 永续）接口")
    p.add_argument("--include-time", action="store_true", help="在 CSV 中额外写入 human‑readable time 列")
    return p.parse_args()

# ---------- 辅助函数 ----------
def dt_to_ms(dt_str: str) -> int:
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
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

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

# ---------- 主流程 ----------
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

    # 生成文件名（包含 interval 与时间范围）
    start_str = args.start.replace(' ', 'T').replace(':', '-')
    end_str = (args.end or datetime.utcfromtimestamp(end_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')).replace(' ', 'T').replace(':', '-')
    filename = f"{args.symbol}_{args.interval}_{start_str}_to_{end_str}.csv"
    out_path = os.path.join(args.output_dir, filename)

    all_rows = []
    cur_ms = start_ms
    batch = 0
    est_batches = max(1, (end_ms - start_ms) // (step_ms * 1000))
    print("开始下载 Binance K 线数据…")
    while cur_ms < end_ms:
        try:
            batch_rows = fetch_batch(url, args.symbol, args.interval, cur_ms, end_ms, limit=1000)
            if not batch_rows:
                break
            all_rows.extend(batch_rows)
            cur_ms = batch_rows[-1][0] + step_ms
            batch += 1
            pct = min(100, (batch / est_batches) * 100)
            latest = datetime.utcfromtimestamp(batch_rows[-1][0] / 1000).strftime('%Y-%m-%d %H:%M')
            print(f"[{pct:5.1f}%] 批次 {batch:4d} | 最新: {latest} | 累计: {len(all_rows):,} 条")
            time.sleep(0.07)
        except requests.HTTPError as e:
            print(f"HTTP 错误: {e}，5 秒后重试…", file=sys.stderr)
            time.sleep(5)
        except Exception as e:
            print(f"下载出错: {e}", file=sys.stderr)
            break

    df = rows_to_df(all_rows)
    if df.empty:
        print("未获取到数据", file=sys.stderr)
        sys.exit(1)

    # freqtrade 必要的 timestamp（毫秒）列
    df_freq = df.copy()
    df_freq["timestamp"] = (df_freq["timestamp"].astype('int64') // 10**6)

    if args.include_time:
        # 添加 human‑readable 列，保持 UTC
        df_freq["time"] = pd.to_datetime(df_freq["timestamp"], unit="ms", utc=True)
        df_freq["time"] = df_freq["time"].dt.strftime("%Y-%m-%d %H:%M:%S")
        cols = ["timestamp", "time", "open", "high", "low", "close", "volume"]
    else:
        cols = ["timestamp", "open", "high", "low", "close", "volume"]

    df_freq = df_freq[cols]
    df_freq.to_csv(out_path, index=False)
    print(f"已保存 {len(df_freq)} 条记录至 {out_path}")

if __name__ == "__main__":
    main()
