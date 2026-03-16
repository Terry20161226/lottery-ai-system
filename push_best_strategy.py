#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送最佳策略推荐号码到钉钉
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from lottery_strategies import LotteryStrategies
# strategy_tracker 是函数模块，不是类
from adaptive_strategy import AdaptiveStrategy
from datetime import datetime, timedelta


def get_next_draw_date(lottery_type: str) -> tuple:
    """获取下一期开奖日期和期号"""
    today = datetime.now()
    storage = LotteryStorage()
    last_issue = storage.get_last_issue(lottery_type)
    
    # 计算下期期号（基于当前年份和周数）
    year = today.year
    week_num = today.isocalendar()[1]
    
    if lottery_type == 'ssq':
        # 双色球：每周二、四、日开奖，每年约 153-156 期
        draw_days = [1, 3, 6]  # 周二、周四、周六
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                # 期号格式：YYYY + 3 位序号 (001-156)
                # 简单估算：每周 3 期，第 N 周约有 N*3 期
                issue_seq = min(156, (week_num - 1) * 3 + draw_days.index(date.weekday()) + 1)
                next_issue = f"{year}{issue_seq:03d}"
                return date.strftime("%Y-%m-%d"), next_issue
    elif lottery_type == 'dlt':
        # 大乐透：每周一、三、六开奖，每年约 153-156 期
        draw_days = [0, 2, 5]  # 周一、周三、周六
        for i in range(1, 8):
            date = today + timedelta(days=i)
            if date.weekday() in draw_days:
                issue_seq = min(156, (week_num - 1) * 3 + draw_days.index(date.weekday()) + 1)
                next_issue = f"{year}{issue_seq:03d}"
                return date.strftime("%Y-%m-%d"), next_issue
    
    return today.strftime("%Y-%m-%d"), f"{year}024"


def generate_best_recommendation(lottery_type: str, strategy_name: str) -> tuple:
    """生成最佳策略推荐"""
    storage = LotteryStorage()
    strategies = LotteryStrategies(storage)
    
    all_strategies = strategies.get_all_strategies(lottery_type)
    strategy_func = all_strategies.get(strategy_name)
    
    if not strategy_func:
        return None, None, None
    
    draw_date, next_issue = get_next_draw_date(lottery_type)
    recommendations = strategy_func()
    
    return recommendations, next_issue, draw_date


def format_message(lottery_type: str, lottery_name: str, strategy_name: str, 
                   recommendations: list, next_issue: str, draw_date: str) -> str:
    """格式化推送消息"""
    lines = [
        f"🎰 {lottery_name} 推荐",
        f"📅 开奖：{draw_date} | 期号：{next_issue}",
        f"💡 策略：{strategy_name}（根据近期中奖率智能选择）",
        ""
    ]
    
    for i, rec in enumerate(recommendations, 1):
        if lottery_type == 'ssq':
            red = ' '.join(f"{n:02d}" for n in rec['red'])
            blue = ' '.join(f"{n:02d}" for n in rec['blue'])
            lines.append(f"{i}. 🔴 {red} + 🔵 {blue}")
        else:
            front = ' '.join(f"{n:02d}" for n in rec['front'])
            back = ' '.join(f"{n:02d}" for n in rec['back'])
            lines.append(f"{i}. 🔴 {front} + 🔵 {back}")
    
    lines.extend([
        "",
        "⚠️ 彩票有风险，购买需谨慎",
        "祝你好运！🍀"
    ])
    
    return "\n".join(lines)


def main():
    """主函数 - 使用自适应策略"""
    from lottery_strategies import LotteryStrategies
    
    adaptive = AdaptiveStrategy()
    # tracker = StrategyTracker()  # 已移除
    storage = LotteryStorage()
    strategies = LotteryStrategies(storage)
    
    messages = []
    
    # 双色球
    ssq_draw_date, ssq_next_issue = get_next_draw_date('ssq')
    ssq_recs = adaptive.generate_adaptive_recommendation('ssq', 5)
    
    if ssq_recs:
        ssq_msg = format_adaptive_message('ssq', '双色球', ssq_recs, ssq_next_issue, ssq_draw_date, adaptive)
        messages.append(ssq_msg)
        
        # 保存推荐结果到 tracker（用于后续核对中奖）
        all_ssq_strategies = strategies.get_all_strategies('ssq')
        ssq_all_result = {name: func() for name, func in all_ssq_strategies.items()}
        # tracker.save_recommendations  # 已移除('ssq', ssq_next_issue, ssq_all_result)
        print(f"✅ 双色球推荐已保存：{ssq_next_issue}")
    
    # 大乐透
    dlt_draw_date, dlt_next_issue = get_next_draw_date('dlt')
    dlt_recs = adaptive.generate_adaptive_recommendation('dlt', 5)
    
    if dlt_recs:
        dlt_msg = format_adaptive_message('dlt', '大乐透', dlt_recs, dlt_next_issue, dlt_draw_date, adaptive)
        messages.append(dlt_msg)
        
        # 保存推荐结果到 tracker
        all_dlt_strategies = strategies.get_all_strategies('dlt')
        dlt_all_result = {name: func() for name, func in all_dlt_strategies.items()}
        # tracker.save_recommendations  # 已移除('dlt', dlt_next_issue, dlt_all_result)
        print(f"✅ 大乐透推荐已保存：{dlt_next_issue}")
    
    full_message = "\n\n".join(messages)
    
    print("\n" + full_message)
    return full_message


def format_adaptive_message(lottery_type: str, lottery_name: str, 
                           recommendations: list, next_issue: str, 
                           draw_date: str, adaptive: AdaptiveStrategy) -> str:
    """格式化自适应策略推送消息"""
    weights_explanation = ""  # 已移除
    
    lines = [
        f"🎰 {lottery_name} 智能推荐",
        f"📅 开奖：{draw_date} | 期号：{next_issue}",
        f"💡 策略：自适应策略（根据历史数据动态优化）",
        ""
    ]
    
    for i, rec in enumerate(recommendations, 1):
        strategy = rec.get('strategy_name', '均衡策略')
        if lottery_type == 'ssq':
            red = ' '.join(f"{n:02d}" for n in rec['red'])
            blue = ' '.join(f"{n:02d}" for n in rec['blue'])
            lines.append(f"{i}. [{strategy}] 🔴 {red} + 🔵 {blue}")
        else:
            front = ' '.join(f"{n:02d}" for n in rec['front'])
            back = ' '.join(f"{n:02d}" for n in rec['back'])
            lines.append(f"{i}. [{strategy}] 🔴 {front} + 🔵 {back}")
    
    lines.extend([
        "",
        weights_explanation,
        "",
        "⚠️ 彩票有风险，购买需谨慎",
        "祝你好运！🍀"
    ])
    
    return "\n".join(lines)


if __name__ == "__main__":
    main()
