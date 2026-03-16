#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成 7 种策略推荐号码并保存
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from lottery_strategies import LotteryStrategies
# from strategy_tracker import StrategyTracker  # 已移除
from datetime import datetime

STRATEGY_NAMES = {
    'balanced': '均衡策略',
    'hot_tracking': '热号追踪',
    'cold_rebound': '冷号反弹',
    'odd_even': '奇偶均衡',
    'zone_distribution': '区间分布',
    'consecutive': '连号追踪',
    'warm_balance': '温号搭配',
}


def get_next_draw_date(lottery_type: str) -> tuple:
    """获取下一期开奖日期和期号"""
    from datetime import timedelta
    today = datetime.now()
    storage = LotteryStorage()
    last_issue = storage.get_last_issue(lottery_type)
    
    if lottery_type == 'ssq':
        draw_days = [1, 3, 6]  # 周二、四、日
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                next_issue = str(int(last_issue) + 1) if last_issue else f"{date.year}001"
                return date.strftime("%Y-%m-%d"), next_issue
    elif lottery_type == 'dlt':
        draw_days = [0, 2, 5]  # 周一、三、六
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                next_issue = str(int(last_issue) + 1) if last_issue else f"{date.year}001"
                return date.strftime("%Y-%m-%d"), next_issue
    
    return today.strftime("%Y-%m-%d"), last_issue or f"{datetime.now().year}001"


def generate_all_strategies(lottery_type: str):
    """生成所有策略推荐"""
    storage = LotteryStorage()
    strategies = LotteryStrategies(storage)
    tracker = StrategyTracker()
    
    # 获取下期信息
    draw_date, next_issue = get_next_draw_date(lottery_type)
    
    print(f"\n{'='*50}")
    print(f"{('双色球' if lottery_type == 'ssq' else '大乐透')} 7 种策略推荐")
    print(f"期号：{next_issue} | 开奖日期：{draw_date}")
    print(f"{'='*50}\n")
    
    # 生成所有策略
    all_strategies = strategies.get_all_strategies(lottery_type)
    strategies_result = {}
    
    for strategy_name, strategy_func in all_strategies.items():
        recommendations = strategy_func()
        strategies_result[strategy_name] = recommendations
        
        # 打印结果
        cn_name = STRATEGY_NAMES.get(strategy_name, strategy_name)
        print(f"【{cn_name}】")
        
        for i, rec in enumerate(recommendations, 1):
            if lottery_type == 'ssq':
                red = ' '.join(f"{n:02d}" for n in rec['red'])
                blue = ' '.join(f"{n:02d}" for n in rec['blue'])
                print(f"  {i}. 🔴 {red} + 🔵 {blue}")
            else:
                front = ' '.join(f"{n:02d}" for n in rec['front'])
                back = ' '.join(f"{n:02d}" for n in rec['back'])
                print(f"  {i}. 🔴 {front} + 🔵 {back}")
        print()
    
    # 保存推荐结果
    tracker.save_recommendations(lottery_type, next_issue, strategies_result)
    print(f"✅ 推荐结果已保存")
    
    # 获取最佳策略
    best = tracker.get_best_strategy(lottery_type)
    if best:
        print(f"⭐ 当前最佳策略：{best.get('name_cn', '均衡策略')} (累计奖金：¥{best.get('total_prize', 0):,})")
    else:
        print(f"⭐ 当前最佳策略：均衡策略 (新策略，等待数据积累)")
    
    return strategies_result, next_issue, draw_date, best


def main():
    """主函数"""
    print("=" * 50)
    print("彩票 7 策略推荐生成")
    print("=" * 50)
    
    # 双色球
    ssq_result, ssq_issue, ssq_date, ssq_best = generate_all_strategies('ssq')
    
    # 大乐透
    dlt_result, dlt_issue, dlt_date, dlt_best = generate_all_strategies('dlt')
    
    print("\n" + "=" * 50)
    print("生成完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
