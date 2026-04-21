#!/usr/bin/env python3
"""
批量运行freqtrade期货回测脚本
- 从策略汇总.csv读取所有策略
- 使用Binance testnet进行期货回测（5分钟，2024年全年）
- 结果保存到 backtest_results/
"""

import pandas as pd
import subprocess
import sys
import os
import json
from datetime import datetime

# 配置
CSV_PATH = '/home/kali/Project/freqtrade/user_data/notebooks/策略汇总.csv'
# 使用现货配置运行回测（期货数据通过data-dir指定）
CONFIG_PATH = '/home/kali/Project/freqtrade/user_data/config_binance_spot.json'
DATA_DIR = '/home/kali/Project/freqtrade/user_data/data/binance'
OUTPUT_DIR = '/home/kali/Project/freqtrade/user_data/backtest_results'
STRATEGY_BASE_DIR = '/home/kali/Project/freqtrade/user_data/strategies'

TIMEFRAME = '5m'
TIMERANGE = '20240101-20241231'
PAIR = 'BTC/USDT'  # 现货格式

def load_strategies():
    """从CSV读取策略列表"""
    print(f"📂 读取策略列表: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, encoding='gbk')
    
    strategies = []
    for idx, row in df.iterrows():
        strategy_name = row['策略名']
        strategy_path = row['路径']
        
        # 跳过空路径
        if pd.isna(strategy_path) or not strategy_path:
            continue
            
        strategies.append({
            'name': strategy_name,
            'path': strategy_path
        })
    
    print(f"✅ 共加载 {len(strategies)} 个策略")
    return strategies


def run_backtest(strategy_name, strategy_path):
    """运行单个策略的回测"""
    # 构建策略路径 - 路径是相对于 strategies 目录的
    # 例如: davidzr/strategies/ADXMomentum/ADXMomentum.py -> 目录是 davidzr/strategies/ADXMomentum/
    full_path = os.path.join(STRATEGY_BASE_DIR, strategy_path)
    
    # 确定strategy路径参数 (目录路径)
    strategy_path_arg = os.path.dirname(full_path)
    
    # 创建输出目录
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_dir = os.path.join(OUTPUT_DIR, f'{strategy_name}_期货5m_{timestamp}')
    os.makedirs(result_dir, exist_ok=True)
    
    # 构建命令
    cmd = [
        'python', '-m', 'freqtrade', 'backtesting',
        '-c', CONFIG_PATH,
        '-s', strategy_name,
        '--strategy-path', strategy_path_arg,
        '-i', TIMEFRAME,
        '--timerange', TIMERANGE,
        '-p', PAIR,
        '--export', 'trades',
        '--backtest-directory', result_dir
    ]
    
    print(f"\n🔄 运行回测: {strategy_name}")
    print(f"   策略路径: {strategy_path_arg}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd='/home/kali/Project/freqtrade',
            capture_output=True,
            text=True,
            timeout=600  # 10分钟超时
        )
        
        output = result.stdout + result.stderr
        
        # 保存完整输出
        output_file = os.path.join(result_dir, 'output.log')
        with open(output_file, 'w') as f:
            f.write(output)
        
        # 解析结果
        summary = parse_result(output, strategy_name)
        
        # 保存摘要
        summary_file = os.path.join(result_dir, 'summary.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        if summary.get('success'):
            print(f"   ✅ 成功 - 收益: {summary.get('profit_total', 'N/A')}")
        else:
            print(f"   ❌ 失败 - {summary.get('error', '未知错误')}")
        
        return summary
        
    except subprocess.TimeoutExpired:
        error_msg = f"❌ 超时 (10分钟)"
        print(f"   {error_msg}")
        return {'success': False, 'error': error_msg, 'strategy': strategy_name}
    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ 错误: {error_msg}")
        return {'success': False, 'error': error_msg, 'strategy': strategy_name}


def parse_result(output, strategy_name):
    """解析回测输出"""
    summary = {
        'strategy': strategy_name,
        'success': False,
        'profit_total': None,
        'profit_ratio': None,
        'total_trades': 0,
        'win_rate': None,
        'duration': None,
        'error': None
    }
    
    try:
        # 检查返回码
        if 'returncode' in output.lower() and '1' in output[output.lower().find('returncode'):output.lower().find('returncode')+20] if 'returncode' in output.lower() else False:
            # 检查具体错误
            if 'error' in output.lower() or 'exception' in output.lower():
                lines = output.split('\n')
                for line in lines:
                    if 'error' in line.lower() and 'traceback' not in line.lower():
                        summary['error'] = line.strip()
                        break
                if not summary['error']:
                    summary['error'] = '执行失败，请查看日志'
                return summary
        
        # 解析 STRATEGY SUMMARY 表格
        # 格式: │ ADXMomentum │    433 │        -0.19 │        -829.236 │        -8.29 │      4:34:00 │  178     0   255  41.1 │ 848.885 USDT  8.48% │
        lines = output.split('\n')
        for line in lines:
            # 查找包含策略名和数据的那一行
            if f'│ {strategy_name} │' in line:
                parts = [p.strip() for p in line.split('│') if p.strip()]
                if len(parts) >= 8:
                    try:
                        summary['total_trades'] = int(parts[1]) if parts[1].isdigit() else 0
                        summary['profit_total'] = parts[3]  # Tot Profit USDT
                        summary['profit_ratio'] = parts[4]  # Tot Profit %
                        summary['duration'] = parts[5]       # Avg Duration
                        summary['success'] = True
                        
                        # 尝试提取胜率 (parts[6] = "178     0   255  41.1")
                        if len(parts) >= 7:
                            win_info = parts[6]
                            win_parts = win_info.split()
                            if len(win_parts) >= 4:
                                summary['win_rate'] = win_parts[-1] + '%'
                    except (ValueError, IndexError) as e:
                        summary['error'] = f'解析失败: {str(e)}'
                break
        
        # 如果没找到策略名行，检查是否成功运行
        if not summary['success']:
            if 'Backtested' in output and 'STRATEGY SUMMARY' in output:
                summary['error'] = '未找到策略结果'
            elif 'Backtested' not in output:
                # 可能是其他错误
                for line in lines:
                    if 'ERROR' in line.upper() or 'FATAL' in line.upper():
                        summary['error'] = line.strip()
                        break
    
    except Exception as e:
        summary['error'] = f'解析异常: {str(e)}'
    
    return summary


def save_summary(results):
    """保存汇总结果"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file = os.path.join(OUTPUT_DIR, f'汇总_{timestamp}.csv')
    
    rows = []
    for r in results:
        rows.append({
            '策略名': r.get('strategy'),
            '成功': r.get('success'),
            '收益总额': r.get('profit_total'),
            '收益率': r.get('profit_ratio'),
            '交易次数': r.get('total_trades'),
            '耗时': r.get('duration'),
            '错误': r.get('error')
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(summary_file, index=False, encoding='utf-8-sig')
    print(f"\n📊 汇总结果已保存: {summary_file}")
    
    return summary_file


def main():
    print("=" * 60)
    print("🚀 Freqtrade 批量期货回测")
    print(f"   时间框架: {TIMEFRAME}")
    print(f"   时间段: {TIMERANGE}")
    print(f"   交易对: {PAIR}")
    print("=" * 60)
    
    # 加载策略
    strategies = load_strategies()
    
    # 运行回测
    results = []
    success_count = 0
    fail_count = 0
    
    for i, strategy in enumerate(strategies):
        print(f"\n[{i+1}/{len(strategies)}] ", end="")
        
        result = run_backtest(strategy['name'], strategy['path'])
        result['index'] = i + 1
        results.append(result)
        
        if result.get('success'):
            success_count += 1
        else:
            fail_count += 1
    
    # 保存汇总
    summary_file = save_summary(results)
    
    # 打印统计
    print("\n" + "=" * 60)
    print(f"📈 统计结果")
    print(f"   总计: {len(strategies)}")
    print(f"   成功: {success_count}")
    print(f"   失败: {fail_count}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())