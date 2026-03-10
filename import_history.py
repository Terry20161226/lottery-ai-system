#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票历史数据导入脚本
导入最近 1000 期开奖数据
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
import random
from datetime import datetime, timedelta

def generate_mock_history(lottery_type: str, count: int = 1000):
    """
    生成模拟历史数据（实际使用时从 API 获取）
    
    Args:
        lottery_type: 'ssq' 或 'dlt'
        count: 生成期数
    """
    records = []
    today = datetime.now()
    
    if lottery_type == 'ssq':
        # 双色球：二、四、日开奖
        draw_days = [1, 3, 6]  # 周一=0, 周二=1, 周四=3, 周日=6
        for i in range(count):
            # 计算开奖日期
            days_ago = 0
            while True:
                date = today - timedelta(days=days_ago)
                if date.weekday() in draw_days:
                    break
                days_ago += 1
            
            # 生成期号（年份 + 序号）
            issue = f"{date.year}{str(i+1).zfill(3)}"
            
            # 生成号码
            red_balls = sorted(random.sample(range(1, 34), 6))
            blue_balls = [random.randint(1, 16)]
            
            records.append({
                "issue": issue,
                "draw_date": date.strftime("%Y-%m-%d"),
                "numbers": {"red": red_balls, "blue": blue_balls},
                "pool_amount": random.randint(500000000, 1000000000),
                "sales_amount": random.randint(100000000, 300000000)
            })
            
            today = date - timedelta(days=1)
    
    elif lottery_type == 'dlt':
        # 大乐透：一、三、六开奖
        draw_days = [0, 2, 5]  # 周一=0, 周三=2, 周六=5
        for i in range(count):
            # 计算开奖日期
            days_ago = 0
            while True:
                date = today - timedelta(days=days_ago)
                if date.weekday() in draw_days:
                    break
                days_ago += 1
            
            # 生成期号
            issue = f"{date.year}{str(i+1).zfill(3)}"
            
            # 生成号码
            front_balls = sorted(random.sample(range(1, 36), 5))
            back_balls = sorted(random.sample(range(1, 13), 2))
            
            records.append({
                "issue": issue,
                "draw_date": date.strftime("%Y-%m-%d"),
                "numbers": {"front": front_balls, "back": back_balls},
                "pool_amount": random.randint(30000000, 100000000),
                "sales_amount": random.randint(50000000, 150000000)
            })
            
            today = date - timedelta(days=1)
    
    return records


def import_history_data(storage: LotteryStorage, count: int = 1000):
    """
    导入历史数据
    
    Args:
        storage: LotteryStorage 实例
        count: 导入期数
    """
    print(f"开始导入历史数据，目标：{count} 期")
    
    # 导入双色球
    print("\n========== 导入双色球数据 ==========")
    ssq_records = generate_mock_history('ssq', count)
    ssq_count = 0
    for record in ssq_records:
        result = storage.save_lottery_result(
            lottery_type='ssq',
            issue=record['issue'],
            numbers=record['numbers'],
            draw_date=record['draw_date'],
            pool_amount=record['pool_amount'],
            sales_amount=record['sales_amount']
        )
        if result:
            ssq_count += 1
    
    print(f"双色球导入完成：{ssq_count} 期")
    
    # 导入大乐透
    print("\n========== 导入大乐透数据 ==========")
    dlt_records = generate_mock_history('dlt', count)
    dlt_count = 0
    for record in dlt_records:
        result = storage.save_lottery_result(
            lottery_type='dlt',
            issue=record['issue'],
            numbers=record['numbers'],
            draw_date=record['draw_date'],
            pool_amount=record['pool_amount'],
            sales_amount=record['sales_amount']
        )
        if result:
            dlt_count += 1
    
    print(f"大乐透导入完成：{dlt_count} 期")
    
    # 显示统计
    print("\n========== 导入统计 ==========")
    ssq_stats = storage.get_statistics('ssq')
    dlt_stats = storage.get_statistics('dlt')
    
    print(f"双色球总记录：{ssq_stats['total_records']} 期")
    print(f"双色球最新期号：{ssq_stats['last_issue']}")
    print(f"大乐透总记录：{dlt_stats['total_records']} 期")
    print(f"大乐透最新期号：{dlt_stats['last_issue']}")
    
    return ssq_count, dlt_count


if __name__ == "__main__":
    storage = LotteryStorage()
    import_history_data(storage, count=1000)
