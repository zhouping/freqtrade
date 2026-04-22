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

## Feather 数据格式关键陷阱（2026-04 实测）

### 目录结构陷阱

| 交易模式 | 数据目录结构 | 示例 |
|----------|------------|------|
| **现货 SPOT** | 直接在 `--datadir/` 下 | `datadir/BTC_USDT-5m.feather` |
| **期货 FUTURES** | 在 `--datadir/futures/` 下 | `datadir/futures/BTC_USDT-5m-futures.feather` |

- ❌ 现货数据放在 `--datadir/spot/` 子目录下 → 报 `No history found`
- ❌ 期货数据放在 `--datadir/` 根目录下 → 找不到

### Feather date 列格式陷阱

- ❌ `date` 列是 pandas `datetime64[ns]` → 报 `No history found`
- ✅ `date` 列必须是 `int64` 毫秒时间戳
  ```python
  df['date'] = df['date'].astype('int64') // 10**6  # 纳秒转毫秒
  df.to_feather('file.feather', compression='lz4', compression_level=9)
  ```

### 文件名格式陷阱

- ❌ 下载脚本输出 `BTCUSDT_5m_2025.feather` → freqtrade 找不到
- ✅ freqtrade 标准格式：`BTC_USDT-5m.feather`

## 关键发现（2026-04-22 实测）

### ❌ 不需要 Binance Testnet

**错误观念：** 回测需要 Testnet 避免封禁

**正确做法：** 直接使用 Binance 主网 + 代理

原因：
- Binance Testnet 已不支持期货（ccxt 源码确认）
- Testnet 数据质量差，与主网有差异
- 只需要代理连接 `api.binance.com` / `fapi.binance.com`

### ✅ 现货和期货回测都需要代理

| 模式 | 是否需要代理 | 说明 |
|------|------------|------|
| 现货 | ✅ 需要 | 连接 Binance API 验证交易对 |
| 期货 | ✅ 需要 | 连接 Binance API 验证期货交易对 |

即使有本地数据，freqtrade 回测时仍会连接 Binance API。

### ✅ 代理配置（2026-04-23 更新）

```bash
# ⚠️ 必须使用 socks5h:// 格式，不是 http://
export https_proxy=socks5h://127.0.0.1:7897
export http_proxy=socks5h://127.0.0.1:7897
export all_proxy=socks5h://127.0.0.1:7897
```

freqtrade 配置中添加：
```json
"ccxt_config": {
  "aiohttp_trust_env": true,
  "requests_trust_env": true  // ⚠️ 必须同时添加！
}
```

**关键发现：**
- ccxt 同步模式使用 `requests` 库，需要 `requests_trust_env: true`
- ccxt 异步模式使用 `aiohttp` 库，需要 `aiohttp_trust_env: true`
- freqtrade 回测两者都用到，必须同时设置

## 来源

本纠正来自 2026-04-22 与用户 Joey 的对话。

## 数据文件名格式（2026-04-23 更新）

### 目录结构陷阱

| 交易模式 | 数据目录结构 | 示例 |
|----------|------------|------|
| **现货 SPOT** | 直接在 `binance/` 下 | `binance/BTC_USDT-5m.feather` |
| **期货 FUTURES** | 在 `binance/futures/` 下 | `binance/futures/BTC_USDT_USDT-5m-futures.feather` |

- ❌ 现货数据放在 `binance/spot/` 子目录下 → 报 `No history found`
- ❌ 期货数据放在 `binance/` 根目录下 → 找不到

### Feather date 列格式陷阱

- ❌ `date` 列是 pandas `datetime64[ns]` → 报 `No history found`
- ✅ `date` 列必须是 `int64` 毫秒时间戳
  ```python
  df['date'] = df['date'].astype('int64') // 10**6  # 纳秒转毫秒
  df.to_feather('file.feather', compression='lz4', compression_level=9)
  ```

### 文件名格式陷阱

- ❌ 下载脚本输出 `BTCUSDT_USDT_5m_2025.feather` → freqtrade 找不到
- ❌ 下载脚本输出 `BTCUSDT_USDT-5m-futures.feather` → freqtrade 找不到（缺少下划线）
- ✅ freqtrade 标准格式：`BTC_USDT_USDT-5m-futures.feather`（注意中间的 `_USDT_`）