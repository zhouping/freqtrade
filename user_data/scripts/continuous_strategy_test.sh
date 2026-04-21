#!/bin/bash
# 持续测试策略脚本

cd /home/kali/Project/freqtrade

# 记录开始时间
echo "$(date '+%Y-%m-%d %H:%M:%S') - Strategy test loop started" >> user_data/logs/strategy_test.log

# 待测试策略列表
STRATEGIES=("MultiMa" "Heracles" "PatternRecognition" "mabStra" "GodStra_hyperopt" "hlhb" "HourBasedStrategy")

# 已测试的策略记录
TESTED_FILE="user_data/logs/tested_strategies.txt"
mkdir -p user_data/logs

while true; do
    for STRATEGY in "${STRATEGIES[@]}"; do
        # 检查是否已测试
        if grep -q "^${STRATEGY}$" "$TESTED_FILE" 2>/dev/null; then
            continue
        fi
        
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Testing $STRATEGY" >> user_data/logs/strategy_test.log
        
        # 运行回测
        RESULT=$(freqtrade backtesting --strategy "$STRATEGY" --config user_data/config_futures.json --timerange 20240701-20250901 --pairs BTC/USDT --timeframe 1h --stake-amount 3000000 2>&1)
        
        # 提取关键指标
        TRADES=$(echo "$RESULT" | grep -oP '\d+(?=\s+Trades)' | tail -1)
        PROFIT=$(echo "$RESULT" | grep -oP 'Tot Profit.*?\s+([\d.]+)\s+USDT' | grep -oP '[\d.]+' | head -1)
        WINRATE=$(echo "$RESULT" | grep -oP '\d+\s+Win\s+\d+\s+Loss\s+\d+\s+\d+\.\d+' | grep -oP '\d+\.\d+(?=%$)' | tail -1)
        
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $STRATEGY: Trades=$TRADES, Profit=$PROFIT%, WinRate=$WINRATE%" >> user_data/logs/strategy_test.log
        
        # 标记已测试
        echo "$STRATEGY" >> "$TESTED_FILE"
        
        # 休息30秒
        sleep 30
    done
    
    # 一轮完成后休息5分钟
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Round completed, sleeping 5min" >> user_data/logs/strategy_test.log
    sleep 300
done
