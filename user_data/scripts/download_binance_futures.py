#!/usr/bin/env python3
"""
Binance Futures 数据下载脚本

从 Binance Vision 下载 BTCUSDT 永续合约历史K线数据并转换为 Feather 格式

用法:
    python download_binance_futures.py                    # 下载2025年全年数据
    python download_binance_futures.py --year 2024        # 下载指定年份
    python download_binance_futures.py --intervals 1m 5m  # 下载指定间隔
"""

import os
import argparse
import subprocess
import pandas as pd
from pathlib import Path


def get_s3_url(interval: str, year: int, month: int) -> str:
    """生成 Binance Vision S3 URL"""
    return (
        f"https://s3-ap-northeast-1.amazonaws.com/data.binance.vision/"
        f"data/futures/um/monthly/klines/BTCUSDT/{interval}/"
        f"BTCUSDT-{interval}-{year}-{month:02d}.zip"
    )


def download_month(interval: str, year: int, month: int, temp_dir: Path) -> bool:
    """下载单月数据"""
    zip_file = temp_dir / f"BTCUSDT-{interval}-{year}-{month:02d}.zip"
    url = get_s3_url(interval, year, month)
    
    if zip_file.exists():
        print(f"  已存在: {zip_file.name}")
        return True
    
    print(f"  下载: {zip_file.name}")
    try:
        result = subprocess.run(
            f'curl -L -o "{zip_file}" "{url}" --max-time 120',
            shell=True,
            capture_output=True,
            timeout=180
        )
        return result.returncode == 0
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        return False


def extract_and_merge(interval: str, year: int, temp_dir: Path) -> Path:
    """解压并合并CSV文件"""
    merged_csv = temp_dir / f"BTCUSDT_{interval}_{year}.csv"
    
    if merged_csv.exists():
        os.remove(merged_csv)
    
    # 收集该年份该间隔的所有CSV
    csv_files = sorted(temp_dir.glob(f"BTCUSDT-{interval}-{year}-*.csv"))
    
    if not csv_files:
        raise FileNotFoundError(f"没有找到 {interval} {year} 年的CSV文件")
    
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
        
        # 删除已处理的月度CSV
        os.remove(csv_file)
    
    # 删除ZIP文件
    for zip_file in temp_dir.glob(f"BTCUSDT-{interval}-{year}-*.zip"):
        os.remove(zip_file)
    
    return merged_csv


def convert_to_feather(csv_file: Path, output_file: Path) -> None:
    """转换CSV为Feather格式"""
    print(f"  转换: {csv_file.name} -> {output_file.name}")
    
    # CSV列名
    columns = [
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'count', 
        'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'
    ]
    
    # 读取CSV
    df = pd.read_csv(csv_file, header=0, names=columns, skiprows=1, low_memory=False)
    
    # 转换时间戳
    df['date'] = pd.to_datetime(df['open_time'].astype(float), unit='ms')
    
    # 只保留需要的列
    df = df[['date', 'open', 'high', 'low', 'close', 'volume']]
    
    # 按时间排序
    df = df.sort_values('date').reset_index(drop=True)
    
    # 保存为Feather
    df.to_feather(output_file)
    
    print(f"  ✅ {output_file.name}: {len(df)} 行, {df['date'].min()} ~ {df['date'].max()}")


def main():
    parser = argparse.ArgumentParser(description='下载 Binance 期货历史数据')
    parser.add_argument('--year', type=int, default=2025, help='年份 (默认: 2025)')
    parser.add_argument('--intervals', nargs='+', default=['1m', '5m', '30m', '1h'],
                        help='时间间隔 (默认: 1m 5m 30m 1h)')
    parser.add_argument('--output-dir', type=str, 
                        default='/home/kali/Project/freqtrade/user_data/data/binance_futures',
                        help='输出目录')
    
    args = parser.parse_args()
    
    # 创建目录
    output_dir = Path(args.output_dir)
    temp_dir = output_dir / 'temp'
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"=== 下载 {args.year} 年 Binance 期货数据 ===")
    print(f"输出目录: {output_dir}")
    print(f"时间间隔: {args.intervals}")
    print()
    
    for interval in args.intervals:
        print(f"【{interval}】")
        
        # 下载每个月
        for month in range(1, 13):
            if not download_month(interval, args.year, month, temp_dir):
                print(f"  ⚠️ {year}-{month:02d} 下载失败，跳过")
        
        # 合并并转换
        try:
            merged_csv = extract_and_merge(interval, args.year, temp_dir)
            output_file = output_dir / f"BTCUSDT_USDT_{interval}.feather"
            convert_to_feather(merged_csv, output_file)
            os.remove(merged_csv)
        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
        
        print()
    
    print("🎉 完成!")


if __name__ == '__main__':
    main()