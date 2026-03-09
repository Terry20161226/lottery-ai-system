#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每 2 周策略汇总分析
计算各策略中奖金额和中奖几率
"""

import sys
import json
import os
from datetime import datetime

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

# 策略名称映射
STRATEGY_NAMES = {
    "balanced": "均衡策略",
    "hot_tracking": "热号追踪",
    "cold_rebound": "冷号反弹",
    "odd_even": "奇偶均衡",
    "zone_distribution": "区间分布",
    "consecutive": "连号追踪",
    "warm_balance": "温号搭配",
    "hot": "热号追踪",
    "warm": "温号搭配",
    "cold": "冷号反弹",
    "zone": "区间分布",
    # 快三策略
    "hot_number": "热号追踪",
    "cold_number": "冷号反弹",
    "sum_trend": "和值趋势",
    "pattern_follow": "形态追踪",
}

STATS_DIR = "/root/.openclaw/workspace/lottery/stats"


def load_stats(lottery_type):
    """加载策略统计数据"""
    filepath = os.path.join(STATS_DIR, f"{lottery_type}_strategy_stats.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def format_summary(lottery_type: str, lottery_name: str, stats: dict) -> str:
    """格式化汇总报告"""
    if not stats:
        return f"⏳ 暂无 {lottery_name} 统计数据"
    
    lines = [
        f"📊 {lottery_name} 策略汇总报告",
        f"统计周期：近 {stats.get('total_draws', 0)} 期",
        f"更新时间：{stats.get('last_update', '未知')[:10]}",
        ""
    ]
    
    # 各策略排名（基于 stragies 数据）
    strategies = stats.get('strategies', {})
    if not strategies:
        lines.append("📭 暂无策略数据")
        return "\n".join(lines)
    
    sorted_strategies = sorted(
        strategies.items(),
        key=lambda x: x[1].get('total_amount', 0),
        reverse=True
    )
    
    lines.append("【策略排名】")
    lines.append("")
    
    for rank, (strategy_id, data) in enumerate(sorted_strategies, 1):
        cn_name = data.get('name', STRATEGY_NAMES.get(strategy_id, strategy_id))
        win_notes = data.get('win_notes', 0)
        total_notes = data.get('total_notes', 0)
        prize = data.get('total_amount', 0)
        win_rate = data.get('win_rate', 0)
        roi = data.get('roi', 0)
        
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        lines.append(f"{medal} {rank}. {cn_name}")
        lines.append(f"   投注注数：{total_notes} | 中奖注数：{win_notes} | 累计奖金：¥{prize:,} | 中奖率：{win_rate:.2f}% | ROI：{roi:.2f}%")
        lines.append("")
    
    # 最佳策略
    if sorted_strategies:
        best_id, best_data = sorted_strategies[0]
        best_name = best_data.get('name', STRATEGY_NAMES.get(best_id, best_id))
        lines.append("⭐ 本期最佳策略")
        lines.append(f"   {best_name}")
        lines.append(f"   累计奖金：¥{best_data.get('total_amount', 0):,}")
        lines.append(f"   中奖率：{best_data.get('win_rate', 0):.2f}%")
        lines.append(f"   ROI：{best_data.get('roi', 0):.2f}%")
    
    lines.append("")
    lines.append("⚠️ 历史数据仅供参考，不保证未来收益")
    
    return "\n".join(lines)


def main():
    """主函数"""
    print("=" * 50)
    print("双周策略汇总分析")
    print("=" * 50)
    
    # 双色球
    ssq_stats = load_stats('ssq')
    ssq_report = format_summary('ssq', '双色球', ssq_stats)
    
    print("\n" + ssq_report)
    
    # 大乐透
    dlt_stats = load_stats('dlt')
    dlt_report = format_summary('dlt', '大乐透', dlt_stats)
    
    print("\n" + dlt_report)
    
    # 快三
    ks3_stats = load_stats('ks3')
    ks3_report = format_summary('ks3', '快三', ks3_stats)
    
    print("\n" + ks3_report)
    
    # 保存完整报告
    report_file = os.path.join(STATS_DIR, "biweekly_summary_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"生成时间：{datetime.now().isoformat()}\n\n")
        f.write(ssq_report + "\n\n")
        f.write(dlt_report + "\n\n")
        f.write(ks3_report)
    
    print("\n" + "=" * 50)
    print(f"💾 报告已保存到：{report_file}")
    print("=" * 50)
    
    return ssq_report + "\n\n" + dlt_report + "\n\n" + ks3_report


if __name__ == "__main__":
    main()
