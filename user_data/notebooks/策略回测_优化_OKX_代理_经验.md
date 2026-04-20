# 策略回测_优化_OKX_代理_经验

> 测试日期: 2026-04-20

---

## 1. 核心发现

| 库 | 类型 | 代理配置方式 |
|---|------|-----------|
| `ccxt` | 同步 (基于 requests) | 必须显式配置 `proxies` |
| `ccxt.pro` | 异步 (基于 aiohttp) | 使用 `aiohttp_trust_env: true` |

**freqtrade 同时使用两者**：
- 交易操作 → 同步 ccxt (`ccxt_config`)
- 加载市场 → 异步 ccxt.pro (`ccxt_async_config`)

---

## 2. OKX 期货回测方案

### 2.1 OKX 期货不支持直接回测

- freqtrade 明确不支持 OKX 的 `futures` 交易模式
- 错误信息: `Freqtrade does not support 'futures' on OKX`

### 2.2 解决方案: 现货模式 + 期货数据

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

### 2.3 数据准备

**数据位置:**
- 期货数据: `/home/kali/Project/freqtrade/user_data/data/okx/futures/*.feather`
- 使用时复制到 spot 目录并重命名:
```bash
cp /home/kali/Project/freqtrade/user_data/data/okx/futures/*.feather /home/kali/Project/freqtrade/user_data/data/okx/spot/
# 将 BTC-USDT-5m-2025-01.feather 重命名为 BTC-USDT_5m.feather
```

**数据格式:**
- OKX 期货 feather 格式: `[timestamp, open, high, low, close, volume]`
- timestamp 为毫秒时间戳

### 2.4 回测命令

```bash
cd /home/kali/Project/freqtrade

freqtrade backtesting \
  -c user_data/config.json \
  --data-dir user_data/data/okx/spot \
  --timerange 20250101-20251231
```

### 2.5 回测结果保存规范

按规范保存到 `/home/kali/Project/freqtrade/user_data/backtest_results/`:
- 目录名: `策略名-交易所-交易品种-时间周期-日期-时间`
- 包含文件: result.csv (GBK编码), config.json, strategy_parameters.json, 策略源码.py

---

## 2. 代理节点测试流程

### 2.1 检查系统代理环境变量

```bash
echo "HTTP_PROXY: $HTTP_PROXY"
echo "HTTPS_PROXY: $HTTPS_PROXY"
```

预期输出：
```
HTTP_PROXY: http://127.0.0.1:7897
HTTPS_PROXY: http://127.0.0.1:7897
```

### 2.2 列出可用节点

```bash
/home/kali/Project/clash-verge-rev/clash-ctl list
```

### 2.3 切换代理节点

```bash
# 切换到美国节点组
/home/kali/Project/clash-verge-rev/clash-ctl switch "GLOBAL" "🇺🇲 美国节点"

# 验证代理出口
curl -s --max-time 5 -x http://127.0.0.1:7897 https://api.ipify.org
```

### 2.4 节点失败处理（重要！）

如果当前节点连接失败，按顺序尝试下一个节点：

```bash
# 查看美国节点列表
/home/kali/Project/clash-verge-rev/clash-ctl list | grep "🇺🇲 美国节点" -A 20

# 切换到特定节点
/home/kali/Project/clash-verge-rev/clash-ctl switch "GLOBAL" "20251228cf - US-443-WS-TLS"
```

**如果所有节点都失败 → 通知用户换代理IP**

---

## 3. 测试连接

### 3.1 同步 ccxt 测试

```python
import ccxt

okx = ccxt.okx({
    'proxies': {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897'
    }
})
markets = okx.fetch_markets()
print(f'✓ 同步 ccxt: {len(markets)} 个交易对')
```

**结果**: ✅ 成功获取 2907 个交易对

### 3.2 异步 ccxt.pro 测试

```python
import asyncio
import ccxt.pro as ccxt

async def test():
    okx = ccxt.okx({
        'aiohttp_trust_env': True
    })
    markets = await okx.fetch_markets()
    print(f'✓ 异步 ccxt.pro: {len(markets)} 个交易对')
    await okx.close()

asyncio.run(test())
```

**结果**: ✅ 成功获取 2907 个交易对

---

## 4. Freqtrade 配置模板

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

### 配置说明

| 配置项 | 用途 |
|--------|------|
| `ccxt_config.proxies` | 同步 ccxt 必须显式配置 |
| `ccxt_config.aiohttp_trust_env` | 备用（同步版不生效） |
| `ccxt_async_config.aiohttp_trust_env` | 异步 ccxt.pro 读取系统代理 |
| `enableRateLimit` | 启用限流 |

---

## 5. 验证命令

```bash
cd /home/kali/Project/freqtrade
freqtrade list-pairs --config user_data/config.json --print-json
```

**成功输出**:
```
Applying additional ccxt config: {'proxies': {...}, 'aiohttp_trust_env': True, ...}
Exchange OKX has 1196 active pairs.
```

---

## 6. 常见问题

### Q1: 同步 ccxt 超时
- **原因**: 未配置 `proxies`
- **解决**: 在 `ccxt_config` 中添加 `proxies`

### Q2: 异步 ccxt.pro 超时
- **原因**: `aiohttp_trust_env` 未生效
- **解决**: 确认环境变量 `HTTP_PROXY` 已设置

### Q3: 两者都超时
- **原因**: 代理节点被 OKX 封禁
- **解决**: 切换到其他代理节点

---

## 7. 测试结果汇总

| 测试项 | 配置 | 结果 |
|-------|------|------|
| 同步 ccxt | `proxies: {...}` | ✅ 2907 个交易对 |
| 异步 ccxt.pro | `aiohttp_trust_env: true` | ✅ 2907 个交易对 |
| freqtrade list-pairs | 同步+异步配置 | ✅ OKX 1196 交易对 |

---

## 8. 常见问题

### Q1: 同步 ccxt 超时
- **原因**: 未配置 `proxies`
- **解决**: 在 `ccxt_config` 中添加 `proxies`

### Q2: 异步 ccxt.pro 超时
- **原因**: `aiohttp_trust_env` 未生效
- **解决**: 确认环境变量 `HTTP_PROXY` 已设置

### Q3: 两者都超时
- **原因**: 代理节点被 OKX 封禁
- **解决**: 切换到其他代理节点

### Q4: "Freqtrade does not support 'futures' on OKX"
- **原因**: OKX 期货模式不被 freqtrade 支持
- **解决**: 使用现货模式 + 期货数据

### Q5: "No data found"
- **原因**: 数据文件位置或格式不匹配
- **解决**: 确认数据在 spot 目录，文件名为 BTC-USDT_5m.feather

---

## 9. 已验证可用的代理节点

| 日期 | 节点 | 出口IP |
|------|------|--------|
| 2025-04-19 | 🇺🇲 美国节点 | 178.128.16.74 |
| 2026-04-20 | 🇺🇲 美国节点 | 159.223.57.22 |

---

## 10. 环境变量检查

```bash
env | grep -i proxy
# 应显示：
# HTTP_PROXY=http://127.0.0.1:7897
# HTTPS_PROXY=http://127.0.0.1:7897
# ALL_PROXY=socks5://127.0.0.1:7897
```

---

## 11. 交易所连接状态汇总 (2026-04-20)

### 可用交易所（美国节点）

| 交易所 | 交易对数 | USDT交易对 | 状态 | 备注 |
|--------|----------|-----------|------|------|
| OKX | 2907 | 584 | ✅ 可用 | 目前唯一稳定 |
| Gate | - | - | ❌ 超时 | 需要进一步测试 |
| Binance | - | - | ❌ 451错误 | 被代理封禁 |
| Bybit | - | - | ❌ 超时 | - |
| HTX | - | - | ❌ 超时 | - |
| Kraken | - | - | ❌ 超时 | - |

### 期货模式支持

| 交易所 | 现货模式 | 期货模式 | 备注 |
|--------|----------|----------|------|
| OKX | ✅ | ❌ 不支持 | Freqtrade 不支持 OKX futures |
| Gate | ✅ | ✅ | 需要合并数据文件 |
| Binance | ✅ | ✅ | 被代理封禁 |

---

## 12. 数据文件格式汇总

### 现有数据目录

```
user_data/data/
├── binance/
│   └── spot/          # jsongz 格式
├── gate/
│   └── futures/      # feather 格式 (带月份后缀)
├── okx/
│   ├── spot/         # jsongz 格式
│   └── futures/      # feather 格式
└── htx/
    ├── spot/         # feather 格式 (较少)
    └── futures/      # feather 格式
```

### 文件名格式

| 交易所 | 类型 | 文件名格式 | dataformat_ohlcv |
|--------|------|------------|------------------|
| OKX | spot | `BTCUSDT_5m_2025-04-01_to_2025-04-30.jsongz` | `jsongz` |
| OKX | futures | `BTC-USDT-5m-2025-04.feather` | `feather` |
| Gate | futures | `BTC_USDT_USDT-5m-2025-04.feather` | `feather` |
| HTX | spot/futures | `BTC_USDT-5m.feather` | `feather` |

### 数据文件命名规范

Freqtrade 期望的文件名格式：
- **jsongz 实际扩展名**: `.json.gz` (freqtrade 内部映射为 jsongz)
- **文件名**: `{pair_s}-{timeframe}.json.gz`

其中：
- `pair_s` = `pair_to_filename(pair)` → `BTC/USDT` → `BTC_USDT`
- `timeframe` = `5m`

**示例**:
```bash
# 错误 ❌
BTCUSDT_5m_2025-04-01_to_2025-04-30.jsongz  (freqtrade 下载的格式)
BTC-USDT_5m.feather                    (手动下载的格式)

# 正确 ✅
BTC_USDT-5m.json.gz                   (freqtrade 期望的格式)
```

### 合并期货数据脚本

```python
import pandas as pd
import os

data_dir = 'user_data/data/gate/futures'
files = sorted([f for f in os.listdir(data_dir) 
             if f.startswith('BTC_USDT_USDT-5m-') and f.endswith('.feather')])

dfs = []
for f in files:
    df = pd.read_feather(os.path.join(data_dir, f))
    dfs.append(df)

# 合并并去重
merged = pd.concat(dfs, ignore_index=True)
merged = merged.drop_duplicates(subset=['timestamp']).sort_values('timestamp')

# 保存为标准文件名
merged.to_feather(f'{data_dir}/BTC_USDT_USDT_5m.feather')
```

---

## 13. 待解决问题

1. **OKX 回测数据找不到** - 现有 jsongz 文件无法被识别
2. **Gate 期货数据找不到** - 需要合并月份文件
3. **Binance 被封禁** - 代理节点被 Binance 封禁
4. **其他交易所超时** - 需要测试不同的代理节点

---

> 更新时间: 2026-04-20
> 来源: freqtrade-okx-ccxt-proxy-config skill + 测试
