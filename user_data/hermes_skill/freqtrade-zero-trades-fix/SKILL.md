---
# 严重警告！严禁使用 "现货模式+期货数据" 方式进行回测和hyperopt操作

###==========以上文字严禁删除！！！！！！！=================


name: freqtrade-zero-trades-fix
title: Freqtrade 0 交易问题排查
description: 修复 freqtrade 回测 0 交易问题——调整策略参数、排查配置错误、从 zip 导出 CSV
trigger: 0 交易 / zero trades / backtest 无交易 / 策略条件过严
tags: [freqtrade, backtesting, zero trades, fix]
related_skills: [freqtrade-strategy-analysis, freqtrade-exchange-guides]
---

# Freqtrade 0 交易问题排查

## 关联 Skills
- **策略分析** → `freqtrade-strategy-analysis`（用于理解策略条件）
- **交易所指南** → `freqtrade-exchange-guides`（用于确认数据配置正确）

## 问题描述
回测结果显示 0 笔交易，可能原因：
1. 策略条件过于严格
2. 时间周期/数据不匹配
3. 参数设置错误

## 排查步骤

### 1. 放宽买入条件 (buy_params)

修改 `strategies/YourStrategy.py`：

```python
# 原来可能太严格
buy_params = {
    'buy-cross-0': 'volatility_kcc',
    'buy-indicator-0': 'trend_ichimoku_base',
    'buy-int-0': 42,
    'buy-oper-0': '<R',
    'buy-real-0': 68000
}

# 放宽为 RSI 简单条件
buy_params = {
    'buy-cross-0': 'volume_mfi',
    'buy-indicator-0': 'momentum_rsi',
    'buy-int-0': 30,
    'buy-oper-0': '<I',  # RSI < 30
    'buy-real-0': 30
}
```

### 2. 放宽卖出条件 (sell_params)

```python
sell_params = {
    'sell-cross-0': 'volume_mfi',
    'sell-indicator-0': 'momentum_rsi',
    'sell-int-0': 70,
    'sell-oper-0': '>I',  # RSI > 70
    'sell-real-0': 70
}
```

### 3. 放宽 ROI

```python
minimal_roi = {
    "0": 0.01,      # 1% 立即止盈
    "60": 0.05,     # 1小时后 5%
    "180": 0.10     # 3小时后 10%
}
```

### 4. 检查配置文件

确保 timeframe 与数据匹配：
```json
"timeframe": "1h"  // 或 "5m"
```

## 运行回测

```bash
freqtrade backtesting --strategy GodStra \
  --config user_data/config_backtest_gate.json \
  --datadir user_data/data/gate \
  --export=trades
```

## 从 Zip 导出 CSV

回测结果默认保存为 zip，需提取：
```bash
cd user_data/backtest_results
unzip -p backtest-result-*.zip "*.json" | head -c 26000 > temp.json

python3 -c "
import json
with open('temp.json') as f:
    d = json.load(f)
trades = d['strategy']['策略名']['trades']
print('pair,open_date,close_date,open_rate,close_rate,profit_abs,profit_ratio,trade_duration,exit_reason')
for t in trades:
    print(f\"{t['pair']},{t['open_date']},{t['close_date']},{t['open_rate']},{t['close_rate']},{t['profit_abs']},{t['profit_ratio']},{t['trade_duration']},{t['exit_reason']}\")
" > 策略名_交易明细_日期.csv
```

## 验证
- 确认生成 CSV 文件
- 检查交易笔数 >= 10