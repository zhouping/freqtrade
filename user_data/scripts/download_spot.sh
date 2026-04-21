#!/bin/bash
# 下载 Binance 现货历史K线数据
# 保存到 /home/kali/Project/freqtrade/user_data/data/binance/

DATA_DIR="/home/kali/Project/freqtrade/user_data/data/binance"
BASE_URL="https://data.binance.vision/?prefix=data/spot/monthly/klines/BTCUSDT"

TIMEFRAMES=("1m" "5m" "15m" "30m" "1h")
YEARS=("2024" "2025")

mkdir -p "$DATA_DIR"

for TF in "${TIMEFRAMES[@]}"; do
    for YEAR in "${YEARS[@]}"; do
        echo "下载 ${TF} ${YEAR}..."
        FILE="BTCUSDT-${TF}-${YEAR}.zip"
        URL="${BASE_URL}/${FILE}"
        
        # 下载
        curl -L -o "/tmp/${FILE}" "$URL" 2>/dev/null
        
        if [ -f "/tmp/${FILE}" ]; then
            # 解压到临时目录
            mkdir -p "/tmp/klines"
            unzip -o "/tmp/${FILE}" -d "/tmp/klines" 2>/dev/null
            
            # 移动文件，命名格式：BTC_USDT-{timeframe}.feather
            for f in /tmp/klines/*.csv; do
                if [ -f "$f" ]; then
                    BASENAME=$(basename "$f" .csv)
                    # 转换为 feather 格式
                    python3 << EOF
import pandas as pd
import pyarrow.feather as feather

df = pd.read_csv("$f")
# 重命名列
df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume', 'num_trades', 'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore']
df['date'] = pd.to_datetime(df['date'], unit='ms')
df = df.set_index('date')
feather.write_feather(df, "${DATA_DIR}/BTC_USDT-${TF}.feather")
EOF
                    rm -f "$f"
                fi
            done
            
            rm -rf /tmp/klines /tmp/${FILE}
            echo "完成: BTC_USDT-${TF}.feather"
        else
            echo "跳过: ${FILE} 不存在"
        fi
    done
done

echo "全部完成！"