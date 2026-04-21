#!/bin/bash

# 执行100次 GodStra_hyperopt hyperopt优化
# 串行执行，避免资源冲突

BASE_DIR="/home/kali/Project/freqtrade"
WORK_DIR="$BASE_DIR/user_data/backtest_results"
CONFIG_SRC="$BASE_DIR/user_data/config_godstra_okx_futures_backtest.json"

cd "$BASE_DIR"

# 清理锁文件
rm -f "$BASE_DIR/user_data/hyperopt.lock" 2>/dev/null
rm -f "$BASE_DIR/user_data/hyperopt_results"/*.pkl 2>/dev/null

LOG_FILE="$WORK_DIR/hyperopt_100_run.log"
echo "=== 开始100次优化 ===" | tee -a "$LOG_FILE"
echo "开始时间: $(date)" | tee -a "$LOG_FILE"

TOTAL=100
COMPLETED=0

for i in $(seq 1 $TOTAL); do
    # 计算时间戳（每次递增2分钟）
    SEQ=$(( (i - 1) * 2 ))
    TIMESTAMP=$(date -d "+$SEQ minutes" +"%Y%m%d_%H%M")
    
    # 创建目录名
    DIR_NAME="GodStra_hyperopt-OKX-BTC_USDT-5m-优化_${TIMESTAMP}_$(printf "%02d" $i)"
    FULL_DIR="$WORK_DIR/$DIR_NAME"
    
    echo "" | tee -a "$LOG_FILE"
    echo "=== 第 $i/$TOTAL 次优化 ($DIR_NAME) ===" | tee -a "$LOG_FILE"
    echo "开始: $(date)" | tee -a "$LOG_FILE"
    
    # 创建目录
    mkdir -p "$FULL_DIR"
    
    # 创建配置文件
    sed 's/"strategy": "GodStra"/"strategy": "GodStra_hyperopt"/' "$CONFIG_SRC" > "$FULL_DIR/config.json"
    
    # 运行hyperopt
    freqtrade hyperopt \
        --hyperoptloss SharpeHyperOptLoss \
        --spaces buy sell roi stoploss trailing \
        --strategy GodStra_hyperopt \
        --config "$FULL_DIR/config.json" \
        --timerange 20250101-20250601 \
        -j 1 \
        -e 100 2>&1 | tee "$FULL_DIR/result.txt"
    
    # 保存最佳参数
    if [ -f "$BASE_DIR/strategy_parameters.json" ]; then
        cp "$BASE_DIR/strategy_parameters.json" "$FULL_DIR/strategy_parameters.json"
        echo "✓ 结果已保存" | tee -a "$LOG_FILE"
        COMPLETED=$((COMPLETED + 1))
    else
        echo "✗ 未找到参数文件" | tee -a "$LOG_FILE"
    fi
    
    echo "完成: $(date)" | tee -a "$LOG_FILE"
    echo "=== 第 $i/$TOTAL 次优化完成 ===" | tee -a "$LOG_FILE"
    
    # 清理锁文件
    rm -f "$BASE_DIR/user_data/hyperopt.lock" 2>/dev/null
    rm -f "$BASE_DIR/user_data/hyperopt_results"/*.pkl 2>/dev/null
    
    echo "已完成: $COMPLETED/$TOTAL" | tee -a "$LOG_FILE"
done

echo "" | tee -a "$LOG_FILE"
echo "=== 全部完成 ===" | tee -a "$LOG_FILE"
echo "完成时间: $(date)" | tee -a "$LOG_FILE"
echo "总计完成: $COMPLETED/$TOTAL" | tee -a "$LOG_FILE"