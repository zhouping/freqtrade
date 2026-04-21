#!/bin/bash

# 执行10次 GodStra_hyperopt hyperopt优化
# 序号: 41-50

BASE_DIR="/home/kali/Project/freqtrade"
WORK_DIR="/home/kali/Project/freqtrade/user_data/backtest_results"
CONFIG_SRC="$BASE_DIR/user_data/config_godstra_okx_futures_backtest.json"

cd $BASE_DIR

# 清理旧的hyperopt锁文件
rm -f $BASE_DIR/user_data/hyperopt_results/*.pkl 2>/dev/null

echo "开始执行10次hyperopt优化..."
echo "时间: $(date)"

# 循环执行10次hyperopt
for i in $(seq 41 50); do
    # 生成时间戳 (每次递增5分钟以避免冲突)
    SEQ=$(( (i - 41) * 5 ))
    TIMESTAMP=$(date -d "+$SEQ minutes" +"%Y%m%d_%H%M")
    
    # 创建目录名
    DIR_NAME="GodStra_hyperopt-OKX-BTC_USDT-5m-优化_${TIMESTAMP}_$i"
    FULL_DIR="$WORK_DIR/$DIR_NAME"
    
    echo "=== 开始第 $i 次优化 ($DIR_NAME) ==="
    echo "时间: $(date)"
    
    # 创建目录和配置文件
    mkdir -p "$FULL_DIR"
    
    # 基于原始配置创建配置文件，修改strategy为GodStra_hyperopt
    sed 's/"strategy": "GodStra"/"strategy": "GodStra_hyperopt"/' "$CONFIG_SRC" > "$FULL_DIR/config.json"
    
    # 运行hyperopt（使用单线程-j 1来避免资源不足）
    freqtrade hyperopt \
        --hyperoptloss SharpeHyperOptLoss \
        --spaces buy sell roi stoploss trailing \
        --strategy GodStra_hyperopt \
        --config "$FULL_DIR/config.json" \
        --timerange 20250101-20250601 \
        -j 1 \
        -e 100 2>&1 | tee "$FULL_DIR/result.txt"
    
    # 保存结果
    if [ -f "$BASE_DIR/strategy_parameters.json" ]; then
        cp "$BASE_DIR/strategy_parameters.json" "$FULL_DIR/strategy_parameters.json"
    fi
    
    # 保存日志副本
    cp "$FULL_DIR/result.txt" "$FULL_DIR/log.txt"
    
    # 清理锁文件
    rm -f $BASE_DIR/user_data/hyperopt_results/*.pkl 2>/dev/null
    
    echo "=== 第 $i 次优化完成 ==="
    echo "时间: $(date)"
    echo ""
done

echo "所有10次优化完成!"
echo "完成时间: $(date)"