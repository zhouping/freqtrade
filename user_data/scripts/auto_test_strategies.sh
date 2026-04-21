#!/bin/bash
cd /home/kali/Project/freqtrade

# 所有待测试策略（从freqtrade list-strategies获取）
STRATEGIES=(
    "MultiMa"
    "Heracles"
    "PatternRecognition"
    "mabStra"
    "GodStra_hyperopt"
    "hlhb"
    "HourBasedStrategy"
    "Strategy001"
    "Strategy002"
    "Strategy003"
    "Strategy004"
    "Strategy005"
    "GodStra"
    "GodStra_hyperopt_fixinds"
    "BreakEven"
    "CustomStoplossWithPSAR"
    "FixedRiskRewardLoss"
    "InformativeSample"
    "Strategy001_custom_exit"
)

LOG_FILE="user_data/logs/strategy_test_$(date +%Y%m%d_%H%M%S).log"
RESULTS_FILE="user_data/logs/test_results_$(date +%Y%m%d_%H%M%S).csv"

echo "Strategy,CAGR,Trades,WinRate,ProfitFactor,Drawdown" > "$RESULTS_FILE"

for STRATEGY in "${STRATEGIES[@]}"; do
    echo "[$(date '+%H:%M:%S')] Testing $STRATEGY..." | tee -a "$LOG_FILE"
    
    OUTPUT=$(freqtrade backtesting \
        --strategy "$STRATEGY" \
        --config user_data/config_futures.json \
        --timerange 20240701-20250901 \
        --pairs BTC/USDT \
        --timeframe 1h \
        --stake-amount 3000000 2>&1)
    
    # 提取关键指标
    TRADES=$(echo "$OUTPUT" | grep -oP '\d+(?= trades)' | head -1)
    WIN_RATE=$(echo "$OUTPUT" | grep -oP '\d+\.\d+(?=%)' | tail -1)
    PROFIT_FACTOR=$(echo "$OUTPUT" | grep -i "profit factor" | grep -oP '\d+\.\d+' | head -1)
    DRAWDOWN=$(echo "$OUTPUT" | grep -i "drawdown" | grep -oP '\d+\.\d+%' | head -1)
    TOT_PROFIT=$(echo "$OUTPUT" | grep "Tot Profit %" | grep -oP '\d+\.\d+' | head -1)
    
    echo "$STRATEGY,$TOT_PROFIT,$TRADES,$WIN_RATE,$PROFIT_FACTOR,$DRAWDOWN" >> "$RESULTS_FILE"
    echo "[$(date '+%H:%M:%S')] Done: $STRATEGY (Profit: ${TOT_PROFIT}%, Trades: $TRADES, WinRate: ${WIN_RATE}%)" | tee -a "$LOG_FILE"
    
    sleep 2
done

echo "All tests complete! Results saved to $RESULTS_FILE"
