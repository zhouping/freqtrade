---
name: binance-proxy-auto-switch
title: Binance 代理自动切换脚本
description: 自动检测 Binance API 连通性，失败时自动切换到可用节点
tags: [binance, proxy, clash, automation]
related_skills: []
---

# Binance 代理自动切换脚本

自动检测 Binance API 连通性，失败时自动切换到可用节点。

## 关键发现（2026-04-22）

**最重要**：GLOBAL 组实际有 437 个节点，但 `clash-ctl list` **只显示前 10 个**！

必须通过 Clash API 直接获取完整节点列表：

```bash
SECRET="***"
curl -s -x "http://127.0.0.1:7897" --unix-socket /tmp/verge/verge-mihomo.sock \
  -H "Authorization: Bearer $SECRET" http://localhost/proxies | python3 -c "
import sys, json
data = json.load(sys.stdin)
proxies = data.get('proxies', {})
for name, info in proxies.items():
    if name == 'GLOBAL':
        nodes = info.get('all', [])
        for n in nodes:
            if n not in ['DIRECT', 'REJECT']:
                print(n)
"
```

旧方法（只获取 10 个节点，已废弃）：
- `clash-ctl list > /tmp/clash_list.txt`
- `grep "【GLOBAL】" -A2` 获取可用节点行

## 重要修复（2026-04-22）
1. 删除重复脚本预防多实例运行:
   - /home/kali/Project/freqtrade/user_data/scripts/binance_proxy.sh
   - /home/kali/Project/clash-verge-rev/binance_proxy.sh
2. 移除 head -10 限制，尝试所有节点

## 脚本位置
- `/binance_proxy.sh` - 主脚本
- cron: `*/3 * * * * /binance_proxy.sh >> /home/kali/TMP/binance_proxy.log 2>&1`

## 使用方法

### ⚠️ 如果切换失败
先将 Clash Verge 的代理模式改为**全局/GLOBAL**，再执行自动切换。

```bash
# 手动运行测试
/binance_proxy.sh

# 查看日志
tail -f /home/kali/TMP/binance_proxy.log
```

## 工作原理
1. 检测现货 + 期货 API
2. 都通 = 正常，退出
3. 失败则遍历 GLOBAL 组节点
4. 切换节点，测试 API
5. 成功则退出，失败继续下一个