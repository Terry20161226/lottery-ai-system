#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大乐透开奖数据更新 + 策略核对
替代原来的 fetch_and_push.py
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from check_prize import check_lottery_prize, get_latest_draw, get_latest_recommendations

def update_dlt_data():
    """更新大乐透数据"""
    storage = LotteryStorage()
    
    # 获取当前最新期号
    history = storage.get_history('dlt', 1)
    if not history:
        print("⚠️ 大乐透暂无数据")
        return False
    
    current_issue = history[0].get('issue', '')
    print(f"✅ 大乐透已是最新期号：{current_issue}")
    return True

def check_dlt_prize():
    """核对大乐透中奖"""
    try:
        draw_data = get_latest_draw('dlt')
        recommendations = get_latest_recommendations('dlt')
        if draw_data:
            result, total_amount = check_lottery_prize('dlt', draw_data, recommendations)
            if result:
                print(f"✅ 中奖核对完成")
                print(f"💰 中奖注数：{len(result)} 注")
                print(f"💰 总奖金：¥{total_amount:,}")
                for r in result:
                    print(f"   第{r['note']}注：{r['prize_name']} - ¥{r['prize_amount']:,}")
            else:
                print(f"ℹ️ 未中奖")
            return True
    except Exception as e:
        print(f"⚠️ 中奖核对失败：{e}")
    return False

def main():
    print("🕐 大乐透开奖数据更新 + 策略核对")
    print("=" * 50)
    
    # 1. 更新数据
    print("\n【开奖更新】")
    update_dlt_data()
    
    # 2. 核对中奖
    print("\n【策略核对】")
    check_dlt_prize()
    
    print("\n" + "=" * 50)
    print("✅ 操作完成")

if __name__ == "__main__":
    main()
