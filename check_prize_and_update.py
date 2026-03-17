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
from strategy_tracker import load_strategy_stats, save_strategy_stats, update_stats
from datetime import datetime


def check_and_update(lottery_type: str, lottery_name: str):
    """核对开奖结果并更新统计"""
    storage = LotteryStorage()
    
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
    stats = load_strategy_stats()
    if stats.get('total_periods', 0) == 0:
        print(f"ℹ️  {lottery_name} 还没有推荐记录，跳过核对")
        return
    
    # 更新统计数据
    print(f"\n📊 更新策略统计...")
    updated_stats = update_stats()
    
    print(f"\n📈 累计统计：")
    print(f"   总期数：{updated_stats.get('total_periods', 0)} 期")
    print(f"   总投入：¥{updated_stats.get('total_invested', 0):,}")
    print(f"   总奖金：¥{updated_stats.get('total_prize', 0):,}")
    print(f"   净收益：¥{updated_stats.get('total_prize', 0) - updated_stats.get('total_invested', 0):,}")
    
    # 当日表现
    if updated_stats.get('daily_records'):
        today_record = updated_stats['daily_records'][-1]
        print(f"\n📅 今日表现：")
        print(f"   投入：¥{today_record.get('invested', 0)}")
        print(f"   奖金：¥{today_record.get('prize', 0)}")
        print(f"   收益：¥{today_record.get('net', 0)}")
        print(f"   ROI: {today_record.get('roi', 0):.2f}%")
    
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
