#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票推荐号码推送脚本 - 钉钉版本
通过 message tool 推送推荐号码到钉钉
"""

import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


def get_next_draw_date(lottery_type: str) -> str:
    """获取下一期开奖日期"""
    today = datetime.now()
    
    if lottery_type == 'ssq':
        # 双色球：二、四、日开奖（周二、周四、周日）
        draw_days = [1, 3, 6]
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                return date.strftime("%Y-%m-%d")
    elif lottery_type == 'dlt':
        # 大乐透：一、三、六开奖（周一、周三、周六）
        draw_days = [0, 2, 5]
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                return date.strftime("%Y-%m-%d")
    
    return today.strftime("%Y-%m-%d")


def main():
    storage = LotteryStorage()
    settings = storage.get_settings()
    strategy = settings.get('strategy', 'balanced')
    
    messages = []
    
    # 双色球
    ssq_next_draw = get_next_draw_date('ssq')
    ssq_last_issue = storage.get_last_issue('ssq')
    ssq_next_issue = str(int(ssq_last_issue) + 1) if ssq_last_issue else f"{datetime.now().year}001"
    ssq_recs = storage.generate_recommendation('ssq', ssq_next_issue, strategy)
    storage.save_recommendation('ssq', ssq_next_issue, ssq_recs, strategy)
    
    ssq_lines = [
        f"🎰 双色球推荐",
        f"📅 开奖：{ssq_next_draw} | 期号：{ssq_next_issue}",
        f"💡 策略：均衡（热号 + 冷号）",
        ""
    ]
    for i, rec in enumerate(ssq_recs, 1):
        red = ' '.join(f"{n:02d}" for n in rec['red'])
        blue = ' '.join(f"{n:02d}" for n in rec['blue'])
        ssq_lines.append(f"{i}. 🔴 {red} + 🔵 {blue}")
    
    messages.append("\n".join(ssq_lines))
    
    # 大乐透
    dlt_next_draw = get_next_draw_date('dlt')
    dlt_last_issue = storage.get_last_issue('dlt')
    dlt_next_issue = str(int(dlt_last_issue) + 1) if dlt_last_issue else f"{datetime.now().year}001"
    dlt_recs = storage.generate_recommendation('dlt', dlt_next_issue, strategy)
    storage.save_recommendation('dlt', dlt_next_issue, dlt_recs, strategy)
    
    dlt_lines = [
        "",
        f"🎰 大乐透推荐",
        f"📅 开奖：{dlt_next_draw} | 期号：{dlt_next_issue}",
        f"💡 策略：均衡（热号 + 冷号）",
        ""
    ]
    for i, rec in enumerate(dlt_recs, 1):
        front = ' '.join(f"{n:02d}" for n in rec['front'])
        back = ' '.join(f"{n:02d}" for n in rec['back'])
        dlt_lines.append(f"{i}. 🔴 {front} + 🔵 {back}")
    
    messages.append("\n".join(dlt_lines))
    
    full_message = "\n".join(messages) + "\n\n⚠️ 彩票有风险，购买需谨慎\n祝你好运！🍀"
    
    # 输出消息内容
    print(full_message)
    return full_message


if __name__ == "__main__":
    main()
