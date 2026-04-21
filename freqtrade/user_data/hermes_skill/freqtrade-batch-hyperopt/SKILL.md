---
# 严重警告！严禁使用 "现货模式+期货数据" 方式进行回测和hyperopt操作

###==========以上文字严禁删除！！！！！！！=================


name: freqtrade-batch-hyperopt
title: Freqtrade 批量策略优化
description: 批量运行 freqtrade hyperopt 优化多个策略并保存结果到 CSV，支持 HTX/Gate/Binance 各交易所
trigger: 批量 hyperopt / batch optimization / 多个策略优化
tags: [freqtrade, hyperopt, batch, optimization]
related_skills: [freqtrade-proxy-config, freqtrade-exchange-guides]
---

# Freqtrade 批量策略优化 (Batch Hyperopt)

## 概述
批量运行 freqtrade hyperopt 优化多个策略，并保存结果到指定目录。

## 关联 Skills
- **代理配置** → `freqtrade-proxy-config`
- **交易所配置** → `freqtrade-exchange-guides`
- **0交易排查** → `freqtrade-zero-trades-fix`

## 适用场景
- 需要对多个交易策略进行参数优化
- 需要将优化结果保存为可读的 CSV 格式
- 使用 HTX/Gate/Binance 交易所历史数据

## 前置条件
- freqtrade 已安装配置
- 历史数据已下载（`user_data/data/` 对应目录）
- 代理配置正确 → 见 `freqtrade-proxy-config`

## 关键参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--epochs` | 优化迭代次数 | 30 |
| `--spaces` | 优化空间 | roi stoploss |
| `--pairs` | 交易对 | BTC/USDT |
| `--timerange` | 数据时间范围 | 20260101- |

## 使用方法

```python
# 运行批量优化脚本
python3 batch_hyperopt.py
```

脚本会自动：
1. 遍历 strategies 列表中的所有策略
2. 对每个策略运行 hyperopt 优化
3. 从 stdout 解析结果（**结果在 stdout 不是 stderr**）
4. 保存每个策略结果到独立目录
5. 最后生成汇总 CSV 文件

## 输出目录结构

```
user_data/backtest_results/批量优化_YYYYMMDD_HHMMSS/
├── 优化结果汇总.csv          # 所有策略结果汇总
├── 优化详细结果.json         # 详细 JSON 结果
├── GodStra_优化_YYYYMMDD_HHMMSS/
├── Supertrend_优化_YYYYMMDD_HHMMSS/
└── ...
```

## CSV 字段说明

| 字段 | 说明 |
|------|------|
| 策略名 | 策略名称 |
| 退出代码 | 0=成功 |
| 交易次数 | 优化期间交易数 |
| 胜率(%) | 胜率 |
| 利润(USDT) | 绝对收益 |
| 利润(%) | 百分比收益 |
| 目标函数值 | Sharpe 等 loss 函数值 |
| 耗时(秒) | 优化耗时 |
| stoploss | 优化后的止损值 |
| minimal_roi | 优化后的 ROI 规则 |

## 重要发现

1. **输出位置**：freqtrade hyperopt 结果输出到 **stdout**，不是 stderr
2. **解析方法**：
   ```python
   combined = result.stdout + "\n" + result.stderr
   if "Best result:" in combined:
       section = combined.split("Best result:")[-1]
       # 然后用正则提取 trades, profit, objective 等
   ```
3. **性能**：每个策略约 2 分钟（30 epochs，32 核并行）
4. **超时**：建议设置 300 秒超时防止卡死

## 依赖
- Python 3.13+
- freqtrade 2026.3+
- subprocess, os, time, json, re (标准库)

## Hyperopt Loss 函数选择

| Loss 函数 | 目标 | 适用场景 |
|----------|------|---------|
| SharpeHyperOptLoss | 最大化夏普比率 | 追求风险调整收益 |
| OnlyProfitHyperOptLoss | 最大化绝对收益 | 追求利润最大化 |
| SortinoHyperOptLoss | 最大化 Sortino 比率 | 偏重下行风险 |

## 常见问题

### Hyperopt 需要连接交易所
Hyperopt 启动时会尝试从交易所加载市场信息（交易对、最小/最大价格等），即使有本地数据也需要网络。

**解决方案：**
1. 确保代理配置正确 → 见 `freqtrade-proxy-config`
2. 如果代理不可用，使用 **backtesting 离线运行**：
   ```bash
   freqtrade backtesting --strategy GodStra --config config.json --pairs BTC/USDT
   ```
