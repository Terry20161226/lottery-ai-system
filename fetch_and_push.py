#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票推荐推送脚本 - 动态版本
1. 通过网络搜索获取最新开奖数据
2. 更新本地历史数据
3. 计算冷热号并生成推荐
4. 输出 formatted 消息到钉钉
"""

import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage


def search_lottery_result(lottery_type: str):
    """
    使用 web_search 搜索最新开奖结果
    
    Returns:
        dict: {'issue': str, 'numbers': dict, 'draw_date': str} 或 None
    """
    name = "双色球" if lottery_type == "ssq" else "大乐透"
    query = f"{name} 最新开奖结果 期号 号码 2026 年"
    
    try:
        result = subprocess.run(
            ["openclaw", "web-search", "--query", query, "--count", "3"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # 解析搜索结果（简化处理，实际需要根据返回格式调整）
            output = result.stdout
            # 这里需要解析 web_search 的实际返回格式
            # 暂时返回 None，由后续手动处理
            return None
    except Exception as e:
        print(f"搜索失败：{e}", file=sys.stderr)
    
    return None


def parse_search_result(search_output: str, lottery_type: str):
    """
    解析搜索结果，提取开奖信息
    
    Returns:
        dict: {'issue': str, 'numbers': dict, 'draw_date': str} 或 None
    """
    # 简化实现：返回 None，表示需要手动更新
    return None


def get_next_draw_date(lottery_type: str) -> tuple:
    """
    获取下一期开奖日期和期号
    
    Returns:
        tuple: (draw_date_str, next_issue_str)
    """
    today = datetime.now()
    storage = LotteryStorage()
    last_issue = storage.get_last_issue(lottery_type)
    
    if lottery_type == 'ssq':
        # 双色球：二、四、日开奖（周二、周四、周日）
        draw_days = [1, 3, 6]
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                next_issue = str(int(last_issue) + 1) if last_issue else f"{date.year}001"
                return date.strftime("%Y-%m-%d"), next_issue
    elif lottery_type == 'dlt':
        # 大乐透：一、三、六开奖（周一、周三、周六）
        draw_days = [0, 2, 5]
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                next_issue = str(int(last_issue) + 1) if last_issue else f"{date.year}001"
                return date.strftime("%Y-%m-%d"), next_issue
    
    return today.strftime("%Y-%m-%d"), last_issue or f"{today.year}001"


def generate_recommendation_message(storage: LotteryStorage, lottery_type: str, lottery_name: str) -> str:
    """生成推荐号码消息"""
    draw_date, next_issue = get_next_draw_date(lottery_type)
    strategy = storage.get_settings().get('strategy', 'balanced')
    
    # 生成推荐
    recommendations = storage.generate_recommendation(lottery_type, next_issue, strategy)
    storage.save_recommendation(lottery_type, next_issue, recommendations, strategy)
    
    # 格式化消息
    lines = [
        f"🎰 {lottery_name} 推荐",
        f"📅 开奖：{draw_date} | 期号：{next_issue}",
        f"💡 策略：均衡（热号 + 冷号）",
        ""
    ]
    
    for i, rec in enumerate(recommendations, 1):
        if lottery_type == 'ssq':
            red = ' '.join(f"{n:02d}" for n in rec['red'])
            blue = ' '.join(f"{n:02d}" for n in rec['blue'])
            lines.append(f"{i}. 🔴 {red} + 🔵 {blue}")
        elif lottery_type == 'dlt':
            front = ' '.join(f"{n:02d}" for n in rec['front'])
            back = ' '.join(f"{n:02d}" for n in rec['back'])
            lines.append(f"{i}. 🔴 {front} + 🔵 {back}")
    
    return "\n".join(lines)


def main():
    """主函数"""
    storage = LotteryStorage()
    
    # 生成双色球推荐
    ssq_message = generate_recommendation_message(storage, 'ssq', '双色球')
    
    # 生成大乐透推荐
    dlt_message = generate_recommendation_message(storage, 'dlt', '大乐透')
    
    # 组合消息
    full_message = f"{ssq_message}\n\n{dlt_message}\n\n⚠️ 彩票有风险，购买需谨慎\n祝你好运！🍀"
    
    print(full_message)
    return full_message


if __name__ == "__main__":
    main()
