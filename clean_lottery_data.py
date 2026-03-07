#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票历史数据清洗脚本
从网页解析结果中提取并清洗开奖数据
"""

import re
import json
import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


def parse_ssq_from_html(html_content: str) -> list:
    """
    从 HTML 内容中解析双色球开奖数据
    
    匹配格式：
    - 20260232026-03-0301030810232906
    - 202415013142022263202
    """
    results = []
    
    # 匹配模式：期号 + 日期 + 红球 6 位 + 蓝球 1 位
    # 例如：20260232026-03-0301030810232906
    pattern = r'(\d{7})(\d{4}-\d{2}-\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})'
    
    matches = re.findall(pattern, html_content)
    
    for match in matches:
        try:
            issue = match[0]
            draw_date = match[1]
            red_balls = sorted([int(match[2]), int(match[3]), int(match[4]), 
                               int(match[5]), int(match[6]), int(match[7])])
            blue_ball = int(match[8])
            
            # 验证数据有效性
            if all(1 <= n <= 33 for n in red_balls) and 1 <= blue_ball <= 16:
                results.append({
                    'issue': issue,
                    'draw_date': draw_date,
                    'numbers': {
                        'red': red_balls,
                        'blue': [blue_ball]
                    }
                })
        except (ValueError, IndexError):
            continue
    
    return results


def parse_dlt_from_html(html_content: str) -> list:
    """
    从 HTML 内容中解析大乐透开奖数据
    
    匹配格式：
    - 20260222026-03-0405091018260506
    """
    results = []
    
    # 匹配模式：期号 + 日期 + 前区 5 位 + 后区 2 位
    pattern = r'(\d{7})(\d{4}-\d{2}-\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})'
    
    matches = re.findall(pattern, html_content)
    
    for match in matches:
        try:
            issue = match[0]
            draw_date = match[1]
            front_balls = sorted([int(match[2]), int(match[3]), int(match[4]), 
                                 int(match[5]), int(match[6])])
            back_balls = sorted([int(match[7]), int(match[8])])
            
            # 验证数据有效性
            if all(1 <= n <= 35 for n in front_balls) and all(1 <= n <= 12 for n in back_balls):
                results.append({
                    'issue': issue,
                    'draw_date': draw_date,
                    'numbers': {
                        'front': front_balls,
                        'back': back_balls
                    }
                })
        except (ValueError, IndexError):
            continue
    
    return results


def parse_ssq_list_format(html_content: str) -> list:
    """
    解析列表格式的双色球数据
    
    匹配格式：
    2026-03-0320260231381023296361,967,792...
    或
    20251452025-12-1612111525321811121518253214
    """
    results = []
    
    # 匹配：日期 + 期号 + 红球 + 蓝球
    pattern1 = r'(\d{4}-\d{2}-\d{2})(\d{7}).*?(?:红球 | 号码)[:\s]*(\d{2})[\s,]*(\d{2})[\s,]*(\d{2})[\s,]*(\d{2})[\s,]*(\d{2})[\s,]*(\d{2}).*?(?:蓝球 | 蓝球)[:\s]*(\d{2})'
    
    matches = re.findall(pattern1, html_content, re.DOTALL)
    
    for match in matches:
        try:
            draw_date = match[0]
            issue = match[1]
            red_balls = sorted([int(match[2]), int(match[3]), int(match[4]), 
                               int(match[5]), int(match[6]), int(match[7])])
            blue_ball = int(match[8])
            
            if all(1 <= n <= 33 for n in red_balls) and 1 <= blue_ball <= 16:
                results.append({
                    'issue': issue,
                    'draw_date': draw_date,
                    'numbers': {
                        'red': red_balls,
                        'blue': [blue_ball]
                    }
                })
        except (ValueError, IndexError):
            continue
    
    return results


def clean_and_import(html_files: list, lottery_type: str):
    """
    清洗并导入数据
    
    Args:
        html_files: HTML 文件路径列表
        lottery_type: 'ssq' 或 'dlt'
    """
    storage = LotteryStorage()
    all_results = []
    
    print(f"\n开始处理 {lottery_type} 数据...")
    
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            if lottery_type == 'ssq':
                results = parse_ssq_from_html(html_content)
                if not results:
                    results = parse_ssq_list_format(html_content)
            else:
                results = parse_dlt_from_html(html_content)
            
            all_results.extend(results)
            print(f"  {file_path}: 解析到 {len(results)} 期")
            
        except Exception as e:
            print(f"  {file_path}: 解析失败 - {e}")
    
    # 去重
    unique_results = {}
    for r in all_results:
        issue = r['issue']
        if issue not in unique_results:
            unique_results[issue] = r
    
    final_results = list(unique_results.values())
    
    # 按期号排序
    final_results.sort(key=lambda x: x['issue'], reverse=True)
    
    print(f"\n清洗后数据：{len(final_results)}期")
    
    # 批量导入
    if final_results:
        imported, skipped = storage.batch_save_lottery_results(lottery_type, final_results)
        print(f"  导入成功：{imported}期")
        print(f"  跳过重复：{skipped}期")
    
    return len(final_results)


def main():
    """主函数"""
    import os
    
    print("=" * 70)
    print("🧹 彩票历史数据清洗与导入")
    print("=" * 70)
    
    # 检查数据目录
    data_dir = '/root/.openclaw/workspace/lottery/raw_data'
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"\n创建数据目录：{data_dir}")
        print("\n📌 使用说明：")
        print("1. 将网页解析的 HTML 内容保存到以下文件：")
        print(f"   - {data_dir}/ssq_2024.html")
        print(f"   - {data_dir}/ssq_2023.html")
        print(f"   - {data_dir}/dlt_2024.html")
        print(f"   - {data_dir}/dlt_2023.html")
        print("2. 运行此脚本自动清洗和导入")
        return
    
    # 查找 HTML 文件
    ssq_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                 if f.startswith('ssq') and f.endswith('.html')]
    dlt_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir) 
                 if f.startswith('dlt') and f.endswith('.html')]
    
    # 处理双色球
    if ssq_files:
        clean_and_import(ssq_files, 'ssq')
    else:
        print("\n⚠️  未找到双色球 HTML 文件")
    
    # 处理大乐透
    if dlt_files:
        clean_and_import(dlt_files, 'dlt')
    else:
        print("\n⚠️  未找到大乐透 HTML 文件")
    
    # 最终统计
    storage = LotteryStorage()
    ssq_count = len(storage.get_history('ssq', 2000))
    dlt_count = len(storage.get_history('dlt', 2000))
    
    print("\n" + "=" * 70)
    print("📊 最终数据量")
    print("=" * 70)
    print(f"  双色球：{ssq_count}期")
    print(f"  大乐透：{dlt_count}期")
    print("=" * 70)


if __name__ == "__main__":
    main()
