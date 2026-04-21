#!/bin/bash
# 批量执行GodStra_hyperopt hyperopt优化
# 参数: $1=起始序号 $2=结束序号

START=${1:-1}
END=${2:-10}

BASE_DIR="/home/kali/Project/freqtrade"
WORK_DIR="$BASE_DIR/user_data/backtest_results"
CONFIG_SRC="$BASE_DIR/user_data/config_godstra_okx_futures_backtest.json"

cd $BASE_DIR

echo "[$(date)] 开始执行 $START-$END 次优化"

for i in $(seq $START $END); do
    # 生成目录名
    TIMESTAMP=$(date +"%Y%m%d_%H%M")
    DIR_NAME="GodStra_hyperopt-OKX-BTC_USDT-5m-优化_${TIMESTAMP}_$i"
    FULL_DIR="$WORK_DIR/$DIR_NAME"
    
    echo "[$(date)] === 第 $i 次优化 ($DIR_NAME) ==="
    
    # 创建目录
    mkdir -p "$FULL_DIR"
    
    # 复制并修改配置
    cp "$CONFIG_SRC" "$FULL_DIR/config.json"
    sed -i 's/"strategy": "GodStra"/"strategy": "GodStra_hyperopt"/g' "$FULL_DIR/config.json"
    
    # 运行hyperopt
    freqtrade hyperopt \
        --hyperoptloss SharpeHyperOptLoss \
        --spaces buy sell roi stoploss trailing \
        --strategy GodStra_hyperopt \
        --config "$FULL_DIR/config.json" \
        --timerange 20250101-20250601 \
        -j 1 \
        -e 100 2>&1 | tee "$FULL_DIR/result.txt"
    
    # 提取best参数到strategy_parameters.json
    python3 << 'PYEOF'
import re, json, sys, os

result_file = sys.argv[1] if len(sys.argv) > 1 else None
if not result_file:
    exit()

with open(result_file, 'r') as f:
    content = f.read()

params = {}

# buy_params
buy_match = re.search(r'buy_params = \{([^}]+)\}', content, re.MULTILINE)
if buy_match:
    params['buy_params'] = {}
    for line in buy_match.group(1).split('\n'):
        m = re.match(r'\s*"([^"]+)":\s*"?([^",}]+)"?,?', line.strip())
        if m:
            key, val = m.groups()
            try:
                params['buy_params'][key] = eval(val)
            except:
                params['buy_params'][key] = val

# sell_params
sell_match = re.search(r'sell_params = \{([^}]+)\}', content, re.MULTILINE)
if sell_match:
    params['sell_params'] = {}
    for line in sell_match.group(1).split('\n'):
        m = re.match(r'\s*"([^"]+)":\s*"?([^",}]+)"?,?', line.strip())
        if m:
            key, val = m.groups()
            try:
                params['sell_params'][key] = eval(val)
            except:
                params['sell_params'][key] = val

# roi
roi_match = re.search(r'minimal_roi = \{([^}]+)\}', content, re.MULTILINE)
if roi_match:
    params['minimal_roi'] = {}
    for line in roi_match.group(1).split('\n'):
        m = re.match(r'\s*"([^"]+)":\s*([^,}]+)', line.strip())
        if m:
            key, val = m.groups()
            try:
                params['minimal_roi'][key] = float(val)
            except:
                pass

# stoploss
sl_match = re.search(r'stoploss = ([-\d.]+)', content)
if sl_match:
    params['stoploss'] = float(sl_match.group(1))

# trailing
ts_match = re.search(r'trailing_stop = (True|False)', content)
if ts_match:
    params['trailing_stop'] = ts_match.group(1) == 'True'

ts_pos = re.search(r'trailing_stop_positive = ([-\d.]+)', content)
if ts_pos:
    params['trailing_stop_positive'] = float(ts_pos.group(1))

ts_off = re.search(r'trailing_stop_positive_offset = ([-\d.]+)', content)
if ts_off:
    params['trailing_stop_positive_offset'] = float(ts_off.group(1))

ts_only = re.search(r'trailing_only_offset_is_reached = (True|False)', content)
if ts_only:
    params['trailing_only_offset_is_reached'] = ts_only.group(1) == 'True'

params['max_open_trades'] = 3

# Extract results summary
trades_match = re.search(r'Trades\s+\|\s+(\d+)', content)
if trades_match:
    params['trades'] = int(trades_match.group(1))

win_match = re.search(r'(\d+)\s+\d+\s+\d+', content)
if win_match:
    params['wins'] = int(win_match.group(1))

if params:
    out_file = os.path.join(os.path.dirname(result_file), "strategy_parameters.json")
    with open(out_file, 'w') as f:
        json.dump(params, f, indent=2)
    print(f"Saved: {out_file}")
PYEOF
    "$FULL_DIR/result.txt"
    
    echo "[$(date)] === 第 $i 次优化完成 ==="
done

echo "[$(date)] 全部完成 ($START-$END)"