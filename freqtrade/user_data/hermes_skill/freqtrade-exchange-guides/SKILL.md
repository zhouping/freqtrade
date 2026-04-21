---
# 严重警告！严禁使用 "现货模式+期货数据" 方式进行回测和hyperopt操作

###==========以上文字严禁删除！！！！！！！=================


name: freqtrade-exchange-guides
title: Freqtrade 交易所回测指南
description: 各交易所（Gate/Binance/OKX/HTX）的数据格式、回测/优化配置、数据下载与常见问题解决
trigger: freqtrade 回测 / 交易所配置 / 数据下载 / Gate / OKX / HTX / Binance
tags: [freqtrade, exchange, backtesting, hyperopt, gate, okx, htx, binance, futures]
---

# Freqtrade 交易所回测指南

## 概览

| 交易所 | 数据限制 | 是否需要 Key | 备注 |
|--------|---------|-----------|-----------|------|
| **Gate** | 10,000 根K线/次 | 否 | 只能获取近期数据 |
| **Binance 主网** | 无限制 | 否（公开数据） | 需要代理 |
| **Binance Testnet** | 无限制 | 否 | 免费，但数据质量差 |
| **OKX** | 无限制 | 否 | 需要代理 |
| **HTX** | 无限制 | 否 | 支持2025年数据 |
| **Binance Vision S3** | 无限制 | 否 | **最推荐**，直接从AWS下载 |

**核心原则：**
- **本地历史K线**：必须用主网下载的数据（配置 `aiohttp_trust_env: true` + 代理）
- **元数据（交易对信息）**：从对应交易所/测试网获取
- **禁止混用**：现货模式 + 期货数据是错误的！

## Binance

### 数据来源

#### 方式1：Binance Vision S3 下载（推荐）

**不需要代理！** 直接从 AWS S3 下载完整年度数据。

**数据源：** `https://data.binance.vision/`
**Spot 数据 URL：**
```
https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/{interval}/BTCUSDT-{interval}-{year}-{month:02d}.zip
```
**Futures 数据 URL：**
```
https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/{interval}/BTCUSDT-{interval}-{year}-{month:02d}.zip
```

**下载脚本（已确认可用）：**
```bash
python /home/kali/Project/freqtrade/user_data/scripts/download_binance_data_for_testnet_confirm.py --mode both --years 2024 2025 --intervals 1m 5m 30m 1h
# 生成: user_data/data/Testnet/spot/*.feather (现货) 和 user_data/data/Testnet/futures/*.feather (期货)
```

**已下载数据（2026-04-22 确认）：**

现货 (`user_data/data/Testnet/spot/`)：
| 间隔 | 文件名 | 行数 | 时间范围 |
|------|--------|--------|----------|
| 1m | `BTCUSDT_1m_2024.feather` | 527,027 | 2024-01 ~ 2024-12 |
| 1m | `BTCUSDT_1m_2025.feather` | 525,587 | 2025-01 ~ 2025-12 |
| 5m | `BTCUSDT_5m_2024.feather` | 105,395 | 2024-01 ~ 2024-12 |
| 5m | `BTCUSDT_5m_2025.feather` | 105,107 | 2025-01 ~ 2025-12 |
| 30m | `BTCUSDT_30m_2024.feather` | 17,555 | 2024-01 ~ 2024-12 |
| 30m | `BTCUSDT_30m_2025.feather` | 17,507 | 2025-01 ~ 2025-12 |
| 1h | `BTCUSDT_1h_2024.feather` | 8,771 | 2024-01 ~ 2024-12 |
| 1h | `BTCUSDT_1h_2025.feather` | 8,747 | 2025-01 ~ 2025-12 |

期货 (`user_data/data/Testnet/futures/`)：
| 间隔 | 文件名 | 时间范围 |
|------|--------|----------|
| 1m | `BTCUSDT_1m_2024.feather` | 2024-01 ~ 2024-12 |
| 1m | `BTCUSDT_1m_2025.feather` | 2025-01 ~ 2025-12 |
| 5m | `BTCUSDT_5m_2024.feather` | 2024-01 ~ 2024-12 |
| 5m | `BTCUSDT_5m_2025.feather` | 2025-01 ~ 2025-12 |
| 30m | `BTCUSDT_30m_2024.feather` | 2024-01 ~ 2024-12 |
| 30m | `BTCUSDT_30m_2025.feather` | 2025-01 ~ 2025-12 |
| 1h | `BTCUSDT_1h_2024.feather` | 2024-01 ~ 2024-12 |
| 1h | `BTCUSDT_1h_2025.feather` | 2025-01 ~ 2025-12 |

**数据位置：** `user_data/data/Testnet/spot/` 和 `user_data/data/Testnet/futures/`

#### ⚠️ Binance Vision 时间戳格式变化（关键陷阱）

**问题：** Binance Vision 数据的时间戳格式在 2025 年发生了变化：

| 年份 | 时间戳格式 | 示例 | 位数 |
|------|-----------|------|------|------|
| 2024 | **毫秒** | `1704067200000` | 13 位 |
| 2025+ | **微秒** | `1735689600000000` | 16 位 |

**错误表现：** 如果直接用 `pd.to_datetime(ts, unit='ms')` 处理微秒格式数据，会得到 `OutOfBoundsDatetime` 或 1970 年的错误日期。

**自动检测逻辑（脚本中已实现）：**
```python
ts = df['open_time'].astype(float)
if ts.iloc[0] >= 100000000000000:  # ≥15位 = 微秒格式，需要除以 1000
    ts = ts / 1000
df['date'] = pd.to_datetime(ts, unit='ms')
```
- 现货：`BTC_USDT-5m.feather` → `user_data/data/binance/`
- 期货历史：`BTCUSDT_USDT_5m.feather` → `user_data/data/binance_futures/`

#### 方式2：Binance Testnet（不需要代理）

**⚠️ 重要发现：** freqtrade 代码中**没有 testnet/sandbox 的原生支持**！
- 搜索 `freqtrade/exchange/` 目录，没有找到 testnet 相关代码
- `testnet: true` 配置是直接透传给 ccxt，由 ccxt 处理的
- freqtrade 只负责 merge 配置并传递给 ccxt 初始化

```json
{
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "enableRateLimit": true,
      "aiohttp_trust_env": true,
      "testnet": true
    },
    "pair_whitelist": ["BTC/USDT"],
    "trading_mode": "spot"
  }
}
```

```bash
freqtrade download-data -c config.json --pairs BTC/USDT --timerange 20260401-20260410 -t 5m
```

#### 方式3：CCXT 直连（需要代理）

```json
{
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "proxies": {
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"
      },
      "aiohttp_trust_env": true
    },
    "ccxt_async_config": {
      "aiohttp_trust_env": true
    },
    "trading_mode": "futures",
    "futures_trading_mode": "perpetual"
  }
}
```

**期货交易对格式：** `BTCUSDT`（无斜杠） — U本位永续

### 配置文件模板

**现货回测配置：**
```json
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": 1000,
  "dry_run": true,
  "dry_run_wallet": 10000,
  "unfilledtimeout": {"entry": 10, "exit": 10, "unit": "minutes"},
  "entry_pricing": {"price_side": "same", "use_order_book": true, "order_book_depth": "0.01%"},
  "exit_pricing": {"price_side": "same", "use_order_book": true, "order_book_depth": "0.01%"},
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "enableRateLimit": true,
      "aiohttp_trust_env": true,
      "testnet": true
    },
    "pair_whitelist": ["BTC/USDT"],
    "trading_mode": "spot"
  },
  "pairlists": [{"method": "StaticPairList"}]
}
```

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| No history found | 文件名/目录错误 | 确认数据在 `user_data/data/binance/` |
| fapi 超时 | 代理不可达 | 换日本节点 |
| "not tradable" | 交易对名称错误 | 确认 `BTCUSDT` 格式 |

## Gate

### 数据格式

| 字段 | Gate 原始 | Binance jsongz |
|------|----------|---------------|
| timestamp | `1773892200000` (毫秒int) | `"1756684800000"` (字符串) |
| time | 无 | `"2025-09-01 00:00:00"` |
| open | `71260.1` | `"108208.4"` |
| volume | `1238370.0` | `"475.249"` |

### 数据转换

```python
import pandas as pd
import ccxt

exchange = ccxt.gate({'proxies': {'http': 'http://127.0.0.1:7897'}})
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '5m', limit=1500)

df = pd.DataFrame(ohlcv, columns=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
df.to_feather('user_data/data/gate/BTC_USDT-5m.feather')
```

### 永续合约数据下载

```bash
freqtrade download-data --exchange gate -p BTC/USDT:USDT --timeframes 5m --datadir user_data/data/gate
# 保存到: user_data/data/gate/futures/BTC_USDT_USDT-5m-futures.json.gz
```

**重要限制：**
- 最多 10,000 根K线，不能获取2025年历史数据
- `--timerange 20250101-20250131` 会报错：`Candlestick too long ago. Maximum 10000 points`

### 配置文件模板

```json
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": 1000,
  "dry_run": true,
  "dry_run_wallet": {"USDT": 10000},
  "exchange": {
    "name": "gate",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "proxies": {
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"
      },
      "enableRateLimit": true
    },
    "pair_whitelist": ["BTC/USDT:USDT"]
  },
  "pairlists": [{"method": "StaticPairList"}],
  "timeframe": "5m",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "fee": 0.0005,
  "runmode": "backtest",
  "dataformat_ohlcv": "jsongz",
  "entry_pricing": {"price_side": "same"},
  "exit_pricing": {"price_side": "same"}
}
```

## OKX

### 核心问题

freqtrade 无法直接使用 OKX 期货模式（`trading_mode: futures`）进行回测，显示 `not tradable`，可能是交易对名称错误。

**解决方案：**
1. 使用 CCXT 直连获取数据，保存为 feather
2. 使用现货模式 + 对应现货数据

### 当前代理配置（2026-04）

| 项目 | 配置 |
|------|------|
| 代理软件 | Clash Verge |
| 代理模式 | rule |
| 节点 | 🇺🇲 美国节点 |
| 出口IP | 178.128.16.74 |
| HTTP端口 | 7897 |

### 数据获取

```python
import ccxt
import pandas as pd

exchange = ccxt.okx({
    'proxies': {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897'
    }
})
ohlcv = exchange.fetch_ohlcv('BTC/USDT:SUSDT', '5m', limit=1500)

df = pd.DataFrame(ohlcv, columns=['date','open','high','low','close','volume'])
df['date'] = pd.to_datetime(df['date'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')
df.to_feather('user_data/data/okx/BTC_USDT-5m.feather')
```

### 配置文件模板

```json
{
  "exchange": {
    "name": "okx",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "proxies": {
        "http": "http://127.0.0.1:7897",
        "https": "http://127.0.0.1:7897"
      },
      "aiohttp_trust_env": true,
      "timeout": 30000,
      "enableRateLimit": true
    },
    "ccxt_async_config": {
      "aiohttp_trust_env": true,
      "timeout": 30000,
      "enableRateLimit": true
    }
  }
}
```

## HTX

### 配置

```json
{
  "exchange": {
    "name": "htx",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "aiohttp_trust_env": true
    },
    "ccxt_async_config": {
      "aiohttp_trust_env": true
    }
  }
}
```

### 数据下载

```bash
freqtrade download-data --exchange htx --pairs BTC/USDT --timeframes 5m --datadir user_data/data/htx
# 生成: user_data/data/htx/BTC_USDT-5m.feather
```

**优势：** HTX 可以获取2025年全年数据（Gate 限制10,000条）

## Feather 格式官方规范

### 数据来源
Freqtrade 官方源代码 (`featherdatahandler.py`) 定义：

```python
# DEFAULT_DATAFRAME_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
# DEFAULT_TRADES_COLUMNS = ["timestamp", "id", "type", "side", "price", "amount", "cost"]
```

### OHLCV 数据
| 列名 | 类型 | 说明 |
|------|------|------|
| `date` | int | UTC 毫秒时间戳 |
| `open` | float | 开盘价 |
| `high` | float | 最高价 |
| `low` | float | 最低价 |
| `close` | float | 收盘价 |
| `volume` | float | 成交量 |

### 文件压缩
- 使用 LZ4 压缩 (`compression="lz4"`, `compression_level=9`)

### 源代码位置
`/home/kali/.local/share/pipx/venvs/freqtrade/lib/python3.13/site-packages/freqtrade/data/history/datahandlers/featherdatahandler.py`

## 历史教训：已删除的问题脚本 (2026-04-22)

以下脚本因**期货数据+现货配置混用**问题被删除（共 4 个）：

| 脚本 | 问题 |
|------|------|
| `batch_backtest_futures.py` | 名为期货回测，但用现货配置 + 期货数据 |
| `batch_backtest_cron.py` | 依赖上述脚本 |
| `download_all_data.py` | 下载期货数据到 `data/binance/`（目录名误导现货） |
| `auto_test_strategies.sh` | 引用不存在的 `config_futures.json` |

**核心教训：** 回测必须严格遵循 现货模式+现货数据、期货模式+期货数据 的对应关系！

## 数据文件名规范

freqtrade **只认识固定格式**的文件名，不能随意改名：

```
{交易对}-{时间周期}.feather           # 现货 feather
{交易对}-{时间周期}-futures.feather  # 期货 feather（带 -futures）
{交易对}-{时间周期}.json.gz          # 现货 json.gz
{交易对}-{时间周期}-futures.json.gz   # 期货 json.gz
```

| 数据源 | 文件名示例 | 目录 |
|--------|-----------|------|
| 现货 feather | `BTC_USDT-5m.feather` | `user_data/data/binance/` |
| 期货 feather（实时） | `BTC_USDT-5m-futures.feather` | `user_data/data/binance/` |
| 期货 feather（历史） | `BTCUSDT_USDT_5m.feather` | `user_data/data/binance_futures/` |
| 永续合约 | `BTC_USDT_USDT-5m-futures.json.gz` | `user_data/data/gate/futures/` |
| HTX feather | `BTC_USDT-5m.feather` | `user_data/data/htx/` |

## 回测命令

```bash
cd /home/kali/Project/freqtrade

# Binance
freqtrade backtesting \
  --strategy GodStra \
  --config user_data/config_binance_testnet.json \
  --timerange 20260401-20260410

# Gate
freqtrade backtesting \
  --strategy GodStra \
  --config user_data/config_gate.json \
  --datadir user_data/data/gate \
  --export trades

# OKX
freqtrade backtesting \
  --strategy GodStra \
  --config user_data/config_okx.json \
  --datadir user_data/data/okx \
  --export trades
```

## Hyperopt vs Backtesting

| 操作 | 是否需要网络 | 适用场景 |
|------|-----------|-----------|
| **hyperopt** | ✅ 必须连接交易所API | 参数优化 |
| **backtesting** | ❌ 可完全离线运行 | 已有本地数据时的回测 |
当代理不可用时，用 backtesting 作为替代方案。

## Freqtrade ccxt 架构

freqtrade 同时使用两个 ccxt 库：

| 库 | 类型 | 用途 | 导入方式 |
|---|------|------|----------|
| `ccxt` | 同步 | 交易操作（下单、平仓等） | `import ccxt` |
| `ccxt.pro` | 异步 | 加载市场数据 | `import ccxt.pro as ccxt_pro` |

### 两个 API 对象

```python
# freqtrade/exchange/exchange.py
self._api: ccxt.Exchange          # 同步 ccxt - 用于交易操作
self._api_async: ccxt_pro.Exchange  # 异步 ccxt.pro - 用于加载市场
```

### 初始化流程

```python
# 创建同步 ccxt
self._api = self._init_ccxt(exchange_conf, sync=True, ccxt_config)

# 创建异步 ccxt.pro
self._api_async = self._init_ccxt(exchange_conf, sync=False, ccxt_async_config)
```

### 配置优先级

```python
# 先合并 ccxt_config，再合并 ccxt_sync_config
ccxt_config = deep_merge_dicts(exchange_conf.get("ccxt_config", {}), ccxt_config)
ccxt_config = deep_merge_dicts(exchange_conf.get("ccxt_sync_config", {}), ccxt_config)

# 先合并 ccxt_config，再合并 ccxt_async_config
ccxt_async_config = deep_merge_dicts(exchange_conf.get("ccxt_config", {}), ccxt_async_config)
ccxt_async_config = deep_merge_dicts(exchange_conf.get("ccxt_async_config", {}), ccxt_async_config)
```

### 默认 ccxt_config

```python
@property
def _ccxt_config(self) -> dict:
    if self.trading_mode == TradingMode.MARGIN:
        return {"options": {"defaultType": "margin"}}
    elif self.trading_mode == TradingMode.FUTURES:
        return {"options": {"defaultType": self._ft_has["ccxt_futures_name"]}}
    else:
        return {}
```

**关键发现：** freqtrade 本身不处理 `testnet`、`proxies`、`aiohttp_trust_env` 等配置，这些配置是直接透传给 ccxt 的。| testnet | ✅ 必须连接交易所API | 参数优化 |
当代理不可用时，用 backtesting 作为替代方案。