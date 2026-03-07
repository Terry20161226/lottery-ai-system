#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动获取最新开奖数据并更新到本地（追加模式）
"""

import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage


def web_search_lottery_result(lottery_type: str):
    """
    使用 web_search 获取最新开奖结果
    
    Returns:
        str: 搜索结果文本 或 None
    """
    name = "双色球" if lottery_type == "ssq" else "大乐透"
    query = f"{name} 最新开奖结果 2026 年 期号 开奖号码"
    
    # 使用 shell 调用，避免 Python 版本兼容问题
    cmd = f'openclaw web-search --query "{query}" --count 3 2>/dev/null'
    
    try:
        result = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = result.communicate()
        
        if result.returncode == 0:
            return stdout.decode('utf-8') if isinstance(stdout, bytes) else stdout
    except Exception as e:
        print(f"搜索失败：{e}", file=sys.stderr)
    
    return None


def parse_ssq_result(search_text: str):
    """解析双色球搜索结果"""
    import re
    
    if not search_text:
        return None
    
    # 匹配格式：双色球第 2026023 期开奖号码：01 03 08 10 23 29+06
    patterns = [
        r'第\s*(\d+)\s*期.*?[\u7ea2\u7403]?\s*[:：]?\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*[\+＋]\s*(\d+)',
        r'(\d+)\s*期.*?(\d{4}-\d{2}-\d{2}).*?红球.*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+).*?蓝球.*?(\d+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        if matches:
            match = matches[0]
            try:
                if len(match) == 8:
                    issue = match[0]
                    red = sorted([int(match[i]) for i in range(1, 7)])
                    blue = [int(match[7])]
                    return {'issue': issue, 'numbers': {'red': red, 'blue': blue}}
                elif len(match) == 9:
                    issue = match[0]
                    draw_date = match[1]
                    red = sorted([int(match[i]) for i in range(2, 8)])
                    blue = [int(match[8])]
                    return {'issue': issue, 'numbers': {'red': red, 'blue': blue}, 'draw_date': draw_date}
            except (ValueError, IndexError):
                continue
    
    return None


def parse_dlt_result(search_text: str):
    """解析大乐透搜索结果"""
    import re
    
    if not search_text:
        return None
    
    patterns = [
        r'第\s*(\d+)\s*期.*?[\u524d\u533a]?\s*[:：]?\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*[\+＋]\s*(\d+)\s+(\d+)',
        r'(\d+)\s*期.*?(\d{4}-\d{2}-\d{2}).*?前区.*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+).*?后区.*?(\d+)\s+(\d+)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        if matches:
            match = matches[0]
            try:
                if len(match) == 8:
                    issue = match[0]
                    front = sorted([int(match[i]) for i in range(1, 6)])
                    back = sorted([int(match[6]), int(match[7])])
                    return {'issue': issue, 'numbers': {'front': front, 'back': back}}
                elif len(match) == 9:
                    issue = match[0]
                    draw_date = match[1]
                    front = sorted([int(match[i]) for i in range(2, 7)])
                    back = sorted([int(match[7]), int(match[8])])
                    return {'issue': issue, 'numbers': {'front': front, 'back': back}, 'draw_date': draw_date}
            except (ValueError, IndexError):
                continue
    
    return None


def update_lottery_data(lottery_type: str, storage: LotteryStorage):
    """
    更新开奖数据（追加模式）
    
    Returns:
        int: 新增记录数
    """
    name = "双色球" if lottery_type == "ssq" else "大乐透"
    print(f"\n========== 更新{name}数据 ==========")
    
    # 获取最新开奖
    search_text = web_search_lottery_result(lottery_type)
    
    if not search_text:
        print(f"⚠️  {name}搜索失败，跳过")
        return 0
    
    # 解析结果
    if lottery_type == "ssq":
        result = parse_ssq_result(search_text)
    else:
        result = parse_dlt_result(search_text)
    
    if not result:
        print(f"⚠️  {name}解析失败，跳过")
        return 0
    
    # 检查是否已存在
    last_issue = storage.get_last_issue(lottery_type)
    
    if result['issue'] == last_issue:
        print(f"✅ {name}已是最新（{result['issue']} 期）")
        return 0
    
    # 追加新数据
    draw_date = result.get('draw_date', datetime.now().strftime("%Y-%m-%d"))
    
    saved = storage.save_lottery_result(
        lottery_type=lottery_type,
        issue=result['issue'],
        numbers=result['numbers'],
        draw_date=draw_date
    )
    
    if saved:
        print(f"✅ {name}新增 {result['issue']} 期 ({draw_date})")
        print(f"   号码：{result['numbers']}")
        return 1
    else:
        print(f"⏭️  {name}{result['issue']} 期已存在")
        return 0


def main():
    """主函数"""
    storage = LotteryStorage()
    
    print("=" * 50)
    print("自动更新开奖数据（追加模式）")
    print("=" * 50)
    
    # 更新双色球
    ssq_count = update_lottery_data('ssq', storage)
    
    # 更新大乐透
    dlt_count = update_lottery_data('dlt', storage)
    
    # 显示统计
    print("\n========== 更新统计 ==========")
    ssq_stats = storage.get_statistics('ssq')
    dlt_stats = storage.get_statistics('dlt')
    
    print(f"双色球：{ssq_stats['total_records']} 期（最新：{ssq_stats['last_issue']}）")
    print(f"大乐透：{dlt_stats['total_records']} 期（最新：{dlt_stats['last_issue']}）")
    print(f"\n本次新增：双色球 {ssq_count} 期，大乐透 {dlt_count} 期")
    
    return ssq_count + dlt_count


if __name__ == "__main__":
    main()
