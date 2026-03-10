#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 策略回测系统
基于历史数据回测各策略的表现
"""

import json
from collections import Counter
from datetime import datetime

DATA_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_history.json"
REPORT_FILE = "/root/.openclaw/workspace/lottery/stats/fc3d_backtest_report.txt"

# 福彩 3D 奖级规则
FC3D_PRIZES = {
    "直选": {"amount": 1040, "condition": "exact"},
    "组三": {"amount": 346, "condition": "group3"},
    "组六": {"amount": 173, "condition": "group6"},
}


def load_history():
    """加载福彩 3D 历史数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])


def analyze_pattern(numbers):
    """分析号码形态"""
    counter = Counter(numbers)
    if len(counter) == 1:
        return "豹子"
    elif len(counter) == 2:
        return "组三"
    else:
        return "组六"


def generate_hot_strategy(hot_nums, count=1):
    """热号追踪策略"""
    from itertools import combinations_with_replacement
    bets = []
    for combo in combinations_with_replacement(hot_nums, 3):
        if len(set(combo)) >= 2:  # 排除豹子
            bets.append(list(combo))
    return bets[:count]


def generate_cold_strategy(cold_nums, count=1):
    """冷号反弹策略"""
    from itertools import combinations_with_replacement
    bets = []
    for combo in combinations_with_replacement(cold_nums, 3):
        if len(set(combo)) >= 2:
            bets.append(list(combo))
    return bets[:count]


def generate_balanced_strategy(all_nums, count=1):
    """均衡策略"""
    import random
    bets = []
    for _ in range(count):
        bet = random.sample(all_nums, 3)
        bets.append(bet)
    return bets


def check_prize(bet, draw_numbers):
    """检查中奖"""
    bet_pattern = analyze_pattern(bet)
    draw_pattern = analyze_pattern(draw_numbers)
    
    # 直选：号码和顺序完全匹配
    if bet == draw_numbers:
        return "直选", 1040
    
    # 组选：号码匹配但顺序不限
    if Counter(bet) == Counter(draw_numbers):
        if draw_pattern == "组三":
            return "组三", 346
        elif draw_pattern == "组六":
            return "组六", 173
    
    return None, 0


def run_backtest(periods=100, bet_per_period=10):
    """
    运行回测
    
    Args:
        periods: 回测期数
        bet_per_period: 每期投注金额
    """
    print("=" * 70)
    print("福彩 3D 策略回测")
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
        "热号追踪": {"invested": 0, "prize": 0, "wins": 0},
        "冷号反弹": {"invested": 0, "prize": 0, "wins": 0},
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
            # 统计热号冷号
            all_nums = []
            for d in past_data:
                all_nums.extend(d['numbers'])
            counter = Counter(all_nums)
            hot_nums = [n for n, c in counter.most_common(5)]
            cold_nums = [n for n, c in counter.most_common()[:-6:-1]]
        else:
            hot_nums = [2, 1, 5, 0, 7]
            cold_nums = [9, 3, 8, 4, 6]
        
        # 生成各策略投注
        hot_bets = generate_hot_strategy(hot_nums, 2)
        cold_bets = generate_cold_strategy(cold_nums, 2)
        balanced_bets = generate_balanced_strategy(list(range(10)), 2)
        
        # 统计本期投注
        period_invested = 0
        period_prize = 0
        period_wins = 0
        
        # 热号追踪
        for bet in hot_bets:
            period_invested += 2
            strategy_stats["热号追踪"]["invested"] += 2
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["热号追踪"]["prize"] += prize_amount
                strategy_stats["热号追踪"]["wins"] += 1
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "热号追踪",
                    "bet": bet,
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 冷号反弹
        for bet in cold_bets:
            period_invested += 2
            strategy_stats["冷号反弹"]["invested"] += 2
            prize_name, prize_amount = check_prize(bet, draw_numbers)
            if prize_amount > 0:
                period_prize += prize_amount
                period_wins += 1
                strategy_stats["冷号反弹"]["prize"] += prize_amount
                strategy_stats["冷号反弹"]["wins"] += 1
                details.append({
                    "issue": issue,
                    "date": draw_date,
                    "strategy": "冷号反弹",
                    "bet": bet,
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        # 均衡策略
        for bet in balanced_bets:
            period_invested += 2
            strategy_stats["均衡策略"]["invested"] += 2
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
                    "bet": bet,
                    "draw": draw_numbers,
                    "prize": prize_name,
                    "amount": prize_amount
                })
        
        total_invested += period_invested
        total_prize += period_prize
        wins += period_wins
        capital = initial_capital - total_invested + total_prize
        
        if (i + 1) % 20 == 0:
            print(f"   第{i+1}期：投入¥{period_invested} 中奖¥{period_prize} 资金¥{capital}")
    
    # 计算指标
    roi = (total_prize - total_invested) / total_invested * 100 if total_invested > 0 else 0
    win_rate = wins / (periods * 6) * 100 if periods > 0 else 0  # 6 注/期
    
    # 生成报告
    print("\n" + "=" * 70)
    print("📊 回测结果")
    print("=" * 70)
    
    report = []
    report.append("=" * 70)
    report.append("福彩 3D 策略回测报告")
    report.append("=" * 70)
    report.append(f"生成时间：{datetime.now().isoformat()}")
    report.append(f"回测期数：{periods} 期")
    report.append(f"时间范围：{recent[0]['draw_date']} 至 {recent[-1]['draw_date']}")
    report.append("")
    report.append("💰 总体表现")
    report.append("-" * 70)
    report.append(f"初始资金：¥{initial_capital:,}")
    report.append(f"总投入：¥{total_invested:,}")
    report.append(f"总奖金：¥{total_prize:,}")
    report.append(f"净收益：¥{total_prize - total_invested:,}")
    report.append(f"ROI：{roi:.2f}%")
    report.append(f"中奖次数：{wins} 次")
    report.append(f"中奖率：{win_rate:.2f}%")
    report.append(f"最终资金：¥{capital:,}")
    report.append("")
    report.append("📊 策略对比")
    report.append("-" * 70)
    
    for strategy, stats in strategy_stats.items():
        s_roi = (stats['prize'] - stats['invested']) / stats['invested'] * 100 if stats['invested'] > 0 else 0
        s_win_rate = stats['wins'] / (periods * 2) * 100 if periods > 0 else 0
        report.append(f"\n{strategy}:")
        report.append(f"  投入：¥{stats['invested']:,}")
        report.append(f"  奖金：¥{stats['prize']:,}")
        report.append(f"  收益：¥{stats['prize'] - stats['invested']:,}")
        report.append(f"  ROI：{s_roi:.2f}%")
        report.append(f"  中奖：{stats['wins']} 次")
        report.append(f"  中奖率：{s_win_rate:.2f}%")
    
    report.append("")
    report.append("🏆 中奖详情（前 20 次）")
    report.append("-" * 70)
    for d in details[:20]:
        report.append(f"{d['date']} {d['issue']} {d['strategy']} [{d['bet']}] vs [{d['draw']}] → {d['prize']} ¥{d['amount']}")
    
    report.append("")
    report.append("=" * 70)
    report.append("💡 优化建议")
    report.append("=" * 70)
    
    # 分析优化建议
    best_strategy = max(strategy_stats.items(), key=lambda x: x[1]['prize'] - x[1]['invested'])
    worst_strategy = min(strategy_stats.items(), key=lambda x: x[1]['prize'] - x[1]['invested'])
    
    report.append(f"\n1. 最佳策略：{best_strategy[0]} (收益¥{best_strategy[1]['prize'] - best_strategy[1]['invested']:,})")
    report.append(f"2. 待优化策略：{worst_strategy[0]} (收益¥{worst_strategy[1]['prize'] - worst_strategy[1]['invested']:,})")
    
    if roi < 0:
        report.append("\n3. ⚠️ 整体亏损，建议：")
        report.append("   - 减少投注注数，控制成本")
        report.append("   - 聚焦表现最好的策略")
        report.append("   - 考虑结合形态分析（组三/组六概率）")
    else:
        report.append("\n3. ✅ 整体盈利，可以：")
        report.append("   - 保持当前策略")
        report.append("   - 适当增加投入")
    
    report.append("\n4. 形态分析优化:")
    report.append("   - 组三概率约 27%，可适当增加组三投注")
    report.append("   - 组六概率约 72%，主要投注方向")
    report.append("   - 豹子概率约 1%，不建议专门投注")
    
    report.append("\n5. 遗漏值优化:")
    report.append("   - 关注遗漏 7 期以上的号码")
    report.append("   - 结合热号冷号动态调整")
    
    report.append("")
    report.append("=" * 70)
    
    # 保存报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    # 输出报告
    print('\n'.join(report[:30]))
    print("...")
    print(f"\n📄 完整报告：{REPORT_FILE}")
    
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
    run_backtest(periods=100)
