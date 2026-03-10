#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
保存开奖数据到本地（追加模式）
接收 JSON 格式数据作为命令行参数或 stdin
"""

import sys
import json
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


def save_result(lottery_type: str, issue: str, numbers: dict, draw_date: str):
    """保存开奖结果"""
    storage = LotteryStorage()
    
    # 检查是否已存在
    last_issue = storage.get_last_issue(lottery_type)
    if issue == last_issue:
        print(f"⏭️  {lottery_type.upper()} {issue} 期已存在")
        return False
    
    # 保存数据
    saved = storage.save_lottery_result(
        lottery_type=lottery_type,
        issue=issue,
        numbers=numbers,
        draw_date=draw_date
    )
    
    if saved:
        print(f"✅ {lottery_type.upper()} 新增 {issue} 期 ({draw_date})")
        print(f"   号码：{numbers}")
    else:
        print(f"⚠️  {lottery_type.upper()} {issue} 期保存失败")
    
    return saved


if __name__ == "__main__":
    if len(sys.argv) >= 5:
        lottery_type = sys.argv[1]
        issue = sys.argv[2]
        numbers_json = sys.argv[3]
        draw_date = sys.argv[4]
        
        numbers = json.loads(numbers_json)
        save_result(lottery_type, issue, numbers, draw_date)
    else:
        # 从 stdin 读取 JSON
        data = json.loads(sys.stdin.read())
        save_result(data['type'], data['issue'], data['numbers'], data['date'])
