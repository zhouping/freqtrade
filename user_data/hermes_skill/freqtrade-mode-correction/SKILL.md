---
name: freqtrade-mode-correction
title: "Freqtrade 交易模式与数据对应关系纠正"
description: "纠正关于现货模式/期货模式的错误理解，确保数据格式与交易模式正确对应"
tags:
  - freqtrade
  - 交易模式
  - 数据格式
  - 重要纠正
related_skills:
  - freqtrade-exchange-guides
  - freqtrade-zero-trades-fix
---

# Freqtrade 交易模式与数据对应关系纠正

## 严重警告
**严禁使用 '现货模式+期货数据' 方式进行回测和 hyperopt 操作！**

## 正确的对应关系

| 数据类型 | 合约名称格式 | trading_mode | 示例 |
|---------|-------------|-------------|------|
| 期货数据 (Futures) | `BTCUSDT` | `"futures"` | 永续合约数据 |
| 现货数据 (Spot) | `BTC/USDT` | `"spot"` | 现货交易对数据 |

## 常见错误

```bash
# ❌ 错误：现货模式 + 期货数据
trading_mode: "spot"
data: "BTCUSDT"  # 期货格式的symbol

# ✅ 正确：期货数据 → futures模式
trading_mode: "futures"
data: "BTCUSDT"

# ✅ 正确：现货数据 → spot模式
trading_mode: "spot"
data: "BTC/USDT"
```

## 关键点

1. **user_data 目录下的配置文件不是 Freqtrade 源代码**
   - user_data/config_binance_spot.json 等文件是用户自己创建的
   - 这些配置可能包含错误用法，需要验证

2. **Freqtrade 源代码不包含 testnet/sandbox 支持**
   - 源代码中没有 `testnet` 或 `sandbox` 相关代码
   - 所有 testnet 相关配置是直接传给 ccxt，由 ccxt 处理

3. **Testnet 相关文档需要验证**
   - Testnet相关.md 中的内容来自其他地方的经验
   - 需要通过实际测试验证信息的正确性

## 来源

本纠正来自 2026-04-22 与用户 Joey 的对话