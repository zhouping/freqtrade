#!/usr/bin/env python3
"""
测试不同代理节点连接TESTNET

流程:
1. 读取GLOBAL组的节点列表
2. 逐个切换节点测试
3. 使用freqtrade的ccxt库连接TESTNET获取元数据
4. 如果失败则尝试下一个节点
"""

import json
import subprocess
import time
import sys
import os

# 添加freqtrade目录到路径
sys.path.insert(0, '/home/kali/Project/freqtrade')
import ccxt

CLASH_CTL = "/home/kali/Project/clash-verge-rev/clash-ctl"
PROXY_PORT = 7897


def run_cmd(cmd):
    """运行shell命令"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode


def get_global_nodes():
    """获取GLOBAL组的节点列表"""
    output, _ = run_cmd(CLASH_CTL + " list")
    lines = output.split('\n')
    
    nodes = []
    in_global = False
    for line in lines:
        if '【GLOBAL】' in line:
            in_global = True
            continue
        if in_global and '可用节点' in line:
            # 提取节点名列表（在"可用节点: "之后的部分）
            parts = line.split('可用节点:')
            if len(parts) > 1:
                node_str = parts[1].strip()
                # 解析逗号分隔的节点名
                for node in node_str.split(','):
                    node = node.strip()
                    # 跳过特殊项
                    if node in ['DIRECT', 'REJECT', '🚀 节点选择', '♻️ 自动选择']:
                        continue
                    if node.startswith('🇭🇰') or node.startswith('🇹🇼') or node.startswith('🇸🇬') or \
                       node.startswith('🇯🇵') or node.startswith('🇺🇲') or node.startswith('🇰🇷'):
                        continue
                    if node:
                        nodes.append(node)
            break
    
    return nodes


def switch_node(node_name):
    """切换节点"""
    print(f"\n🔄 切换到节点: {node_name}")
    # 使用switch命令
    cmd = f'{CLASH_CTL} switch "GLOBAL" "{node_name}"'
    output, code = run_cmd(cmd)
    if code != 0:
        print(f"   切换命令输出: {output}")
    time.sleep(2)


def check_proxy_ip():
    """检查代理出口IP"""
    cmd = f'curl -s --max-time 5 -x http://127.0.0.1:{PROXY_PORT} https://api.ipify.org'
    output, code = run_cmd(cmd)
    if code == 0 and output and len(output) > 6:
        return output
    return None


def test_ccxt_testnet():
    """使用ccxt测试TESTNET连接"""
    try:
        # 创建binance exchange实例，使用testnet
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'aiohttp_trust_env': True,  # 信任环境变量代理
            'options': {
                'defaultMarket' : 'futures',
            },
        })
        exchange.set_sandbox_mode(True)  # 启用testnet模式
        
        # 获取markets元数据
        markets = exchange.fetch_markets()
        
        # 获取BTC/USDT的交易对信息
        btc_usdt = None
        for m in markets:
            if m['symbol'] == 'BTC/USDT':
                btc_usdt = m
                break
        
        if btc_usdt:
            return {
                'success': True,
                'symbol': btc_usdt['symbol'],
                'pricePrecision': btc_usdt['precision']['price'],
                'amountPrecision': btc_usdt['precision']['amount'],
                'minAmount': btc_usdt['limits']['amount']['min'],
                'maxAmount': btc_usdt['limits']['amount']['max'],
                'taker': btc_usdt['taker'],
                'maker': btc_usdt['maker'],
            }
        else:
            return {'success': False, 'error': 'BTC/USDT not found in markets'}
            
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    print("=" * 60)
    print("🔍 测试不同代理节点连接 Binance TESTNET")
    print("=" * 60)
    
    # 获取节点列表
    nodes = get_global_nodes()
    print(f"\n📋 GLOBAL组节点数量: {len(nodes)}")
    for i, node in enumerate(nodes[:5]):  # 只显示前5个
        print(f"   {i+1}. {node[:50]}...")
    if len(nodes) > 5:
        print(f"   ... 共 {len(nodes)} 个节点")
    
    # 测试每个节点
    success_count = 0
    for i, node in enumerate(nodes):
        print(f"\n{'='*60}")
        print(f"测试节点 {i+1}/{len(nodes)}: {node[:60]}")
        print(f"{'='*60}")
        
        # 切换节点
        switch_node(node)
        time.sleep(1)
        
        # 检查代理IP
        ip = check_proxy_ip()
        if ip:
            print(f"✅ 代理IP: {ip}")
        else:
            print(f"❌ 代理连接失败，跳过此节点")
            continue
        
        # 测试ccxt连接TESTNET
        result = test_ccxt_testnet()
        
        if result['success']:
            success_count += 1
            print(f"\n🎉 TESTNET连接成功!")
            print(f"   交易对: {result['symbol']}")
            print(f"   价格精度: {result['pricePrecision']}")
            print(f"   数量精度: {result['amountPrecision']}")
            print(f"   最小数量: {result['minAmount']}")
            print(f"   最大数量: {result['maxAmount']}")
            print(f"   Taker费率: {result['taker']}")
            print(f"   Maker费率: {result['maker']}")
            print(f"\n" + "="*60)
            print(f"✅ 成功! 当前节点: {node}")
            print(f"   代理IP: {ip}")
            print("="*60)
            return 0
        else:
            print(f"❌ TESTNET连接失败: {result['error']}")
    
    print(f"\n{'='*60}")
    print(f"❌ 所有节点测试完成，失败 {len(nodes)} 个节点")
    print(f"✅ 成功连接: {success_count} 个节点")
    print(f"{'='*60}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
