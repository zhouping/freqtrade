#!/usr/bin/env python3
"""
Freqtrade 批量期货回测 Cronjob 入口脚本
从策略汇总.csv读取所有策略，执行期货5分钟K线回测（2024年全年）
结果保存到 backtest_results/
"""

import sys
import os

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

import batch_backtest_futures

if __name__ == '__main__':
    # 设置工作目录
    os.chdir('/home/kali/Project/freqtrade')
    
    print("=" * 70)
    print("🚀 Freqtrade 批量回测任务启动")
    print(f"   时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 运行主函数
    exit_code = batch_backtest_futures.main()
    
    print(f"\n✅ 任务完成，退出码: {exit_code}")
    sys.exit(exit_code)