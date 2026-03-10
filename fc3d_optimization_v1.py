#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 策略优化 V1 - 冷号策略重构
结合遗漏值动态选择冷号
"""

import json
from collections import Counter
from datetime import datetime

DATA_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_history.json"


def load_history():
    """加载福彩 3D 历史数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])


def calculate_omission(history, num, max_lookback=50):
    """
    计算某个号码的遗漏期数（连续多少期未出现）
    
    Args:
        history: 历史数据（从新到旧排序）
        num: 号码（0-9）
        max_lookback: 最大回溯期数
    
    Returns:
        遗漏期数
    """
    omission = 0
    for draw in history[:max_lookback]:
        if num in draw['numbers']:
            break
        omission += 1
    return omission


def calculate_frequency(history, num, max_lookback=50):
    """
    计算某个号码在近期出现的频率
    
    Returns:
        出现次数
    """
    count = 0
    for draw in history[:max_lookback]:
        if num in draw['numbers']:
            count += 1
    return count


def get_optimized_cold_nums(history, top_n=5, lookback=50):
    """
    优化后的冷号选择 - 结合遗漏值和频率
    
    评分公式：score = 遗漏值 * 0.6 + (max_lookback - 频率) * 0.4
    
    Args:
        history: 历史数据
        top_n: 返回前 N 个冷号
        lookback: 回溯期数
    
    Returns:
        冷号列表
    """
    cold_candidates = []
    
    for num in range(10):
        omission = calculate_omission(history, num, lookback)
        frequency = calculate_frequency(history, num, lookback)
        
        # 综合评分：遗漏值权重 60%，频率权重 40%
        score = omission * 0.6 + (lookback - frequency) * 0.4
        cold_candidates.append((num, score, omission, frequency))
    
    # 按评分降序排序
    cold_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # 返回前 N 个冷号
    return [(n, s, o, f) for n, s, o, f in cold_candidates[:top_n]]


def get_optimized_hot_nums(history, top_n=5, lookback=50):
    """
    优化后的热号选择 - 结合近期频率和遗漏值
    
    评分公式：score = 频率 * 0.7 - 遗漏值 * 0.3
    
    Returns:
        热号列表
    """
    hot_candidates = []
    
    for num in range(10):
        omission = calculate_omission(history, num, lookback)
        frequency = calculate_frequency(history, num, lookback)
        
        # 综合评分：频率权重 70%，遗漏值负权重 30%
        score = frequency * 0.7 - omission * 0.3
        hot_candidates.append((num, score, omission, frequency))
    
    # 按评分降序排序
    hot_candidates.sort(key=lambda x: x[1], reverse=True)
    
    return [(n, s, o, f) for n, s, o, f in hot_candidates[:top_n]]


def generate_cold_bets_optimized(cold_nums, count=3):
    """
    基于优化冷号生成投注
    
    Args:
        cold_nums: 冷号列表 [(num, score, omission, frequency), ...]
        count: 生成注数
    
    Returns:
        投注列表
    """
    from itertools import combinations
    
    bets = []
    nums = [n[0] for n in cold_nums]  # 提取号码
    
    # 组六投注（3 个不同号）
    for combo in combinations(nums, 3):
        bets.append({'type': '组六', 'numbers': list(combo), 'cost': 2})
        if len(bets) >= count:
            break
    
    # 如果还需要更多，添加组三
    if len(bets) < count:
        for num in nums[:3]:
            for other in nums[3:] if len(nums) > 3 else nums:
                if num != other:
                    bets.append({'type': '组三', 'numbers': [num, num, other], 'cost': 2})
                    if len(bets) >= count:
                        break
            if len(bets) >= count:
                break
    
    return bets


def generate_hot_bets_optimized(hot_nums, count=3):
    """
    基于优化热号生成投注
    """
    from itertools import combinations
    
    bets = []
    nums = [n[0] for n in hot_nums]
    
    # 组六投注
    for combo in combinations(nums, 3):
        bets.append({'type': '组六', 'numbers': list(combo), 'cost': 2})
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
    bet_pattern = analyze_pattern(bet_nums)
    draw_pattern = analyze_pattern(draw_numbers)
    
    # 直选：号码和顺序完全匹配
    if bet_nums == draw_numbers:
        return "直选", 1040
    
    # 组选：号码匹配但顺序不限
    if Counter(bet_nums) == Counter(draw_numbers):
        if draw_pattern == "组三":
            return "组三", 346
        elif draw_pattern == "组六":
            return "组六", 173
    
    return None, 0


def run_optimized_backtest(periods=100):
    """
    运行优化后回测
    """
    print("=" * 70)
    print("福彩 3D 策略优化 V1 - 冷号策略重构回测")
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
        "热号追踪 (优化)": {"invested": 0, "prize": 0, "wins": 0},
        "冷号反弹 (优化)": {"invested": 0, "prize": 0, "wins": 0},
        "均衡策略": {"invested": 0, "prize": 0, "wins": 0},
    }
    
    print("\n📊 开始回测...")
    
    for i, draw in enumerate(recent):
        draw_numbers = draw['numbers']
        draw_date = draw['draw_date']
        issue = draw['issue']
        
        # 使用之前 50 期数据计算热号冷号
        start_idx = max(0, i - 50)
        past_data = history[start_idx:i] if i > 0 else []
        
        if len(past_data) >= 10:
            # 优化后的热号冷号计算
            hot_nums = get_optimized_hot_nums(past_data, top_n=5, lookback=50)
            cold_nums = get_optimized_cold_nums(past_data, top_n=5, lookback=50)
            
            print(f"\n   第{i+1}期 ({draw_date})")
            print(f"      热号：{[n[0] for n in hot_nums]} (遗漏：{[n[2] for n in hot_nums]})")
            print(f"      冷号：{[n[0] for n in cold_nums]} (遗漏：{[n[2] for n in cold_nums]})")
        else:
            hot_nums = [(2, 0, 0, 10), (1, 0, 0, 10), (5, 0, 0, 10), (0, 0, 0, 10), (7, 0, 0, 10)]
            cold_nums = [(9, 0, 0, 5), (3, 0, 0, 5), (8, 0, 0, 5), (4, 0, 0, 5), (6, 0, 0, 5)]
        
        # 生成各策略投注
        hot_bets = generate_hot_bets_optimized(hot_nums, 2)
        cold_bets = generate_cold_bets_optimized(cold_nums, 2)
        
        from itertools import combinations
        balanced_bets = []
        for combo in combinations(range(10), 3):
            balanced_bets.append({'type': '组六', 'numbers': list(combo), 'cost': 2})
            if len(balanced_bets) >= 2:
                break
        
        # 统计本期投注
        period_invested = 0
        period_prize = 0
        period_wins = 0
        
        # 热号追踪
        for bet in hot_bets:
            period_invested += bet['cost']
            strategy_stats["热号追踪 (优化)"]["invested"] += bet['cost']
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["热号追踪 (优化)"]["prize"] += prize_amount
                strategy_stats["热号追踪 (优化)"]["wins"] += 1
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "热号追踪 (优化)",
                    "bet": bet['numbers'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 冷号反弹
        for bet in cold_bets:
            period_invested += bet['cost']
            strategy_stats["冷号反弹 (优化)"]["invested"] += bet['cost']
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["冷号反弹 (优化)"]["prize"] += prize_amount
                strategy_stats["冷号反弹 (优化)"]["wins"] += 1
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "冷号反弹 (优化)",
                    "bet": bet['numbers'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 均衡策略
        for bet in balanced_bets:
            period_invested += bet['cost']
            strategy_stats["均衡策略"]["invested"] += bet['cost']
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["均衡策略"]["prize"] += prize_amount
                strategy_stats["均衡策略"]["wins"] += 1
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "均衡策略",
                    "bet": bet['numbers'],
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        total_invested += period_invested
        total_prize += period_prize
        wins += period_wins
        capital = initial_capital - total_invested + total_prize
        
        if (i + 1) % 20 == 0:
            print(f"\n   [进度] 第{i+1}期：投入¥{period_invested} 中奖¥{period_prize} 资金¥{capital}")
    
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
    
    print(f"\n🏆 中奖详情（前 10 次）")
    for d in details[:10]:
        print(f"   {d['date']} {d['issue']} {d['strategy']} [{d['bet']}] vs [{d['draw']}] → {d['prize']} ¥{d['amount']}")
    
    # 保存报告
    report_file = "/root/.openclaw/workspace/lottery/stats/fc3d_optimization_v1_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"福彩 3D 策略优化 V1 回测报告\n")
        f.write(f"生成时间：{datetime.now().isoformat()}\n")
        f.write(f"回测期数：{periods} 期\n\n")
        f.write(f"总体表现:\n")
        f.write(f"  ROI: {roi:.2f}%\n")
        f.write(f"  净收益：¥{total_prize - total_invested:,}\n")
        f.write(f"  中奖率：{win_rate:.2f}%\n\n")
        f.write(f"策略对比:\n")
        for strategy, stats in strategy_stats.items():
            s_roi = (stats['prize'] - stats['invested']) / stats['invested'] * 100 if stats['invested'] > 0 else 0
            f.write(f"  {strategy}: ROI {s_roi:.2f}%, 中奖{stats['wins']}次\n")
    
    print(f"\n📄 完整报告：{report_file}")
    print("\n" + "=" * 70)
    
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
    run_optimized_backtest(periods=100)
