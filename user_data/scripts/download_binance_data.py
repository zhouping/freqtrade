#!/usr/bin/env python3
"""
Binance 历史数据下载脚本 - Testnet 回测专用
从 data.binance.vision 下载现货/期货历史K线，转换为 Feather 格式

用法:
    python download_binance_data_for_testnet.py --mode spot      # 下载现货数据
    python download_binance_data_for_testnet.py --mode futures   # 下载期货数据
    python download_binance_data_for_testnet.py --mode both     # 下载两种数据
"""

import os
import argparse
import subprocess
import pandas as pd
from pathlib import Path
from datetime import datetime


def get_url(interval: str, year: int, month: int, mode: str) -> str:
    """生成 Binance Vision URL"""
    if mode == "spot":
        # 现货: data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip
        return (
            f"https://data.binance.vision/"
            f"data/spot/monthly/klines/BTCUSDT/{interval}/"
            f"BTCUSDT-{interval}-{year}-{month:02d}.zip"
        )
    else:
        # 期货 (USDT-M): data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip
        return (
            f"https://data.binance.vision/"
            f"data/futures/um/monthly/klines/BTCUSDT/{interval}/"
            f"BTCUSDT-{interval}-{year}-{month:02d}.zip"
        )


def download_month(interval: str, year: int, month: int, mode: str, temp_dir: Path) -> bool:
    """下载并解压单月数据"""
    zip_file = temp_dir / f"BTCUSDT-{interval}-{year}-{month:02d}.zip"
    csv_file = temp_dir / f"BTCUSDT-{interval}-{year}-{month:02d}.csv"
    url = get_url(interval, year, month, mode)
    
    # 如果 CSV 已存在，跳过
    if csv_file.exists():
        print(f"  已存在: {csv_file.name}")
        return True
    
    # 下载 ZIP
    if not zip_file.exists():
        print(f"  下载: {zip_file.name}")
        try:
            result = subprocess.run(
                f'curl -L -o "{zip_file}" "{url}" --max-time 120',
                shell=True,
                capture_output=True,
                timeout=180
            )
            if result.returncode != 0:
                print(f"  ❌ 下载失败: {url}")
                return False
        except Exception as e:
            print(f"  ❌ 下载失败: {e}")
            return False
    
    # 解压 ZIP
    try:
        subprocess.run(
            f'unzip -o -j "{zip_file}" -d "{temp_dir}"',
            shell=True,
            capture_output=True,
            timeout=30
        )
        # 删除 ZIP 文件节省空间
        os.remove(zip_file)
        return True
    except Exception as e:
        print(f"  ❌ 解压失败: {e}")
        return False


def extract_and_merge(interval: str, year: int, mode: str, temp_dir: Path) -> Path:
    """解压并合并 CSV 文件"""
    merged_csv = temp_dir / f"BTCUSDT_{interval}_{year}.csv"
    
    if merged_csv.exists():
        os.remove(merged_csv)
    
    # 收集该年份该间隔的所有 CSV
    csv_files = sorted(temp_dir.glob(f"BTCUSDT-{interval}-{year}-*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"没有找到 {interval} {year} 年的 CSV 文件")
    
    # 写入表头
    with open(merged_csv, 'w') as outfile:
        with open(csv_files[0], 'r') as infile:
            outfile.write(infile.readline())  # 写入表头
    
    # 追加数据行
    for csv_file in csv_files:
        with open(merged_csv, 'a') as outfile:
            with open(csv_file, 'r') as infile:
                next(infile)  # 跳过表头
                outfile.write(infile.read())
        
        # 删除已处理的月度 CSV
        os.remove(csv_file)
    
    # 删除 ZIP 文件
    for zip_file in temp_dir.glob(f"BTCUSDT-{interval}-{year}-*.zip"):
        os.remove(zip_file)
    
    return merged_csv


def convert_to_feather(csv_file: Path, output_file: Path, mode: str) -> None:
    """转换 CSV 为 Feather 格式"""
    print(f"  转换: {csv_file.name} -> {output_file.name}")
    
    # CSV 列名 (Binance Vision 标准格式)
    columns = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'count', 
        'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
    ]
    
    # 读取 CSV
    df = pd.read_csv(csv_file, header=0, names=columns, skiprows=1, low_memory=False)
    
    # 转换时间戳 (自动检测: 毫秒或微秒格式)
    ts = df['open_time'].astype(float)
    if ts.iloc[0] >= 100000000000000:  # 15位以上为微秒格式，需要除以1000
        ts = ts / 1000
    df['date'] = pd.to_datetime(ts, unit='ms')
    
    # 只保留需要的列 (Freqtrade 标准格式)
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    
    # 按时间排序
    df = df.sort_values('date').reset_index(drop=True)
    
    # 保存为 Feather (LZ4 压缩)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_feather(output_file, compression="lz4", compression_level=9)
    
    print(f"  ✅ {output_file.name}: {len(df)} 行, {df['date'].min()} ~ {df['date'].max()}")


def download_for_mode(mode: str, years: list, intervals: list, base_output_dir: Path):
    """下载指定模式的数据"""
    mode_name = "现货 (spot)" if mode == "spot" else "期货 (futures)"
    print(f"\n{'='*60}")
    print(f"📥 开始下载 {mode_name} 数据")
    print(f"{'='*60}")
    
    output_dir = base_output_dir / mode
    temp_dir = output_dir / 'temp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    success_count = 0
    fail_count = 0
    
    for interval in intervals:
        print(f"\n【{interval}】")
        
        for year in years:
            # 下载每个月
            for month in range(1, 13):
                if not download_month(interval, year, month, mode, temp_dir):
                    print(f"  ⚠️ {year}-{month:02d} 下载失败，跳过")
                    fail_count += 1
                    continue
                success_count += 1
            
            # 合并并转换
            try:
                merged_csv = extract_and_merge(interval, year, mode, temp_dir)
                # 输出文件名: BTCUSDT_5m_2024.feather
                output_file = output_dir / f"BTCUSDT_{interval}_{year}.feather"
                convert_to_feather(merged_csv, output_file, mode)
                os.remove(merged_csv)
            except Exception as e:
                print(f"  ❌ 处理失败: {e}")
                fail_count += 1
            
            # 礼貌性延迟，避免过快请求
            import time
            time.sleep(0.5)
    
    print(f"\n{'='*60}")
    print(f"✅ {mode_name} 下载完成: 成功 {success_count} 月, 失败 {fail_count} 月")
    print(f"📁 数据保存位置: {output_dir}")
    print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='下载 Binance 历史数据 (Testnet 回测专用)')
    parser.add_argument(
        '--mode', 
        type=str, 
        choices=['spot', 'futures', 'both'], 
        default='both',
        help='下载模式: spot(现货), futures(期货), both(两者)'
    )
    parser.add_argument(
        '--years', 
        nargs='+', 
        type=int, 
        default=[2024, 2025],
        help='年份列表 (默认: 2024 2025)'
    )
    parser.add_argument(
        '--intervals', 
        nargs='+', 
        default=['1m', '5m', '30m', '1h'],
        help='时间间隔 (默认: 1m 5m 30m 1h)'
    )
    parser.add_argument(
        '--output-dir', 
        type=str, 
        default='/home/kali/Project/freqtrade/user_data/data/Testnet',
        help='输出目录'
    )
    
    args = parser.parse_args()
    
    base_output_dir = Path(args.output_dir)
    
    print("=" * 60)
    print("🚀 Binance 历史数据下载器 - Testnet 回测专用")
    print(f"   模式: {args.mode}")
    print(f"   年份: {args.years}")
    print(f"   间隔: {args.intervals}")
    print(f"   输出: {base_output_dir}")
    print("=" * 60)
    
    if args.mode in ['spot', 'both']:
        download_for_mode('spot', args.years, args.intervals, base_output_dir)
    
    if args.mode in ['futures', 'both']:
        download_for_mode('futures', args.years, args.intervals, base_output_dir)
    
    print("\n🎉 全部完成!")


if __name__ == '__main__':
    main()
