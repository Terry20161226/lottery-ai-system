#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每 2 周策略汇总分析
计算各策略中奖金额和中奖几率
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from strategy_tracker import StrategyTracker


def format_summary(lottery_type: str, lottery_name: str, stats: dict) -> str:
    """格式化汇总报告"""
    strategy_names = StrategyTracker.STRATEGY_NAMES
    
    lines = [
        f"📊 {lottery_name} 策略汇总报告",
        f"统计周期：近 {stats.get('total_periods', 0)} 期",
        ""
    ]
    
    # 各策略排名
    sorted_strategies = sorted(
        stats.get('strategy_stats', {}).items(),
        key=lambda x: x[1].get('total_prize', 0),
        reverse=True
    )
    
    lines.append("【策略排名】")
    lines.append("")
    
    for rank, (strategy_name, data) in enumerate(sorted_strategies, 1):
        cn_name = strategy_names.get(strategy_name, strategy_name)
        hits = data.get('hits', 0)
        prize = data.get('total_prize', 0)
        hit_rate = data.get('hit_rate', 0)
        
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        lines.append(f"{medal} {rank}. {cn_name}")
        lines.append(f"   中奖次数：{hits} 次 | 累计奖金：¥{prize:,} | 中奖率：{hit_rate:.2f}%")
        lines.append("")
    
    # 最佳策略
    best = stats.get('best_strategy', {})
    lines.append("⭐ 本期最佳策略")
    lines.append(f"   {best.get('name_cn', '均衡策略')}")
    lines.append(f"   累计奖金：¥{best.get('total_prize', 0):,}")
    lines.append(f"   中奖率：{best.get('hit_rate', 0):.2f}%")
    lines.append("")
    lines.append("⚠️ 历史数据仅供参考，不保证未来收益")
    
    return "\n".join(lines)


def main():
    """主函数"""
    tracker = StrategyTracker()
    
    print("=" * 50)
    print("双周策略汇总分析")
    print("=" * 50)
    
    # 双色球
    ssq_stats = tracker.get_summary('ssq')
    ssq_report = format_summary('ssq', '双色球', ssq_stats)
    
    print("\n" + ssq_report)
    
    # 大乐透
    dlt_stats = tracker.get_summary('dlt')
    dlt_report = format_summary('dlt', '大乐透', dlt_stats)
    
    print("\n" + dlt_report)
    
    print("\n" + "=" * 50)
    print("汇总完成")
    print("=" * 50)
    
    return ssq_report + "\n\n" + dlt_report


if __name__ == "__main__":
    main()
