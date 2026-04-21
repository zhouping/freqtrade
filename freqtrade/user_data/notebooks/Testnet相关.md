# Binance Testnet 相关说明

> 本文档整理自 freqtrade-exchange-guides 和 freqtrade-proxy-config skill 中的 Testnet 相关内容。
> **注意：** skill 中的原始内容保留，此文档仅为方便查阅。

---

## 什么是 Binance Testnet？

Binance Testnet（测试网）是 Binance 提供的独立测试环境，用于：

- **模拟交易**：无需真实资金即可测试策略
- **免费数据**：无需代理即可获取数据（测试网不需要翻墙）
- **API 测试**：验证交易逻辑和接口调用

### Testnet API 端点（已废弃，内容可能有误！）

| 类型 | 端点 |
|------|------|
| **现货 (Testnet Spot)** | `https://testnet.binancefuture.com/dapi/v1/exchangeInfo` |
| **期货 (Testnet Futures)** | `https://testnet.binancefuture.com/fapi/v1/exchangeInfo` |

**说明：**
- `dapi` = 现货（Delivery）API
- `fapi` = 期货（Futures）API

### 获取 Testnet 元数据

```python
import ccxt

# 现货 Testnet
exchange_spot = ccxt.binance({
    'options': {'defaultType': 'spot'}
})
exchange_spot.set_sandbox_mode(True)
markets_spot = exchange_spot.fetch_markets()

# 期货 Testnet
exchange_futures = ccxt.binance({
    'options': {'defaultMarket': 'futures'}
})
exchange_futures.set_sandbox_mode(True)
markets_futures = exchange_futures.fetch_markets()

print(f"现货交易对数量: {len(markets_spot)}")
print(f"期货交易对数量: {len(markets_futures)}")
```

**与主网对比：**

| 特性 | Binance 主网 | Binance Testnet |
|------|-------------|-----------------|
| 数据限制 | 无限制 | 无限制 |
| 需要代理 | ✅ 需要 | ❌ 不需要 |
| 数据质量 | 真实市场 | 模拟数据，可能失真 |
| 需要 Key | 否（公开数据） | 否 |
| 用途 | 实盘/回测 | 测试/开发 |

---

## 快速开始

### 1. 配置 Testnet

在 `config.json` 中添加以下交易所配置：

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

**关键参数：**
- `testnet: true` — 启用测试网模式
- `aiohttp_trust_env: true` — 信任环境变量代理（如果需要）
- 不需要配置 `proxies` — Testnet 不需要代理

### 2. 下载 Testnet 数据

```bash
freqtrade download-data -c config.json --pairs BTC/USDT --timerange 20260401-20260410 -t 5m
```

**注意：** ⚠️ **此文档内容未经验证，可能包含错误！** 请以 `freqtrade-exchange-guides` skill 为准。

### 3. 运行回测

```bash
freqtrade backtesting --strategy YourStrategy --config config.json --timerange 20260401-20260410
```

---

## Testnet 配置文件模板

### 现货模式

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

### 期货模式

```json
{
  "max_open_trades": 3,
  "stake_currency": "USDT",
  "stake_amount": 1000,
  "dry_run": true,
  "dry_run_wallet": 10000,
  "unfilledtimeout": {"entry": 10, "exit": 10, "unit": "minutes"},
  "entry_pricing": {"price_side": "same"},
  "exit_pricing": {"price_side": "same"},
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "enableRateLimit": true,
      "aiohttp_trust_env": true,
      "testnet": true
    },
    "ccxt_async_config": {
      "aiohttp_trust_env": true
    },
    "pair_whitelist": ["BTCUSDT"],
    "trading_mode": "futures",
    "futures_trading_mode": "perpetual"
  },
  "pairlists": [{"method": "StaticPairList"}],
  "timeframe": "5m"
}
```

**期货交易对格式：** `BTCUSDT`（无斜杠）— U本位永续

---

## 用 ccxt 直接连接 Testnet

### Python 示例

```python
import ccxt

# 创建 binance exchange 实例，使用 testnet
exchange = ccxt.binance({
    'enableRateLimit': True,
    'aiohttp_trust_env': True,  # 信任环境变量代理
    'options': {
        'defaultMarket': 'futures',
    },
})
exchange.set_sandbox_mode(True)  # 启用 testnet 模式

# 获取 markets 元数据
markets = exchange.fetch_markets()

# 获取 BTC/USDT 的交易对信息
btc_usdt = None
for m in markets:
    if m['symbol'] == 'BTC/USDT':
        btc_usdt = m
        break

if btc_usdt:
    print(f"交易对: {btc_usdt['symbol']}")
    print(f"价格精度: {btc_usdt['precision']['price']}")
    print(f"数量精度: {btc_usdt['precision']['amount']}")
    print(f"最小数量: {btc_usdt['limits']['amount']['min']}")
    print(f"最大数量: {btc_usdt['limits']['amount']['max']}")
    print(f"Taker费率: {btc_usdt['taker']}")
    print(f"Maker费率: {btc_usdt['maker']}")
```

---

## 测试脚本

### test_proxy_for_testnet.py

**位置：** `user_data/scripts/test_proxy_for_testnet.py`

**功能：** 测试不同代理节点连接 Testnet

**使用：**

```bash
python /home/kali/Project/freqtrade/user_data/scripts/test_proxy_for_testnet.py
```

**流程：**
1. 读取 GLOBAL 组的节点列表
2. 逐个切换节点测试
3. 使用 freqtrade 的 ccxt 库连接 TESTNET 获取元数据
4. 如果失败则尝试下一个节点

### batch_backtest_futures_testnet.py

**位置：** `user_data/scripts/batch_backtest_futures_testnet.py`

**功能：** 批量期货回测脚本，使用 Binance Testnet

**使用：**

```bash
python /home/kali/Project/freqtrade/user_data/scripts/batch_backtest_futures_testnet.py
```

**配置参数：**
```python
# 配置文件
CONFIG_FILE = "config_binance_futures_testnet.json"

# 时间框架
TIMEFRAME = "5m"

# 回测时间范围
START_DATE = "2024-01-01"
END_DATE = "2024-12-31"
```

---

## 常见问题

### Q1: Testnet 数据质量差

**原因：** Testnet 是模拟环境，市场数据可能与主网有差异

**解决：**
- 如果需要真实市场数据，使用 Binance Vision S3 下载（推荐）
- 或使用主网 + 代理配置

### Q2: 连接超时

**原因：** 网络问题或 Testnet 服务不稳定

**解决：**
- 检查网络连接
- 尝试使用主网（配置代理）
- 切换代理节点

### Q3: 交易对不可交易

**原因：** Testnet 上的交易对可能被暂停

**解决：**
- 尝试其他交易对（如 ETH/USDT）
- 检查 Testnet 状态

---

## 推荐的数据获取方式

| 优先级 | 方式 | 是否需要代理 | 数据质量 |
|--------|------|------------|----------|
| ⭐⭐⭐ | Binance Vision S3 | ❌ 不需要 | 真实数据 |
| ⭐⭐ | Testnet | ❌ 不需要 | 模拟数据 |
| ⭐ | 主网 + 代理 | ✅ 需要 | 真实数据 |

**Binance Vision S3 下载命令：**

> ⚠️ 以下脚本路径和用法未验证，请以 `freqtrade-exchange-guides` skill 为准！
> 下载后需要重命名文件为 `{pair_s}-{timeframe}.feather` 并复制到 datadir 根目录！

```bash
python /home/kali/Project/freqtrade/user_data/scripts/download_binance_data_for_testnet_confirm.py --mode both --years 2024 2025 --intervals 1m 5m 30m 1h
# ⚠️ 脚本输出的文件名需要手动调整！见 freqtrade-exchange-guides skill
```

---

## ⚠️ 已废弃的脚本

| 文件 | 说明 | 状态 |
|------|------|------|
| `user_data/scripts/download_binance_futures.py` | Binance 主网数据下载脚本 | **已删除** |
| `user_data/scripts/batch_backtest_futures_testnet.py` | 批量期货回测脚本 | **内容有误，待检查** |

> ⚠️ `batch_backtest_futures_testnet.py` 引用的 `config_binance_futures_testnet.json` 不存在！
> 数据目录 `user_data/data/binance/` 应改为 `user_data/data/Testnet/` 或 `user_data/data/Testnet/futures/`

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `freqtrade-exchange-guides` | 各交易所回测指南 |
| `freqtrade-proxy-config` | 代理配置与节点管理 |
| `数据获取指南.md` | 数据下载详细说明 |
