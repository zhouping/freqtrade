---
name: freqtrade-futures-backtest
title: Freqtrade 期货回测指南
description: Binance 期货永续合约回测配置、数据格式、常见问题解决
trigger: freqtrade 期货 / futures / 永续 / BTC/USDT:USDT / 合约回测
tags: [freqtrade, futures, futures-backtest, perpetuals, binance]
---

# Freqtrade 期货回测指南

## 核心原则

| 原则 | 说明 |
|------|------|
| **期货模式 + 期货数据** | 正确 ✓ |
| **现货模式 + 现货数据** | 正确 ✓ |
| **期货模式 + 现货数据** | 错误 ✗ 严禁使用！ |
| **现货模式 + 期货数据** | 错误 ✗ 严禁使用！ |

**关键：** 期货回测必须使用 Binance 主网（不需要 Testnet），代理必须能连接 `fapi.binance.com`。

## ⚠️ 不需要 Testnet！

Binance Testnet 期货 API 已废弃（ccxt 源码确认）。直接使用 Binance 主网：

| 项目 | 端点 |
|------|------|
| 现货 API | `https://api.binance.com` |
| 期货 API | `https://fapi.binance.com` |
| 代理端口 | `7897` (Clash Verge mixed port) |

## 配置差异

|| 配置项 | 现货 (Spot) | 期货 (Futures) |
||--------|-------------|----------------|
| `trading_mode` | `"spot"` | `"futures"` |
| `margin_mode` | ❌ 无 | `"isolated"` |
| `pair_whitelist` | `["BTC/USDT"]` | `["BTC/USDT:USDT"]` |
| 数据目录 | `user_data/data/binance/` | `user_data/data/binance/futures/` |
| 数据文件名 | `BTC_USDT-5m.feather` | `BTC_USDT_USDT-5m-futures.feather` |
| 交易对格式 | `BTC/USDT` | `BTC/USDT:USDT` |

## 代理配置（2026-04-23 更新）

### 环境变量

```bash
# ⚠️ 必须使用 socks5h:// 格式
export https_proxy=socks5h://127.0.0.1:7897
export http_proxy=socks5h://127.0.0.1:7897
export all_proxy=socks5h://127.0.0.1:7897
```

### ccxt_config 配置

```json
"ccxt_config": {
  "enableRateLimit": true,
  "aiohttp_trust_env": true,
  "requests_trust_env": true  // ⚠️ 必须添加！
}
```

**关键发现：**
- ccxt 同步模式使用 `requests` 库，需要 `requests_trust_env: true`
- ccxt 异步模式使用 `aiohttp` 库，需要 `aiohttp_trust_env: true`
- freqtrade 回测两者都用到，必须同时设置

## 配置文件

### config_binance_futures.json

```json
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": 1000,
  "dry_run": true,
  "dry_run_wallet": 10000,
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "unfilledtimeout": {
    "entry": 10,
    "exit": 10,
    "unit": "minutes"
  },
  "entry_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_depth": "0.01%"
  },
  "exit_pricing": {
    "price_side": "same",
    "use_order_book": true,
    "order_book_depth": "0.01%"
  },
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "enableRateLimit": true,
      "aiohttp_trust_env": true
    },
    "pair_whitelist": ["BTC/USDT:USDT"],
    "trading_mode": "futures",
    "futures_trading_mode": "perpetual"
  },
  "pairlists": [{"method": "StaticPairList"}],
  "timeframe": "5m"
}
```

**关键配置点：**
1. `trading_mode: "futures"` — **顶层配置**，不是 exchange section
2. `margin_mode: "isolated"` — **顶层配置**
3. `pair_whitelist: ["BTC/USDT:USDT"]` — 三段式交易对格式

## 数据文件

### 目录结构

```
user_data/
└── data/
    └── binance/
        ├── BTC_USDT-5m.feather              # 现货数据
        └── futures/
            └── BTC_USDT_USDT-5m-futures.feather  # 期货数据
```

### 文件名规范（重要！）

| 数据类型 | 格式 | 示例 | 备注 |
|----------|------|------|------|
| 现货 | `{base}_{quote}-{timeframe}.feather` | `BTC_USDT-5m.feather` | 标准格式 |
| 期货 | `{base}_{quote}_{margin}-{timeframe}-futures.feather` | `BTC_USDT_USDT-5m-futures.feather` | ⚠️ 中间 `_USDT_` |
| 带年份 | `{base}_{quote}-{timeframe}-{year}.feather` | `BTC_USDT-5m-2024.feather` | ❌ 不支持 |

**⚠️ 关键发现：freqtrade 不支持年份文件名！**

- ❌ 不支持：`BTC_USDT-5m-2024.feather`, `BTC_USDT-5m-2025.feather`
- ✅ 必须：`BTC_USDT-5m.feather`（合并所有年份）

### 数据文件重命名（2026-04-23 实测）

下载的期货数据原始文件名：`BTCUSDT_USDT-5m-futures.feather`

freqtrade 内部格式：`BTC_USDT_USDT-5m-futures.feather`

需要重命名：
```bash
mv BTCUSDT_USDT-5m-futures.feather BTC_USDT_USDT-5m-futures.feather
```

**数据合并方法：**
```python
import pandas as pd
import pyarrow.feather as feather

# 合并多年数据
df24 = feather.read_feather('BTCUSDT_5m_2024.feather')
df25 = feather.read_feather('BTCUSDT_5m_2025.feather')
merged = pd.concat([df24, df25]).sort_values('date').reset_index(drop=True)

# 保存为标准格式（无年份）
feather.write_feather(merged, 'BTC_USDT_USDT-5m-futures.feather')
```
```

**注意：** `futures` 必须小写！

## 回测命令

```bash
cd /home/kali/Project/freqtrade

# 设置代理环境变量（必须使用 socks5h:// 格式）
export https_proxy=socks5h://127.0.0.1:7897
export http_proxy=socks5h://127.0.0.1:7897
export all_proxy=socks5h://127.0.0.1:7897

# 期货回测
freqtrade backtesting \
  --config user_data/config_binance_futures.json \
  --strategy GodStra \
  --strategy-path user_data/strategies \
  --data-format-ohlcv feather \
  --datadir user_data/data/binance \
  --pairs BTC/USDT:USDT \
  --timeframe 5m \
  --timerange 20251225-20260101 \
  --dry-run-wallet 10000
```

## 代理测试

### 快速测试 Binance 期货 API

```bash
curl --max-time 5 --proxy http://127.0.0.1:7897 https://fapi.binance.com/fapi/v1/exchangeInfo
```

成功输出示例：
## 代理测试

### 快速测试 Binance 期货 API

```bash
# 必须使用 socks5h:// 格式测试
curl --max-time 5 -x "socks5h://127.0.0.1:7897" https://fapi.binance.com/fapi/v1/exchangeInfo
```

### 测试代理连通性

```bash
# 测试 Binance 主网（使用 socks5h:// 格式）
curl --max-time 5 -x "socks5h://127.0.0.1:7897" https://api.binance.com/api/v3/exchangeInfo

# 测试 Binance 期货
curl --max-time 5 -x "socks5h://127.0.0.1:7897" https://fapi.binance.com/fapi/v1/exchangeInfo
```

## 常见问题

### Q1: "BTC/USDT:USDT is not tradable with Freqtrade"

**原因：** 
- 代理无法连接 Binance API
- `trading_mode` 配置位置错误（放在了 exchange section 内）

**解决：**
1. 检查代理连通性
2. 确认 `trading_mode` 在顶层配置

### Q2: "No history found"

**原因：** 数据文件不在正确目录

**解决：** 确认期货数据在 `user_data/data/futures/BTCUSDT_USDT-5m-futures.feather`

### Q3: 加载的现货交易对而非期货

**原因：** freqtrade 加载了 spot markets

**解决：** 检查配置中的 `trading_mode: "futures"` 是否在顶层

## 相关文档

| 文档 | 说明 |
|------|------|
| `freqtrade-proxy-config` | 代理配置与节点管理 |
| `freqtrade-exchange-guides` | 各交易所回测指南 |
| `freqtrade-mode-correction` | 现货/期货模式纠正 |

## 数据下载脚本

### download_futures_data.py

**位置：** `user_data/scripts/download_futures_data.py`

从 Binance Vision S3 下载期货K线数据：

```python
import requests
import zipfile
import io
import pandas as pd
import pyarrow.feather as feather
from pathlib import Path

BASE_URL = "https://data.binance.vision/data/futures/um/monthly/klines"
OUT_DIR = Path("user_data/data/binance/futures")
PAIR = "BTCUSDT"
TIMEFRAMES = ["1m", "5m", "30m", "1h"]
YEARS = [2024, 2025]

def download_month(tf, year, month):
    url = f"{BASE_URL}/{PAIR}/{tf}/{PAIR}-{tf}-{year}-{month:02d}.zip"
    resp = requests.get(url, timeout=60)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        for name in z.namelist():
            if name.endswith('.csv'):
                with z.open(name) as f:
                    df = pd.read_csv(f, skiprows=1, header=None)  # 跳过表头
                    df = df.iloc[:, :6]
                    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
                    return df

def process_tf(tf):
    all_dfs = []
    for year in YEARS:
        for month in range(1, 13):
            df = download_month(tf, year, month)
            if df: all_dfs.append(df)
    
    merged = pd.concat(all_dfs).sort_values('date').reset_index(drop=True)
    out_file = OUT_DIR / f"{PAIR}_USDT-{tf}-futures.feather"
    feather.write_feather(merged, out_file)
```

### Binance Vision S3 URL 格式

| 数据类型 | URL |
|----------|-----|
| 现货 | `https://data.binance.vision/data/spot/monthly/klines/{PAIR}/{tf}/{PAIR}-{tf}-{year}-{month:02d}.zip` |
| 期货U本位 | `https://data.binance.vision/data/futures/um/monthly/klines/{PAIR}/{tf}/{PAIR}-{tf}-{year}-{month:02d}.zip` |

**⚠️ 注意：** CSV 文件第一行是表头，读取时需要 `skiprows=1`

## 当前数据文件结构

```
user_data/data/
└── binance/                          # 现货数据
    ├── BTC_USDT-1m.feather          (33MB, 105万行)
    ├── BTC_USDT-5m.feather          (6.8MB, 21万行)
    ├── BTC_USDT-30m.feather         (1.1MB, 3.5万行)
    ├── BTC_USDT-1h.feather          (598KB, 1.7万行)
    └── futures/                     # 期货数据
        ├── BTC_USDT_USDT-1m-futures.feather    (29MB)
        ├── BTC_USDT_USDT-5m-futures.feather    (6.1MB)
        ├── BTC_USDT_USDT-30m-futures.feather   (1MB)
        └── BTC_USDT_USDT-1h-futures.feather    (550KB)
```

## 代理连通性监控

**Cron 设置：**
```
# 每天 08:00 检测 Binance 代理连通性
0 8 * * * /binance_proxy.sh >> /home/kali/TMP/binance_proxy_$(date +\%Y\%m\%d).log 2>&1

# 或使用项目内脚本
0 8 * * * /home/kali/Project/clash-verge-rev/binance_proxy.sh >> /home/kali/TMP/binance_proxy_$(date +\%Y\%m\%d).log 2>&1
```

### binance_proxy.sh 功能说明

1. 测试现货 API `https://api.binance.com/api/v3/exchangeInfo`
2. 测试期货 API `https://fapi.binance.com/fapi/v1/exchangeInfo`
3. 如果失败，自动切换 Clash Verge 节点：
   - 先尝试 GLOBAL 组的其他节点
   - 再用 `♻️ 自动选择` 组
4. 验证切换后是否恢复连接

### 查看日志

```bash
# 实时查看
tail -f /home/kali/TMP/binance_proxy.log

# 查看历史
ls -la /home/kali/TMP/binance_proxy_*.log
```