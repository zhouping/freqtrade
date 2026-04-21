---
# 严重警告！严禁使用 "现货模式+期货数据" 方式进行回测和hyperopt操作

###==========以上文字严禁删除！！！！！！！=================


name: freqtrade-proxy-config
title: Freqtrade 代理配置与节点管理
description: 同步/异步 ccxt 代理配置、Clash Verge 节点测试与切换、OKX/Binance/Gate 交易所连接验证
trigger: freqtrade 代理 / proxy 配置 / 节点测试 / ccxt 超时 / 连接失败
tags: [freqtrade, proxy, ccxt, ccxt.pro, aiohttp_trust_env, clash, 节点切换]
---

# Freqtrade 代理配置与节点管理

## 核心原理

| 库 | 类型 | 代理配置方式 | 说明 |
|----|------|-------------|------|
| `ccxt` | 同步 (requests) | 必须显式配置 `proxies` | 交易操作 |
| `ccxt.pro` | 异步 (aiohttp) | `aiohttp_trust_env: true` | 加载市场 |
| freqtrade | 混合 | 两者都需要 | 同时使用 ccxt + ccxt.pro |

**freqtrade 同时使用两者：**
- 交易操作 → 同步 ccxt (`ccxt_config`)
- 加载市场 → 异步 ccxt.pro (`ccxt_async_config`)

## 代理配置模板

### 标准配置（适用于 Binance/OKX/Gate/HTX）

```json
{
  "exchange": {
    "name": "{exchange_name}",
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

### 最小配置（仅 aiohttp_trust_env）

如果只用异步（不需要同步 proxies）：

```json
{
  "exchange": {
    "name": "binance",
    "ccxt_config": {
      "aiohttp_trust_env": true,
      "enableRateLimit": true
    },
    "ccxt_async_config": {
      "aiohttp_trust_env": true,
      "enableRateLimit": true
    }
  }
}
```

### Binance Testnet 专用

```json
{
  "exchange": {
    "name": "binance",
    "key": "",
    "secret": "",
    "ccxt_config": {
      "enableRateLimit": true,
      "aiohttp_trust_env": true
    },
    "pair_whitelist": ["BTC/USDT"],
    "trading_mode": "spot"
  }
}
```

### OKX 专用（最稳定）

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
      "timeout": 30000
    },
    "ccxt_async_config": {
      "aiohttp_trust_env": true,
      "timeout": 30000
    }
  }
}
```

### HTX 专用

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

## 代理节点管理

### 查看节点列表

```bash
/home/kali/Project/clash-verge-rev/clash-ctl list
```

### 切换节点

```bash
# 切换到 GLOBAL 组美国节点
/home/kali/Project/clash-verge-rev/clash-ctl switch "GLOBAL" "🇺🇲 美国节点"
```

### 验证代理出口

```bash
curl -s --max-time 5 -x http://127.0.0.1:7897 https://api.ipify.org
```

### 测试脚本

```bash
cd /home/kali/Project/freqtrade
python user_data/scripts/test_proxy_for_testnet.py
```

**脚本位置：** `user_data/scripts/test_proxy_for_testnet.py`

## 测试连接

### 同步 ccxt 测试

```python
import ccxt

exchange = ccxt.okx({
    'proxies': {
        'http': 'http://127.0.0.1:7897',
        'https': 'http://127.0.0.1:7897'
    }
})
markets = exchange.fetch_markets()
print(f'✓ 同步 ccxt: {len(markets)} 个交易对')
```

### 异步 ccxt.pro 测试

```python
import asyncio
import ccxt.pro as ccxt_pro

async def test():
    exchange = ccxt_pro.okx({'aiohttp_trust_env': True})
    markets = await exchange.fetch_markets()
    print(f'✓ 异步 ccxt.pro: {len(markets)} 个交易对')
    await exchange.close()

asyncio.run(test())
```

### freqtrade 验证命令

```bash
cd /home/kali/Project/freqtrade
freqtrade list-pairs --config user_data/config.json --print-json
```

成功输出示例：
```
Applying additional ccxt config: {'proxies': {...}, 'aiohttp_trust_env': True, ...}
Exchange OKX has 1196 active pairs.
```

## 常见问题

### Q1: 同步 ccxt 超时
- 原因：未配置 `proxies`
- 解决：显式添加 `ccxt_config.proxies`

### Q2: 异步 ccxt.pro 超时
- 原因：`aiohttp_trust_env` 未生效
- 解决：确认 `ccxt_async_config.aiohttp_trust_env: true`

### Q3: 两者都超时
- 原因：代理节点被交易所封禁
- 解决：切换到其他代理节点

### Q4: ValueError: port can't be converted
- 原因：使用了 `proxy` 单数格式
- 解决：使用 `proxies` 复数格式

### Q5: RequestTimeout (freqtrade hyperopt)
- 原因：Hyperopt 需要连接交易所加载市场，即使有本地数据
- 解决：确保代理配置正确，或使用 backtesting 离线运行

## curl vs Python 对比

| 访问方式 | 需要代理？ | 结果 |
|---------|-----------|------|
| curl 直接 | 不需要 | ✓ 成功 |
| curl 走代理 | 需要 | ✓ 成功 |
| Python requests | 不需要 | ✓ 成功 |
| **Python ccxt 同步** | **需要 proxies** | **✓ 成功** |
| Python ccxt.pro 异步 | 需要 aiohttp_trust_env | ✓ 成功 |

## 环境变量检查

```bash
env | grep -i proxy
# 应显示：
# HTTP_PROXY=http://127.0.0.1:7897
# HTTPS_PROXY=http://127.0.0.1:7897
```