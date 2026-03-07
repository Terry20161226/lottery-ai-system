#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开奖后核对中奖并更新策略统计
- 获取最新开奖结果
- 核对各策略推荐号码
- 更新中奖统计和策略权重
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from strategy_tracker import StrategyTracker
from datetime import datetime


def check_and_update(lottery_type: str, lottery_name: str):
    """核对开奖结果并更新统计"""
    storage = LotteryStorage()
    tracker = StrategyTracker()
    
    # 获取最新期号
    last_issue = storage.get_last_issue(lottery_type)
    if not last_issue:
        print(f"⚠️ {lottery_name} 暂无历史数据")
        return
    
    # 获取开奖号码
    history = storage.get_history(lottery_type, 1)
    if not history:
        print(f"⚠️ {lottery_name} 获取开奖结果失败")
        return
    
    latest = history[0]
    issue = latest.get('issue')
    numbers = latest.get('numbers', {})
    
    print(f"🔍 核对 {lottery_name} 第 {issue} 期...")
    print(f"   开奖号码：{numbers}")
    
    # 检查是否有推荐记录
    stats = tracker.get_summary(lottery_type)
    if stats.get('total_periods', 0) == 0:
        print(f"ℹ️  {lottery_name} 还没有推荐记录，跳过核对")
        return
    
    # 核对中奖
    result = tracker.check_prize(lottery_type, issue, numbers)
    
    if 'error' in result:
        print(f"⚠️ {result['error']}")
        return
    
    # 统计中奖情况
    total_prize = 0
    total_hits = 0
    
    print(f"\n📊 各策略中奖情况：")
    for strategy_name, hits in result.items():
        strategy_hits = sum(hits.get(f"level_{i}", 0) for i in range(1, 7))
        prize = hits.get('total_prize', 0)
        total_prize += prize
        total_hits += strategy_hits
        
        if strategy_hits > 0:
            print(f"   ✅ {strategy_name}: 中奖 {strategy_hits} 注，奖金 ¥{prize:,}")
        else:
            print(f"   ❌ {strategy_name}: 未中奖")
    
    # 更新统计
    updated_stats = tracker.get_summary(lottery_type)
    best = updated_stats.get('best_strategy', {})
    
    print(f"\n📈 累计统计：")
    print(f"   总期数：{updated_stats.get('total_periods', 0)} 期")
    print(f"   总中奖：{total_hits} 注")
    print(f"   总奖金：¥{total_prize:,}")
    
    if best:
        print(f"\n⭐ 最佳策略：{best.get('name_cn', '均衡策略')}")
        print(f"   累计奖金：¥{best.get('total_prize', 0):,}")
        print(f"   中奖率：{best.get('hit_rate', 0):.2f}%")
    
    print(f"\n✅ {lottery_name} 核对完成！")


def main():
    """主函数"""
    print("=" * 50)
    print("开奖核对与策略更新")
    print("=" * 50)
    print()
    
    # 双色球（周二、四、日开奖）
    check_and_update('ssq', '双色球')
    print()
    
    # 大乐透（周一、三、六开奖）
    check_and_update('dlt', '大乐透')
    print()
    
    print("=" * 50)
    print("全部完成！")
    print("=" * 50)


if __name__ == "__main__":
    main()
