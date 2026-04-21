#!/bin/bash

# Hyperopt 优化脚本 - 执行200次
# 参数: --timerange 20250101-20250601 --spaces all -e 200

WORKDIR=/home/kali/Project/freqtrade
CONFIG_FILE=$WORKDIR/user_data/config_okx_hyperopt.json
STRATEGY=GodStra_hyperopt_fixinds
HYPEROPT_STRATEGY=GodStraHo
TIMERANGE=20250101-20250601
EPOCHS=200
SPACES="buy sell roi stoploss trailing"

cd $WORKDIR

# 生成时间戳
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建结果目录
RESULT_DIR=$WORKDIR/user_data/backtest_results/GodStra_hyperopt-OKX-BTC_USDT-5m-优化_${TIMESTAMP}
mkdir -p $RESULT_DIR

# 创建配置文件
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

echo "开始 Hyperopt 优化..."
echo "参数: timerange=$TIMERANGE, epochs=$EPOCHS, spaces=$SPACES"
echo "结果目录: $RESULT_DIR"

# 执行 hyperopt
freqtrade hyperopt \
  --hyperopt-loss SharpeHyperOptLoss \
  --spaces $SPACES \
  --strategy $STRATEGY \
  --strategy-path $WORKDIR/user_data/strategies \
  --config $CONFIG_FILE \
  --timerange $TIMERANGE \
  -e $EPOCHS 2>&1 | tee $RESULT_DIR/hyperopt_output.txt

# 提取最佳结果
echo ""
echo "===== 优化完成 =====" 
echo "查看最佳结果..."

# 提取最佳参数
BEST_PARAMS=$(grep -A 50 "Best result" $RESULT_DIR/hyperopt_output.txt | head -60)

# 保存结果
cat > $RESULT_DIR/result.txt << EOF
========================================
Hyperopt 优化结果
========================================
策略: $STRATEGY
交易所: OKX
交易对: BTC/USDT
时间周期: 5m
优化周期: $TIMERANGE
epochs: $EPOCHS
spaces: $SPACES
优化时间: $TIMESTAMP

$BEST_PARAMS
EOF

# 复制配置文件
cp $CONFIG_FILE $RESULT_DIR/config.json

# 复制策略源码
cp $WORKDIR/user_data/strategies/$STRATEGY.py $RESULT_DIR/ 2>/dev/null

echo ""
echo "结果已保存到: $RESULT_DIR"
ls -la $RESULT_DIR/

