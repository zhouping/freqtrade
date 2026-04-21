#!/bin/bash

# 连续执行200次 Hyperopt 优化脚本
# 带自动监控和重启功能

WORKDIR=/home/kali/Project/freqtrade
CONFIG_FILE=$WORKDIR/user_data/config_okx_hyperopt.json
STRATEGY=GodStra_hyperopt_fixinds
HYPEROPT_STRATEGY=GodStraHo
TIMERANGE=20250101-20250601
EPOCHS=200
SPACES="buy sell roi stoploss trailing"
# 注意：spaces all 包含 protection 空间会报错，使用明确的参数空间
TOTAL_RUNS=200
RUN_INTERVAL=0  # 每次完成后等待0秒立即开始下一次

LOG_FILE=$WORKDIR/user_data/logs/hyperopt_200_runs.log
MARKER_FILE=$WORKDIR/.hyperopt_200_running

cd $WORKDIR

# 确保日志目录存在
mkdir -p $WORKDIR/user_data/logs

# 创建配置文件
create_config() {
cat > $CONFIG_FILE << 'EOF'
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": 1000,
  "dry_run": true,
  "dry_run_wallet": {"USDT": 10000},
  "exchange": {
    "name": "okx",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "enableRateLimit": true,
      "aiohttp_trust_env": true
    },
    "pair_whitelist": ["BTC/USDT"]
  },
  "pairlists": [{"method": "StaticPairList"}],
  "timeframe": "5m",
  "trading_mode": "spot",
  "fee": 0.0005,
  "runmode": "backtest",
  "dataformat_ohlcv": "feather",
  "dataformat_trades": "jsongz",
  "entry_pricing": {"price_side": "same"},
  "exit_pricing": {"price_side": "same"}
}
EOF
}

# 初始化
create_config
echo "========================================" | tee -a $LOG_FILE
echo "开始连续执行 $TOTAL_RUNS 次优化" | tee -a $LOG_FILE
echo "开始时间: $(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

# 记录开始运行
echo "$(date +%s)" > $MARKER_FILE

RUN_COUNT=0
SUCCESS_COUNT=0

while [ $RUN_COUNT -lt $TOTAL_RUNS ]; do
    RUN_COUNT=$((RUN_COUNT + 1))
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    RESULT_DIR=$WORKDIR/user_data/backtest_results/GodStra_hyperopt-OKX-BTC_USDT-5m-优化_${TIMESTAMP}_${RUN_COUNT}
    mkdir -p $RESULT_DIR
    
    echo "" | tee -a $LOG_FILE
    echo "===== 第 $RUN_COUNT/$TOTAL_RUNS 次优化 =====" | tee -a $LOG_FILE
    echo "开始时间: $(date)" | tee -a $LOG_FILE
    
    # 执行 hyperopt
    freqtrade hyperopt \
      --hyperopt-loss SharpeHyperOptLoss \
      --spaces $SPACES \
      --strategy $STRATEGY \
      --strategy-path $WORKDIR/user_data/strategies \
      --config $CONFIG_FILE \
      --timerange $TIMERANGE \
      -e $EPOCHS 2>&1 | tee $RESULT_DIR/hyperopt_output.txt
    
    EXIT_CODE=${PIPESTATUS[0]}
    
    # 提取最佳结果
    BEST_RESULT=$(grep -A 5 "Best result:" $RESULT_DIR/hyperopt_output.txt | head -10)
    
    # 保存结果
    cat > $RESULT_DIR/result.txt << EOF
========================================
Hyperopt 优化结果 (第 $RUN_COUNT/$TOTAL_RUNS 次)
========================================
策略: $STRATEGY
交易所: OKX
交易对: BTC/USDT
时间周期: 5m
优化周期: $TIMERANGE
epochs: $EPOCHS
spaces: $SPACES
优化时间: $TIMESTAMP

$BEST_RESULT
EOF

    # 复制配置文件和策略
    cp $CONFIG_FILE $RESULT_DIR/config.json
    cp $WORKDIR/user_data/strategies/$STRATEGY.py $RESULT_DIR/ 2>/dev/null
    
    # 更新进度
    echo "完成时间: $(date)" | tee -a $LOG_FILE
    echo "结果: $BEST_RESULT" | tee -a $LOG_FILE
    
    if [ $EXIT_CODE -eq 0 ]; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
    
    # 更新运行标记（用于监控检测）
    echo "$(date +%s) $RUN_COUNT $SUCCESS_COUNT" > $MARKER_FILE
    
    # 打印进度
    echo "进度: $RUN_COUNT/$TOTAL_RUNS (成功: $SUCCESS_COUNT)" | tee -a $LOG_FILE
    
    # 等待后继续下一次
    if [ $RUN_COUNT -lt $TOTAL_RUNS ]; then
        sleep $RUN_INTERVAL
    fi
done

echo "" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE
echo "全部完成！" | tee -a $LOG_FILE
echo "总运行: $RUN_COUNT 次" | tee -a $LOG_FILE
echo "成功: $SUCCESS_COUNT 次" | tee -a $LOG_FILE
echo "结束时间: $(date)" | tee -a $LOG_FILE
echo "========================================" | tee -a $LOG_FILE

# 清理标记文件
rm -f $MARKER_FILE