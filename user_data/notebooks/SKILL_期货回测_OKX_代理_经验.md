---
name: freqtrade-okx-futures-backtesting
title: Freqtrade OKX期货数据回测
description: 使用OKX期货历史数据进行现货模式回测的配置和代理设置
---

# Freqtrade OKX期货数据回测

## 核心配置

### OKX期货不支持直接回测
- freqtrade明确不支持OKX的`futures`交易模式
- 错误信息: `Freqtrade does not support 'futures' on OKX`

### 解决方案: 现货模式 + 期货数据

**配置文件关键设置:**
```json
{
  "exchange": {
    "name": "okx",
    "pair_whitelist": ["BTC/USDT"]
  },
  "trading_mode": "spot",
  "dataformat_ohlcv": "feather"
}
```

## 数据准备

### 1. 数据位置
- 期货数据: `/home/kali/Project/freqtrade/user_data/data/okx/futures/*.feather`
- 使用时复制到spot目录并重命名:
```bash
cp /home/kali/Project/freqtrade/user_data/data/okx/futures/*.feather /home/kali/Project/freqtrade/user_data/data/okx/spot/
# 将 BTC-USDT-5m-2025-01.feather 重命名为 BTC-USDT_5m.feather
```

### 2. 数据格式
- OKX期货feather格式: `[timestamp, open, high, low, close, volume]`
- timestamp为毫秒时间戳

## 代理设置

### 代理配置
```json
"ccxt_config": {
  "enableRateLimit": true,
  "aiohttp_trust_env": true
}
```
- 不需要在ccxt_config中设置proxies
- 使用clash-verge的系统代理环境变量

### 切换代理连接OKX
```bash
# 查看当前节点
/home/kali/Project/clash-verge-rev/clash-ctl list

# 切换节点 (使用交互模式)
echo -e "switch GLOBAL 香港\nq\n" | /home/kali/Project/clash-verge-rev/clash-ctl i

# 或使用
/home/kali/Project/clash-verge-rev/clash-ctl switch "GLOBAL" "节点名"
```

### 验证连接
```bash
# 检查代理出口IP
curl -s --max-time 5 -x http://127.0.0.1:7897 https://api.ipify.org
```

## 回测命令

```bash
cd /home/kali/Project/freqtrade

freqtrade backtesting \
  -c /home/kali/Project/freqtrade/user_data/config_godstra_okx_futures_backtest.json \
  --data-dir /home/kali/Project/freqtrade/user_data/data/okx/spot \
  --timerange 20250101-20251231
```

## 已验证可用的代理节点 (2025-04-19)
- 节点名称: 🇺🇲 美国节点
- 实际出口IP: 178.128.16.74
- 代理模式: rule
- 端口: 7897

## 常见问题

### 1. "No data found"
- 确认数据文件在正确的目录
- 确认文件名格式正确 (BTC-USDT_5m.feather)
- 确认dataformat_ohlcv与实际数据格式匹配

### 2. 连接超时
- 更换代理节点
- 检查clash-verge是否正常运行
- 确认端口7897可用

## 回测结果保存

按规范保存到 `/home/kali/Project/freqtrade/user_data/backtest_results/`:
- 目录名: `策略名-交易所-交易品种-时间周期-日期-时间`
- 包含文件: result.csv (GBK编码), config.json, strategy_parameters.json, 策略源码.py
