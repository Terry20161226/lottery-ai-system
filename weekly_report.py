#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略效果周报生成器
每周日生成策略效果汇总报告
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

STATS_DIR = Path("/root/.openclaw/workspace/lottery/stats")
REPORTS_DIR = Path("/root/.openclaw/workspace/lottery/reports")

def generate_weekly_report():
    """生成周报"""
    # 加载统计数据
    stats_file = STATS_DIR / "strategy_performance.json"
    if not stats_file.exists():
        print("❌ 无统计数据")
        return
    
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    
    # 本周数据（最近 7 天）
    if not stats['daily_records']:
        print("❌ 无每日记录")
        return
    
    recent_7d = stats['daily_records'][-7:]
    
    # 计算汇总
    total_invested = sum(d['invested'] for d in recent_7d)
    total_prize = sum(d['prize'] for d in recent_7d)
    net = total_prize - total_invested
    roi = net / total_invested * 100 if total_invested > 0 else 0
    
    # 最佳/最差日
    best_day = max(recent_7d, key=lambda x: x['roi'])
    worst_day = min(recent_7d, key=lambda x: x['roi'])
    
    # 生成报告
    report = {
        'report_type': 'weekly',
        'generated_at': datetime.now().isoformat(),
        'period': {
            'start': recent_7d[0]['date'],
            'end': recent_7d[-1]['date']
        },
        'summary': {
            'periods': len(recent_7d),
            'total_invested': total_invested,
            'total_prize': total_prize,
            'net_profit': net,
            'roi': roi
        },
        'daily_breakdown': recent_7d,
        'best_day': {
            'date': best_day['date'],
            'roi': best_day['roi'],
            'prize': best_day['prize']
        },
        'worst_day': {
            'date': worst_day['date'],
            'roi': worst_day['roi'],
            'prize': worst_day['prize']
        },
        'recommendations': []
    }
    
    # 生成建议
    if roi < -30:
        report['recommendations'].append('⚠️ 本周亏损严重，建议降低投注金额')
    if roi > 20:
        report['recommendations'].append('✅ 本周表现良好，保持当前策略')
    if best_day['prize'] > 0 and worst_day['prize'] == 0:
        report['recommendations'].append('📊 表现波动较大，建议稳定投注')
    
    if not report['recommendations']:
        report['recommendations'].append('📈 表现稳定，继续观察')
    
    # 保存报告
    week_num = datetime.now().isocalendar()[1]
    report_file = REPORTS_DIR / f"weekly_report_2026_W{week_num}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 周报已生成：reports/weekly_report_2026_W{week_num}.json")
    print()
    print(f"=== 本周汇总 ({recent_7d[0]['date']} ~ {recent_7d[-1]['date']}) ===")
    print(f"  投注期数：{len(recent_7d)} 期")
    print(f"  总投入：¥{total_invested}")
    print(f"  总奖金：¥{total_prize}")
    print(f"  净收益：¥{net}")
    print(f"  收益率：{roi:.2f}%")
    print()
    print(f"  最佳日：{best_day['date']} (ROI: {best_day['roi']:.2f}%)")
    print(f"  最差日：{worst_day['date']} (ROI: {worst_day['roi']:.2f}%)")
    print()
    print(f"  建议：")
    for rec in report['recommendations']:
        print(f"    {rec}")
    
    return report


if __name__ == "__main__":
    generate_weekly_report()
