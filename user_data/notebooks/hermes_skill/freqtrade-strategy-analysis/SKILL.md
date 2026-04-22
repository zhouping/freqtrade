---
# 严重警告！严禁使用 "现货模式+期货数据" 方式进行回测和hyperopt操作

###==========以上文字严禁删除！！！！！！！=================


name: freqtrade-strategy-analysis
title: Freqtrade 策略分析
description: 分析 freqtrade 策略结构，提取交易条件、参数、时间框架，并与 0 交易问题排查联动
trigger: 策略分析 / strategy analysis / 交易条件 / populate_entry_trend
tags: [freqtrade, strategy, analysis, parameters, trading conditions]
related_skills: [freqtrade-zero-trades-fix, freqtrade-exchange-guides]
---

# Freqtrade 策略分析

## 关联 Skills
- **0 交易排查** → `freqtrade-zero-trades-fix`（策略条件过严时使用）
- **交易所回测** → `freqtrade-exchange-guides`（数据配置时使用）

## 快速参数提取

| 参数 | 位置 | 正则 |
|------|------|------|
| timeframe | 类定义 | `timeframe\s*=\s*['"](\w+)['"]` |
| stoploss | 类定义 | `stoploss\s*=\s*([-\d.]+)` |
| minimal_roi | 类定义 | `minimal_roi\s*=\s*\{([^}]+)\}` |
| trailing_stop | 类定义 | `trailing_stop\s*=\s*(True\|False)` |
| trailing_stop_positive | 类定义 | `trailing_stop_positive\s*=\s*([\d.]+)` |

## 策略代码结构

| 组件 | 方法 | 行范围 |
|------|------|--------|
| 买入信号 | `populate_entry_trend()` | ~80-150 行 |
| 卖出信号 | `populate_exit_trend()` | ~140-200 行 |
| 指标计算 | `populate_indicators()` | ~60-100 行 |

## 交易条件提取

Entry/exit 条件格式：`dataframe.loc[(conditions), 'enter_long'] = 1`

常见模式：
- RSI：`dataframe['rsi'] < 30`（超卖）
- MACD：`dataframe['macd'] > dataframe['macd_signal']`（金叉）
- EMA：cross_above/over 函数
- K线形态：`CDLHAMMER`, `CDLDOJI` 等

## 重要发现

### 策略代码中无 pair_whitelist

**所有分析的 50+ 个策略都未在源码中定义 pair_whitelist。**

交易对在 `config.json` 中配置：
```json
"pairlists": [{
  "method": "StaticPairList",
  "pair_whitelist": ["BTCUSDT"]
}]
```

这是 Freqtrade 标准架构——策略是交易对无关的。

## 分析流程

1. 列出 strategies 目录下的所有 .py 文件
2. 读取每个文件，通过正则提取参数
3. 解析 populate_entry_trend/populate_exit_trend 的条件
4. 验证 pair_whitelist——策略源码中应无此配置
5. 生成汇总报告

## 提取命令示例

```bash
# 提取 timeframe
grep "timeframe\s*=" strategy.py

# 提取 stoploss
grep "stoploss\s*=" strategy.py

# 提取 entry 条件
sed -n '/def populate_entry_trend/,/return dataframe/p' strategy.py
```

## 相关文件

- 策略目录：`/home/kali/Project/freqtrade/user_data/strategies/`
- 配置目录：`/home/kali/Project/freqtrade/user_data/`
- 笔记目录：`/home/kali/Project/freqtrade/user_data/notebooks/`