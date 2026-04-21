#!/usr/bin/env python3
"""
批量运行 freqtrade hyperopt 优化所有策略
"""
import subprocess
import os
import time
import json
import re

# 策略列表
strategies = [
    "GodStra", "Supertrend", "UniversalMACD", "Bandtastic", "BreakEven", 
    "CustomStoplossWithPSAR", "Diamond", "FixedRiskRewardLoss", "Heracles", 
    "HourBasedStrategy", "InformativeSample", "MultiMa", "PatternRecognition", 
    "PowerTower", "Strategy001", "Strategy001_custom_exit", "Strategy002", 
    "Strategy003", "Strategy004", "Strategy005", "SwingHighToSky", "hlhb", 
    "mabStra", "multi_tf", "vegas_strategy",
    "lookahead_bias/GodStraNew", "lookahead_bias/DevilStra", "lookahead_bias/Zeus", "lookahead_bias/wtc",
    "futures/FAdxSmaStrategy", "futures/FOttStrategy", "futures/FReinforcedStrategy", "futures/FSampleStrategy",
    "futures/FSupertrendStrategy", "futures/TrendFollowingStrategy", "futures/VolatilitySystem",
    "berlinguyinca/Low_BB", "berlinguyinca/CCIStrategy", "berlinguyinca/TechnicalExampleStrategy", 
    "berlinguyinca/SmoothScalp", "berlinguyinca/ClucMay72018", "berlinguyinca/ASDTSRockwellTrading", 
    "berlinguyinca/MultiRSI", "berlinguyinca/ReinforcedAverageStrategy", "berlinguyinca/SmoothOperator",
    "berlinguyinca/CofiBitStrategy", "berlinguyinca/BinHV27", "berlinguyinca/MACDStrategy_crossed",
    "berlinguyinca/BinHV45", "berlinguyinca/ADXMomentum", "berlinguyinca/MACDStrategy",
    "berlinguyinca/ReinforcedSmoothScalp", "berlinguyinca/Scalp", "berlinguyinca/AdxSmas",
    "berlinguyinca/Simple", "berlinguyinca/BbandRsi", "berlinguyinca/AwesomeMacd",
    "berlinguyinca/AverageStrategy", "berlinguyinca/EMASkipPump", "berlinguyinca/CMCWinner",
    "berlinguyinca/CombinedBinHAndCluc", "berlinguyinca/DoesNothingStrategy",
    "berlinguyinca/Freqtrade_backtest_validation_freqtrade1", "berlinguyinca/Quickie",
    "berlinguyinca/ReinforcedQuickie", "berlinguyinca/ReinforcedSmoothOperator"
]

timestamp = time.strftime("%Y%m%d_%H%M%S")
results = []

output_dir = f"/home/kali/Project/freqtrade/user_data/backtest_results/批量优化_{timestamp}"
os.makedirs(output_dir, exist_ok=True)

print(f"Output: {output_dir}, Total: {len(strategies)}")
print("=" * 60)

for idx, strategy in enumerate(strategies, 1):
    strategy_name = strategy.replace("/", "_")
    strategy_dir = os.path.join(output_dir, f"{strategy_name}_优化_{timestamp}")
    os.makedirs(strategy_dir, exist_ok=True)
    
    print(f"[{idx}/{len(strategies)}] {strategy}...", end=" ")
    
    cmd = [
        "freqtrade", "hyperopt", "--strategy", strategy,
        "--config", "user_data/config.json",
        "--hyperopt-loss", "SharpeHyperOptLoss",
        "-e", "30", "--spaces", "roi", "stoploss",
        "--pairs", "BTC/USDT", "--datadir", "user_data/data/htx",
        "--timerange", "20260101-"
    ]
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, cwd="/home/kali/Project/freqtrade", 
                              capture_output=True, text=True, timeout=300)
        elapsed = time.time() - start_time
        
        # 关键：结果在 stdout，不是 stderr
        combined = result.stdout + "\n" + result.stderr
        
        # 解析结果
        trades = win_rate = profit = profit_pct = objective = 0
        stoploss = 0
        roi = "{}"
        
        if "Best result:" in combined:
            section = combined.split("Best result:")[-1]
            tr = re.search(r'(\d+)\s+trades', section)
            win = re.search(r'(\d+)/(\d+)/(\d+)\s+Wins', section)
            prof = re.search(r'Total profit\s+([-\d.]+)\s+USDT\s+\(([-\d.]+)%\)', section)
            obj = re.search(r'Objective:\s+([-\d.]+)', section)
            
            if tr: trades = int(tr.group(1))
            if win and trades:
                win_rate = round(int(win.group(1)) / trades * 100, 1)
            if prof:
                profit = float(prof.group(1))
                profit_pct = float(prof.group(2))
            if obj: objective = float(obj.group(1))
        
        # 提取参数
        sl = re.search(r'stoploss\s*=\s*([-\d.]+)', combined)
        if sl: stoploss = float(sl.group(1))
        
        r_match = re.search(r'minimal_roi\s*=\s*\{([^}]+)\}', combined)
        if r_match: roi = "{" + r_match.group(1) + "}"
        
        results.append({
            "strategy": strategy, "exit_code": result.returncode,
            "trades": trades, "win_rate": win_rate,
            "profit_usdt": profit, "profit_pct": profit_pct,
            "objective": objective, "elapsed_seconds": round(elapsed, 1),
            "stoploss": stoploss, "roi": roi
        })
        
        print(f"✓ trades={trades}, win={win_rate}%, profit={profit_pct}%, obj={objective}")
        
    except subprocess.TimeoutExpired:
        results.append({"strategy": strategy, "exit_code": -1, "error": "timeout"})
        print("✗ Timeout")
    except Exception as e:
        results.append({"strategy": strategy, "exit_code": -1, "error": str(e)})
        print(f"✗ Error: {e}")

print("=" * 60)
print("Saving...")

# 保存JSON
with open(os.path.join(output_dir, "优化详细结果.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

# 保存CSV
csv_path = os.path.join(output_dir, "优化结果汇总.csv")
with open(csv_path, "w", encoding="utf-8") as f:
    f.write("策略名,退出代码,交易次数,胜率(%),利润(USDT),利润(%),目标函数值,耗时(秒),stoploss,minimal_roi\n")
    for r in results:
        f.write(f"{r.get('strategy','')},{r.get('exit_code','')},{r.get('trades','')},{r.get('win_rate','')},{r.get('profit_usdt','')},{r.get('profit_pct','')},{r.get('objective','')},{r.get('elapsed_seconds','')},{r.get('stoploss','')},{r.get('roi','')}\n")

success = sum(1 for r in results if r.get('exit_code') == 0)
print(f"Done: {success}/{len(results)} succeeded")
print(f"CSV: {csv_path}")