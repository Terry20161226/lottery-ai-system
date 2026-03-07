#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票真实开奖数据获取脚本
通过网络搜索获取最新开奖数据并更新到本地存储
"""

import sys
import json
import subprocess
import re
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage


def web_search_lottery(lottery_type: str, page: int = 1):
    """
    使用 web_search 搜索开奖结果
    
    Args:
        lottery_type: 'ssq' 或 'dlt'
        page: 页码（用于分页获取多期数据）
    
    Returns:
        str: 搜索结果文本
    """
    name = "双色球" if lottery_type == "ssq" else "大乐透"
    
    # 搜索最近开奖数据
    if page == 1:
        query = f"{name} 最新开奖结果 2026 年 期号 红球 蓝球 开奖号码"
    else:
        query = f"{name} 历史开奖数据 2026 年 期号 开奖结果 第{page}页"
    
    try:
        result = subprocess.run(
            ["openclaw", "web-search", "--query", query, "--count", "5"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"搜索失败：{result.stderr}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"搜索异常：{e}", file=sys.stderr)
        return None


def parse_ssq_result(search_text: str):
    """
    解析双色球搜索结果
    
    Returns:
        list: [{'issue': str, 'numbers': {'red': [], 'blue': []}, 'draw_date': str}, ...]
    """
    records = []
    
    if not search_text:
        return records
    
    # 尝试匹配常见格式
    # 格式1: 双色球第 2026023 期开奖号码：05 12 18 23 27 31 + 09
    pattern1 = r'第\s*(\d+)\s*期.*?[\u7ea2\u7ea2\u7403]?\s*[:：]?\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*[\+＋]\s*(\d+)'
    
    # 格式2: 2026023 期 开奖日期 2026-03-03 红球 05 12 18 23 27 31 蓝球 09
    pattern2 = r'(\d+)\s*期.*?(\d{4}-\d{2}-\d{2}).*?红球.*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+).*?蓝球.*?(\d+)'
    
    # 格式3: 开奖期号 2026023 开奖日期 2026-03-03 中奖号码 05 12 18 23 27 31 09
    pattern3 = r'期号.*?(\d+).*?日期.*?(\d{4}-\d{2}-\d{2}).*?号码.*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)'
    
    for pattern in [pattern1, pattern2, pattern3]:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 8:  # pattern1
                    issue = match[0]
                    red = [int(match[i]) for i in range(1, 7)]
                    blue = [int(match[7])]
                    draw_date = datetime.now().strftime("%Y-%m-%d")
                elif len(match) == 9:  # pattern2
                    issue = match[0]
                    draw_date = match[1]
                    red = [int(match[i]) for i in range(2, 8)]
                    blue = [int(match[8])]
                elif len(match) == 9:  # pattern3
                    issue = match[0]
                    draw_date = match[1]
                    red = [int(match[i]) for i in range(2, 8)]
                    blue = [int(match[8])]
                else:
                    continue
                
                records.append({
                    "issue": issue,
                    "draw_date": draw_date,
                    "numbers": {"red": sorted(red), "blue": blue}
                })
            except (ValueError, IndexError) as e:
                continue
    
    return records


def parse_dlt_result(search_text: str):
    """
    解析大乐透搜索结果
    
    Returns:
        list: [{'issue': str, 'numbers': {'front': [], 'back': []}, 'draw_date': str}, ...]
    """
    records = []
    
    if not search_text:
        return records
    
    # 格式1: 大乐透第 2026023 期：05 12 18 23 27 + 09 11
    pattern1 = r'第\s*(\d+)\s*期.*?[\u524d\u533a]?\s*[:：]?\s*(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s*[\+＋]\s*(\d+)\s+(\d+)'
    
    # 格式2: 2026023 期 开奖日期 2026-03-03 前区 05 12 18 23 27 后区 09 11
    pattern2 = r'(\d+)\s*期.*?(\d{4}-\d{2}-\d{2}).*?前区.*?(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+).*?后区.*?(\d+)\s+(\d+)'
    
    for pattern in [pattern1, pattern2]:
        matches = re.findall(pattern, search_text, re.IGNORECASE)
        for match in matches:
            try:
                if len(match) == 8:  # pattern1
                    issue = match[0]
                    front = [int(match[i]) for i in range(1, 6)]
                    back = [int(match[6]), int(match[7])]
                    draw_date = datetime.now().strftime("%Y-%m-%d")
                elif len(match) == 9:  # pattern2
                    issue = match[0]
                    draw_date = match[1]
                    front = [int(match[i]) for i in range(2, 7)]
                    back = [int(match[7]), int(match[8])]
                else:
                    continue
                
                records.append({
                    "issue": issue,
                    "draw_date": draw_date,
                    "numbers": {"front": sorted(front), "back": sorted(back)}
                })
            except (ValueError, IndexError) as e:
                continue
    
    return records


def fetch_and_save(lottery_type: str, storage: LotteryStorage, max_records: int = 50):
    """
    获取并保存开奖数据
    
    Args:
        lottery_type: 'ssq' 或 'dlt'
        storage: LotteryStorage 实例
        max_records: 最多获取期数
    
    Returns:
        int: 成功导入的记录数
    """
    print(f"\n========== 获取{('双色球' if lottery_type == 'ssq' else '大乐透')}数据 ==========")
    
    all_records = []
    page = 1
    
    while len(all_records) < max_records and page <= 5:
        search_text = web_search_lottery(lottery_type, page)
        
        if not search_text:
            print(f"第{page}页搜索失败，跳过")
            page += 1
            continue
        
        if lottery_type == 'ssq':
            records = parse_ssq_result(search_text)
        else:
            records = parse_dlt_result(search_text)
        
        if not records:
            print(f"第{page}页未解析到数据")
            page += 1
            continue
        
        all_records.extend(records)
        print(f"第{page}页解析到 {len(records)} 条记录")
        page += 1
    
    # 去重并保存
    saved_count = 0
    for record in all_records:
        if lottery_type == 'ssq':
            result = storage.save_lottery_result(
                lottery_type='ssq',
                issue=record['issue'],
                numbers=record['numbers'],
                draw_date=record['draw_date']
            )
        else:
            result = storage.save_lottery_result(
                lottery_type='dlt',
                issue=record['issue'],
                numbers=record['numbers'],
                draw_date=record['draw_date']
            )
        
        if result:
            saved_count += 1
    
    print(f"成功导入 {saved_count} 条新记录")
    return saved_count


def main():
    """主函数"""
    storage = LotteryStorage()
    
    print("=" * 50)
    print("彩票真实数据获取脚本")
    print("=" * 50)
    
    # 获取双色球数据
    ssq_count = fetch_and_save('ssq', storage, max_records=50)
    
    # 获取大乐透数据
    dlt_count = fetch_and_save('dlt', storage, max_records=50)
    
    # 显示统计
    print("\n========== 导入统计 ==========")
    ssq_stats = storage.get_statistics('ssq')
    dlt_stats = storage.get_statistics('dlt')
    
    print(f"双色球总记录：{ssq_stats['total_records']} 期（本次新增：{ssq_count}）")
    print(f"双色球最新期号：{ssq_stats['last_issue']}")
    print(f"大乐透总记录：{dlt_stats['total_records']} 期（本次新增：{dlt_count}）")
    print(f"大乐透最新期号：{dlt_stats['last_issue']}")
    
    return ssq_count, dlt_count


if __name__ == "__main__":
    main()
