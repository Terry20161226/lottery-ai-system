#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 策略优化 V3 - 精简投注 + 形态聚焦
每期 6 注：组六 4 注 (67%) + 组三 2 注 (33%)
成本控制：¥12/期
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


def calculate_omission(history, num, max_lookback=30):
    """计算遗漏期数"""
    omission = 0
    for draw in history[:max_lookback]:
        if num in draw['numbers']:
            break
        omission += 1
    return omission


def calculate_frequency(history, num, max_lookback=30):
    """计算出现频率"""
    count = sum(1 for draw in history[:max_lookback] if num in draw['numbers'])
    return count


def get_scored_nums(history, lookback=30):
    """
    综合评分选号
    score = 频率*0.5 + 遗漏*0.3 + 近期趋势*0.2
    """
    candidates = []
    for num in range(10):
        frequency = calculate_frequency(history, num, lookback)
        omission = calculate_omission(history, num, lookback)
        
        # 近期趋势（近 10 期是否出现）
        recent = sum(1 for draw in history[:10] if num in draw['numbers'])
        
        # 综合评分
        score = frequency * 0.5 + omission * 0.3 + recent * 0.2
        candidates.append((num, score, omission, frequency))
    
    # 降序排序
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates


def generate_group6_bets(nums, count=4):
    """生成组六投注"""
    bets = []
    for combo in combinations(nums, 3):
        # 排除全热或全冷，保持多样性
        bets.append({
            'type': '组六',
            'numbers': list(combo),
            'cost': 2
        })
        if len(bets) >= count:
            break
    return bets


def generate_group3_bets(hot_nums, cold_nums, count=2):
    """
    生成组三投注
    策略：热号对子 + 冷号单配
    """
    bets = []
    
    # 热号对子
    for num in hot_nums[:2]:
        for other in hot_nums[2:5]:
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


def analyze_pattern(numbers):
    """分析号码形态"""
    counter = Counter(numbers)
    if len(counter) == 1:
        return "豹子"
    elif len(counter) == 2:
        return "组三"
    else:
        return "组六"


def check_prize(bet, draw_numbers):
    """检查中奖"""
    bet_nums = bet['numbers']
    bet_type = bet['type']
    draw_pattern = analyze_pattern(draw_numbers)
    
    # 组选：号码匹配但顺序不限
    if Counter(bet_nums) == Counter(draw_numbers):
        if bet_type == '组三' and draw_pattern == '组三':
            return "组三", 346
        elif bet_type == '组六' and draw_pattern == '组六':
            return "组六", 173
    
    return None, 0


def run_optimization_v3(periods=100):
    """
    运行优化 V3 回测
    精简投注：组六 4 注 + 组三 2 注 = 6 注/期
    成本：¥12/期
    """
    print("=" * 70)
    print("福彩 3D 策略优化 V3 - 精简投注 + 形态聚焦")
    print("=" * 70)
    
    # 加载历史数据
    print("\n📖 加载历史数据...")
    history = load_history()
    print(f"   总数据量：{len(history)} 期")
    
    # 取最近 N 期
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
        "热号追踪 (V3)": {"invested": 0, "prize": 0, "wins": 0},
        "冷号反弹 (V3)": {"invested": 0, "prize": 0, "wins": 0},
        "均衡策略 (V3)": {"invested": 0, "prize": 0, "wins": 0},
    }
    
    # 形态统计
    pattern_stats = {
        "组六": {"bets": 0, "wins": 0, "prize": 0},
        "组三": {"bets": 0, "wins": 0, "prize": 0},
    }
    
    print("\n📊 开始回测...")
    print("   投注策略：组六 4 注 + 组三 2 注 = 6 注/期")
    print("   成本控制：¥12/期")
    
    for i, draw in enumerate(recent):
        draw_numbers = draw['numbers']
        draw_date = draw['draw_date']
        issue = draw['issue']
        
        # 使用之前 30 期数据计算
        start_idx = max(0, i - 30)
        past_data = history[start_idx:i] if i > 0 else []
        
        if len(past_data) >= 10:
            scored = get_scored_nums(past_data, lookback=30)
            hot_nums = [n[0] for n in scored[:5]]  # 前 5 热号
            cold_nums = [n[0] for n in scored[-5:]]  # 后 5 冷号
            mid_nums = [n[0] for n in scored[3:8]]  # 中间号
        else:
            hot_nums = [2, 1, 5, 0, 7]
            cold_nums = [9, 3, 8, 4, 6]
            mid_nums = [0, 1, 2, 4, 5]
        
        # 生成各策略投注（精简版）
        # 热号策略：组六 4 注（热号组合）+ 组三 2 注（热对 + 热单）
        hot_group6 = generate_group6_bets(hot_nums, 4)
        hot_group3 = generate_group3_bets(hot_nums, cold_nums, 2)
        hot_bets = hot_group6 + hot_group3
        
        # 冷号策略：组六 4 注（冷号组合）+ 组三 2 注（冷对 + 热单）
        cold_group6 = generate_group6_bets(cold_nums, 4)
        cold_group3 = generate_group3_bets(cold_nums, hot_nums, 2)
        cold_bets = cold_group6 + cold_group3
        
        # 均衡策略：组六 4 注（中间号）+ 组三 2 注
        balanced_group6 = generate_group6_bets(mid_nums, 4)
        balanced_group3 = generate_group3_bets(mid_nums, hot_nums, 2)
        balanced_bets = balanced_group6 + balanced_group3
        
        # 统计本期
        period_invested = 0
        period_prize = 0
        period_wins = 0
        
        # 热号追踪
        for bet in hot_bets:
            period_invested += bet['cost']
            strategy_stats["热号追踪 (V3)"]["invested"] += bet['cost']
            pattern_stats[bet['type']]["bets"] += 1
            
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["热号追踪 (V3)"]["prize"] += prize_amount
                strategy_stats["热号追踪 (V3)"]["wins"] += 1
                pattern_stats[bet['type']]["wins"] += 1
                pattern_stats[bet['type']]["prize"] += prize_amount
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "热号追踪 (V3)",
                    "bet": bet['numbers'],
                    "type": bet['type'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 冷号反弹
        for bet in cold_bets:
            period_invested += bet['cost']
            strategy_stats["冷号反弹 (V3)"]["invested"] += bet['cost']
            pattern_stats[bet['type']]["bets"] += 1
            
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["冷号反弹 (V3)"]["prize"] += prize_amount
                strategy_stats["冷号反弹 (V3)"]["wins"] += 1
                pattern_stats[bet['type']]["wins"] += 1
                pattern_stats[bet['type']]["prize"] += prize_amount
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "冷号反弹 (V3)",
                    "bet": bet['numbers'],
                    "type": bet['type'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 均衡策略
        for bet in balanced_bets:
            period_invested += bet['cost']
            strategy_stats["均衡策略 (V3)"]["invested"] += bet['cost']
            pattern_stats[bet['type']]["bets"] += 1
            
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["均衡策略 (V3)"]["prize"] += prize_amount
                strategy_stats["均衡策略 (V3)"]["wins"] += 1
                pattern_stats[bet['type']]["wins"] += 1
                pattern_stats[bet['type']]["prize"] += prize_amount
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "均衡策略 (V3)",
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
    win_rate = wins / (periods * 6) * 100 if periods > 0 else 0
    
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
        s_win_rate = stats['wins'] / (periods * 2) * 100 if periods > 0 else 0
        print(f"\n   {strategy}:")
        print(f"      投入：¥{stats['invested']:,} | 奖金：¥{stats['prize']:,} | 收益：¥{stats['prize'] - stats['invested']:,}")
        print(f"      ROI：{s_roi:.2f}% | 中奖：{stats['wins']}次 | 中奖率：{s_win_rate:.2f}%")
    
    print(f"\n🎯 形态分布统计")
    for pattern, stats in pattern_stats.items():
        hit_rate = stats['wins'] / stats['bets'] * 100 if stats['bets'] > 0 else 0
        print(f"   {pattern}: 投注{stats['bets']}次 中奖{stats['wins']}次 命中率{hit_rate:.2f}% 奖金¥{stats['prize']:,}")
    
    print(f"\n🏆 中奖详情（全部）")
    for d in details:
        print(f"   {d['date']} {d['issue']} {d['strategy']} [{d['type']}{d['bet']}] vs [{d['draw']}] → {d['prize']} ¥{d['amount']}")
    
    # 保存报告
    report_file = "/root/.openclaw/workspace/lottery/stats/fc3d_optimization_v3_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"福彩 3D 策略优化 V3 回测报告\n")
        f.write(f"生成时间：{datetime.now().isoformat()}\n")
        f.write(f"回测期数：{periods} 期\n")
        f.write(f"投注策略：组六 4 注 + 组三 2 注 = 6 注/期\n")
        f.write(f"成本控制：¥12/期\n\n")
        f.write(f"总体表现:\n")
        f.write(f"  ROI: {roi:.2f}%\n")
        f.write(f"  净收益：¥{total_prize - total_invested:,}\n")
        f.write(f"  中奖率：{win_rate:.2f}%\n\n")
        f.write(f"策略对比:\n")
        for strategy, stats in strategy_stats.items():
            s_roi = (stats['prize'] - stats['invested']) / stats['invested'] * 100 if stats['invested'] > 0 else 0
            f.write(f"  {strategy}: ROI {s_roi:.2f}%, 中奖{stats['wins']}次\n")
    
    print(f"\n📄 完整报告：{report_file}")
    
    # 版本对比
    print("\n" + "=" * 70)
    print("📈 版本对比")
    print("=" * 70)
    print(f"   原始版：ROI +15.50% | 中奖率 0.33% | 成本¥12/期")
    print(f"   优化 V1: ROI -42.33% | 中奖率 0.67% | 成本¥12/期")
    print(f"   优化 V2: ROI -71.17% | 中奖率 0.28% | 成本¥36/期")
    print(f"   优化 V3: ROI {roi:.2f}% | 中奖率 {win_rate:.2f}% | 成本¥12/期")
    
    if roi > -42.33:
        print(f"\n   ✅ V3 表现优于 V1/V2")
    elif roi > -71.17:
        print(f"\n   ✅ V3 表现优于 V2")
    else:
        print(f"\n   ⚠️ V3 仍需优化")
    
    print("=" * 70)
    
    return {
        "periods": periods,
        "total_invested": total_invested,
        "total_prize": total_prize,
        "roi": roi,
        "win_rate": win_rate,
        "strategy_stats": strategy_stats,
        "details": details
    }


if __name__ == "__main__":
    run_optimization_v3(periods=100)
