#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 策略优化 V2 - 组选投注比例优化
组六 60% + 组三 30% + 直选 10%
"""

import json
from collections import Counter
from datetime import datetime
from itertools import combinations

DATA_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_history.json"


def load_history():
    """加载福彩 3D 历史数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])


def calculate_omission(history, num, max_lookback=50):
    """计算遗漏期数"""
    omission = 0
    for draw in history[:max_lookback]:
        if num in draw['numbers']:
            break
        omission += 1
    return omission


def calculate_frequency(history, num, max_lookback=50):
    """计算出现频率"""
    count = 0
    for draw in history[:max_lookback]:
        if num in draw['numbers']:
            count += 1
    return count


def get_optimized_hot_nums(history, top_n=5, lookback=50):
    """优化后的热号选择"""
    hot_candidates = []
    for num in range(10):
        omission = calculate_omission(history, num, lookback)
        frequency = calculate_frequency(history, num, lookback)
        score = frequency * 0.7 - omission * 0.3
        hot_candidates.append((num, score, omission, frequency))
    hot_candidates.sort(key=lambda x: x[1], reverse=True)
    return [(n, s, o, f) for n, s, o, f in hot_candidates[:top_n]]


def get_optimized_cold_nums(history, top_n=5, lookback=50):
    """优化后的冷号选择"""
    cold_candidates = []
    for num in range(10):
        omission = calculate_omission(history, num, lookback)
        frequency = calculate_frequency(history, num, lookback)
        score = omission * 0.6 + (lookback - frequency) * 0.4
        cold_candidates.append((num, score, omission, frequency))
    cold_candidates.sort(key=lambda x: x[1], reverse=True)
    return [(n, s, o, f) for n, s, o, f in cold_candidates[:top_n]]


def analyze_pattern(numbers):
    """分析号码形态"""
    counter = Counter(numbers)
    if len(counter) == 1:
        return "豹子"
    elif len(counter) == 2:
        return "组三"
    else:
        return "组六"


def generate_group6_bets(nums, count=3):
    """生成组六投注（3 个不同号）"""
    bets = []
    for combo in combinations(nums, 3):
        bets.append({
            'type': '组六',
            'numbers': list(combo),
            'cost': 2
        })
        if len(bets) >= count:
            break
    return bets


def generate_group3_bets(nums, count=2):
    """生成组三投注（2 个相同号）"""
    bets = []
    for num in nums[:3]:  # 前 3 个热号作为对子
        for other in nums:
            if num != other:
                bets.append({
                    'type': '组三',
                    'numbers': [num, num, other],
                    'cost': 2
                })
                if len(bets) >= count:
                    break
        if len(bets) >= count:
            break
    return bets


def generate_direct_bets(nums, count=1):
    """生成直选投注"""
    bets = []
    for combo in combinations(nums, 3):
        bets.append({
            'type': '直选',
            'numbers': list(combo),
            'cost': 2
        })
        if len(bets) >= count:
            break
    return bets


def check_prize(bet, draw_numbers):
    """检查中奖"""
    bet_nums = bet['numbers']
    bet_type = bet['type']
    draw_pattern = analyze_pattern(draw_numbers)
    
    # 直选：号码和顺序完全匹配
    if bet_type == '直选' and bet_nums == draw_numbers:
        return "直选", 1040
    
    # 组选：号码匹配但顺序不限
    if Counter(bet_nums) == Counter(draw_numbers):
        if bet_type == '组三' and draw_pattern == '组三':
            return "组三", 346
        elif bet_type == '组六' and draw_pattern == '组六':
            return "组六", 173
        elif bet_type == '组六' and draw_pattern == '组三':
            return "组三", 346  # 组六投注中组三也算中
    
    return None, 0


def run_optimization_v2(periods=100):
    """
    运行优化 V2 回测
    投注比例：组六 60% + 组三 30% + 直选 10%
    """
    print("=" * 70)
    print("福彩 3D 策略优化 V2 - 组选投注比例优化")
    print("=" * 70)
    
    # 加载历史数据
    print("\n📖 加载历史数据...")
    history = load_history()
    print(f"   总数据量：{len(history)} 期")
    
    # 取最近 N 期（从旧到新排序）
    recent = history[:periods][::-1]
    print(f"   回测期数：{periods} 期")
    print(f"   时间范围：{recent[0]['draw_date']} 至 {recent[-1]['draw_date']}")
    
    # 初始化统计
    initial_capital = 10000
    capital = initial_capital
    total_invested = 0
    total_prize = 0
    wins = 0
    details = []
    
    # 策略统计
    strategy_stats = {
        "热号追踪 (V2)": {"invested": 0, "prize": 0, "wins": 0},
        "冷号反弹 (V2)": {"invested": 0, "prize": 0, "wins": 0},
        "均衡策略 (V2)": {"invested": 0, "prize": 0, "wins": 0},
    }
    
    # 形态统计
    pattern_stats = {
        "组六": {"bets": 0, "wins": 0, "prize": 0},
        "组三": {"bets": 0, "wins": 0, "prize": 0},
        "直选": {"bets": 0, "wins": 0, "prize": 0},
    }
    
    print("\n📊 开始回测...")
    print("   投注比例：组六 60% + 组三 30% + 直选 10%")
    
    for i, draw in enumerate(recent):
        draw_numbers = draw['numbers']
        draw_date = draw['draw_date']
        issue = draw['issue']
        
        # 使用之前 50 期数据计算热号冷号
        start_idx = max(0, i - 50)
        past_data = history[start_idx:i] if i > 0 else []
        
        if len(past_data) >= 10:
            hot_nums = get_optimized_hot_nums(past_data, top_n=6, lookback=50)
            cold_nums = get_optimized_cold_nums(past_data, top_n=6, lookback=50)
            hot_list = [n[0] for n in hot_nums]
            cold_list = [n[0] for n in cold_nums]
        else:
            hot_list = [2, 1, 5, 0, 7, 4]
            cold_list = [9, 3, 8, 4, 6, 0]
        
        # 生成各策略投注（优化 V2 比例）
        # 热号策略：组六 3 注 + 组三 2 注 + 直选 1 注 = 6 注
        hot_group6 = generate_group6_bets(hot_list, 3)
        hot_group3 = generate_group3_bets(hot_list, 2)
        hot_direct = generate_direct_bets(hot_list, 1)
        hot_bets = hot_group6 + hot_group3 + hot_direct
        
        # 冷号策略：组六 3 注 + 组三 2 注 + 直选 1 注 = 6 注
        cold_group6 = generate_group6_bets(cold_list, 3)
        cold_group3 = generate_group3_bets(cold_list, 2)
        cold_direct = generate_direct_bets(cold_list, 1)
        cold_bets = cold_group6 + cold_group3 + cold_direct
        
        # 均衡策略：组六 3 注 + 组三 2 注 + 直选 1 注 = 6 注
        balanced_group6 = generate_group6_bets(list(range(10)), 3)
        balanced_group3 = generate_group3_bets(list(range(10)), 2)
        balanced_direct = generate_direct_bets(list(range(10)), 1)
        balanced_bets = balanced_group6 + balanced_group3 + balanced_direct
        
        # 统计本期投注
        period_invested = 0
        period_prize = 0
        period_wins = 0
        
        # 热号追踪
        for bet in hot_bets:
            period_invested += bet['cost']
            strategy_stats["热号追踪 (V2)"]["invested"] += bet['cost']
            pattern_stats[bet['type']]["bets"] += 1
            
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["热号追踪 (V2)"]["prize"] += prize_amount
                strategy_stats["热号追踪 (V2)"]["wins"] += 1
                pattern_stats[bet['type']]["wins"] += 1
                pattern_stats[bet['type']]["prize"] += prize_amount
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "热号追踪 (V2)",
                    "bet": bet['numbers'],
                    "type": bet['type'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 冷号反弹
        for bet in cold_bets:
            period_invested += bet['cost']
            strategy_stats["冷号反弹 (V2)"]["invested"] += bet['cost']
            pattern_stats[bet['type']]["bets"] += 1
            
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["冷号反弹 (V2)"]["prize"] += prize_amount
                strategy_stats["冷号反弹 (V2)"]["wins"] += 1
                pattern_stats[bet['type']]["wins"] += 1
                pattern_stats[bet['type']]["prize"] += prize_amount
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "冷号反弹 (V2)",
                    "bet": bet['numbers'],
                    "type": bet['type'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 均衡策略
        for bet in balanced_bets:
            period_invested += bet['cost']
            strategy_stats["均衡策略 (V2)"]["invested"] += bet['cost']
            pattern_stats[bet['type']]["bets"] += 1
            
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["均衡策略 (V2)"]["prize"] += prize_amount
                strategy_stats["均衡策略 (V2)"]["wins"] += 1
                pattern_stats[bet['type']]["wins"] += 1
                pattern_stats[bet['type']]["prize"] += prize_amount
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "均衡策略 (V2)",
                    "bet": bet['numbers'],
                    "type": bet['type'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        total_invested += period_invested
        total_prize += period_prize
        wins += period_wins
        capital = initial_capital - total_invested + total_prize
        
        if (i + 1) % 20 == 0:
            print(f"   [进度] 第{i+1}期：投入¥{period_invested} 中奖¥{period_prize} 资金¥{capital}")
    
    # 计算指标
    roi = (total_prize - total_invested) / total_invested * 100 if total_invested > 0 else 0
    win_rate = wins / (periods * 18) * 100 if periods > 0 else 0  # 18 注/期
    
    # 生成报告
    print("\n" + "=" * 70)
    print("📊 回测结果")
    print("=" * 70)
    
    print(f"\n💰 总体表现")
    print(f"   初始资金：¥{initial_capital:,}")
    print(f"   总投入：¥{total_invested:,}")
    print(f"   总奖金：¥{total_prize:,}")
    print(f"   净收益：¥{total_prize - total_invested:,}")
    print(f"   ROI：{roi:.2f}%")
    print(f"   中奖次数：{wins} 次")
    print(f"   中奖率：{win_rate:.2f}%")
    print(f"   最终资金：¥{capital:,}")
    
    print(f"\n📊 策略对比")
    for strategy, stats in strategy_stats.items():
        s_roi = (stats['prize'] - stats['invested']) / stats['invested'] * 100 if stats['invested'] > 0 else 0
        s_win_rate = stats['wins'] / (periods * 6) * 100 if periods > 0 else 0
        print(f"\n   {strategy}:")
        print(f"      投入：¥{stats['invested']:,} | 奖金：¥{stats['prize']:,} | 收益：¥{stats['prize'] - stats['invested']:,}")
        print(f"      ROI：{s_roi:.2f}% | 中奖：{stats['wins']}次 | 中奖率：{s_win_rate:.2f}%")
    
    print(f"\n🎯 形态分布统计")
    for pattern, stats in pattern_stats.items():
        hit_rate = stats['wins'] / stats['bets'] * 100 if stats['bets'] > 0 else 0
        print(f"   {pattern}: 投注{stats['bets']}次 中奖{stats['wins']}次 命中率{hit_rate:.2f}% 奖金¥{stats['prize']:,}")
    
    print(f"\n🏆 中奖详情（前 10 次）")
    for d in details[:10]:
        print(f"   {d['date']} {d['issue']} {d['strategy']} [{d['type']}{d['bet']}] vs [{d['draw']}] → {d['prize']} ¥{d['amount']}")
    
    # 保存报告
    report_file = "/root/.openclaw/workspace/lottery/stats/fc3d_optimization_v2_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"福彩 3D 策略优化 V2 回测报告\n")
        f.write(f"生成时间：{datetime.now().isoformat()}\n")
        f.write(f"回测期数：{periods} 期\n")
        f.write(f"投注比例：组六 60% + 组三 30% + 直选 10%\n\n")
        f.write(f"总体表现:\n")
        f.write(f"  ROI: {roi:.2f}%\n")
        f.write(f"  净收益：¥{total_prize - total_invested:,}\n")
        f.write(f"  中奖率：{win_rate:.2f}%\n\n")
        f.write(f"策略对比:\n")
        for strategy, stats in strategy_stats.items():
            s_roi = (stats['prize'] - stats['invested']) / stats['invested'] * 100 if stats['invested'] > 0 else 0
            f.write(f"  {strategy}: ROI {s_roi:.2f}%, 中奖{stats['wins']}次\n")
        f.write(f"\n形态分布:\n")
        for pattern, stats in pattern_stats.items():
            hit_rate = stats['wins'] / stats['bets'] * 100 if stats['bets'] > 0 else 0
            f.write(f"  {pattern}: {stats['bets']}投 {stats['wins']}中 命中率{hit_rate:.2f}%\n")
    
    print(f"\n📄 完整报告：{report_file}")
    print("\n" + "=" * 70)
    
    # 与 V1 对比
    print("\n📈 与 V1 对比")
    print(f"   V1 ROI: -42.33% | V2 ROI: {roi:.2f}%")
    print(f"   V1 中奖率：0.67% | V2 中奖率：{win_rate:.2f}%")
    if roi > -42.33:
        print(f"   ✅ V2 表现优于 V1")
    else:
        print(f"   ⚠️ V2 表现待改进")
    
    return {
        "periods": periods,
        "total_invested": total_invested,
        "total_prize": total_prize,
        "roi": roi,
        "win_rate": win_rate,
        "strategy_stats": strategy_stats,
        "pattern_stats": pattern_stats,
        "details": details
    }


if __name__ == "__main__":
    run_optimization_v2(periods=100)
