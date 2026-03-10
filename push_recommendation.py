#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票推荐号码推送脚本
每天 22:00 执行，推送下一期的推荐号码
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


def get_next_draw_date(lottery_type: str) -> str:
    """获取下一期开奖日期"""
    today = datetime.now()
    
    if lottery_type == 'ssq':
        # 双色球：二、四、日开奖（周二、周四、周日）
        draw_days = [1, 3, 6]  # 周一=0
        next_draw = None
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                next_draw = date
                break
    elif lottery_type == 'dlt':
        # 大乐透：一、三、六开奖（周一、周三、周六）
        draw_days = [0, 2, 5]
        next_draw = None
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                next_draw = date
                break
    
    if next_draw:
        return next_draw.strftime("%Y-%m-%d")
    return today.strftime("%Y-%m-%d")


def generate_push_message(lottery_type: str, lottery_name: str, recommendations: list, next_issue: str, draw_date: str) -> str:
    """生成推送消息"""
    lines = [
        f"🎰 {lottery_name} 推荐号码",
        f"📅 开奖日期：{draw_date}",
        f"📝 期号：{next_issue}",
        "",
        f"💡 推荐策略：均衡（热号 + 冷号组合）",
        ""
    ]
    
    for i, rec in enumerate(recommendations, 1):
        if lottery_type == 'ssq':
            red = ' '.join(f"{n:02d}" for n in rec['red'])
            blue = ' '.join(f"{n:02d}" for n in rec['blue'])
            lines.append(f"第{i}注：🔴 {red} + 🔵 {blue}")
        elif lottery_type == 'dlt':
            front = ' '.join(f"{n:02d}" for n in rec['front'])
            back = ' '.join(f"{n:02d}" for n in rec['back'])
            lines.append(f"第{i}注：🔴 {front} + 🔵 {back}")
    
    lines.extend([
        "",
        "⚠️ 温馨提示：彩票有风险，购买需谨慎",
        "祝你好运！🍀"
    ])
    
    return "\n".join(lines)


def main():
    storage = LotteryStorage()
    
    # 获取配置
    settings = storage.get_settings()
    recommend_count = settings.get('recommend_count', 5)
    strategy = settings.get('strategy', 'balanced')
    
    results = []
    
    # 双色球推荐
    ssq_next_draw = get_next_draw_date('ssq')
    ssq_last_issue = storage.get_last_issue('ssq')
    ssq_next_issue = str(int(ssq_last_issue) + 1) if ssq_last_issue else f"{datetime.now().year}001"
    
    ssq_recommendations = storage.generate_recommendation('ssq', ssq_next_issue, strategy)
    ssq_message = generate_push_message('ssq', '双色球', ssq_recommendations, ssq_next_issue, ssq_next_draw)
    
    # 保存推荐
    ssq_rec_id = storage.save_recommendation('ssq', ssq_next_issue, ssq_recommendations, strategy)
    
    results.append({
        'type': 'ssq',
        'message': ssq_message,
        'rec_id': ssq_rec_id
    })
    
    # 大乐透推荐（只在开奖日前一天推送）
    today = datetime.now()
    dlt_next_draw = get_next_draw_date('dlt')
    dlt_last_issue = storage.get_last_issue('dlt')
    dlt_next_issue = str(int(dlt_last_issue) + 1) if dlt_last_issue else f"{datetime.now().year}001"
    
    dlt_recommendations = storage.generate_recommendation('dlt', dlt_next_issue, strategy)
    dlt_message = generate_push_message('dlt', '大乐透', dlt_recommendations, dlt_next_issue, dlt_next_draw)
    
    # 保存推荐
    dlt_rec_id = storage.save_recommendation('dlt', dlt_next_issue, dlt_recommendations, strategy)
    
    results.append({
        'type': 'dlt',
        'message': dlt_message,
        'rec_id': dlt_rec_id
    })
    
    # 输出消息（供 cron job 调用）
    for result in results:
        print(f"\n========== {result['type'].upper()} ==========")
        print(result['message'])
        print(f"推荐记录 ID: {result['rec_id']}")
    
    return results


if __name__ == "__main__":
    main()
