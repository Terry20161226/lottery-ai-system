#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略效果追踪器
每日自动统计策略效果，生成报告
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("/root/.openclaw/workspace/lottery/data")
STATS_DIR = Path("/root/.openclaw/workspace/lottery/stats")
REPORTS_DIR = Path("/root/.openclaw/workspace/lottery/reports")

def load_strategy_stats():
    """加载策略统计数据"""
    stats_file = STATS_DIR / "strategy_performance.json"
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'daily_records': [],
        'weekly_summary': [],
        'total_invested': 0,
        'total_prize': 0,
        'total_periods': 0
    }

def save_strategy_stats(stats):
    """保存策略统计数据"""
    stats_file = STATS_DIR / "strategy_performance.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def calculate_daily_performance():
    """计算当日表现"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    # 加载当日日志
    log_file = DATA_DIR / f"recommend_{today}.json"
    if not log_file.exists():
        return None
    
    with open(log_file, 'r', encoding='utf-8') as f:
        recommendations = json.load(f)
    
    # 统计
    invested = len(recommendations.get('notes', [])) * 2  # 每注 2 元
    prize = sum(note.get('prize', 0) for note in recommendations.get('notes', []))
    
    return {
        'date': today,
        'invested': invested,
        'prize': prize,
        'net': prize - invested,
        'roi': (prize - invested) / invested * 100 if invested > 0 else 0,
        'notes_count': len(recommendations.get('notes', []))
    }

def update_stats():
    """更新统计数据"""
    stats = load_strategy_stats()
    
    # 计算当日表现
    daily = calculate_daily_performance()
    if daily:
        # 避免重复添加
        existing_dates = {r['date'] for r in stats['daily_records']}
        if daily['date'] not in existing_dates:
            stats['daily_records'].append(daily)
            stats['total_invested'] += daily['invested']
            stats['total_prize'] += daily['prize']
            stats['total_periods'] += 1
    
    # 计算周汇总
    if stats['daily_records']:
        # 最近 7 天
        recent_7d = stats['daily_records'][-7:]
        weekly = {
            'week_start': recent_7d[0]['date'],
            'week_end': recent_7d[-1]['date'],
            'total_invested': sum(d['invested'] for d in recent_7d),
            'total_prize': sum(d['prize'] for d in recent_7d),
            'net': sum(d['net'] for d in recent_7d),
            'roi': sum(d['net'] for d in recent_7d) / sum(d['invested'] for d in recent_7d) * 100 if sum(d['invested']) > 0 else 0,
            'periods': len(recent_7d)
        }
        
        # 避免重复添加
        existing_weeks = {w['week_end'] for w in stats['weekly_summary']}
        if weekly['week_end'] not in existing_weeks:
            stats['weekly_summary'].append(weekly)
    
    save_strategy_stats(stats)
    return stats

def generate_report(stats):
    """生成策略效果报告"""
    report = {
        'generated_at': datetime.now().isoformat(),
        'overall': {
            'total_periods': stats['total_periods'],
            'total_invested': stats['total_invested'],
            'total_prize': stats['total_prize'],
            'net_profit': stats['total_prize'] - stats['total_invested'],
            'roi': (stats['total_prize'] - stats['total_invested']) / stats['total_invested'] * 100 if stats['total_invested'] > 0 else 0
        },
        'recent_7d': None,
        'trend': 'stable'
    }
    
    # 最近 7 天表现
    if stats['daily_records']:
        recent_7d = stats['daily_records'][-7:]
        report['recent_7d'] = {
            'periods': len(recent_7d),
            'avg_daily_invested': sum(d['invested'] for d in recent_7d) / len(recent_7d),
            'avg_daily_prize': sum(d['prize'] for d in recent_7d) / len(recent_7d),
            'avg_daily_roi': sum(d['roi'] for d in recent_7d) / len(recent_7d)
        }
        
        # 趋势分析
        if len(recent_7d) >= 3:
            first_half = sum(d['roi'] for d in recent_7d[:len(recent_7d)//2])
            second_half = sum(d['roi'] for d in recent_7d[len(recent_7d)//2:])
            if second_half > first_half + 5:
                report['trend'] = 'improving'
            elif second_half < first_half - 5:
                report['trend'] = 'declining'
    
    # 告警
    alerts = []
    if report['overall']['roi'] < -50:
        alerts.append('⚠️ 收益率低于 -50%，建议降低投注')
    if stats['total_periods'] > 0 and stats['total_prize'] == 0:
        alerts.append('⚠️ 连续未中奖，建议调整策略')
    
    report['alerts'] = alerts
    
    # 保存报告
    report_file = REPORTS_DIR / f"strategy_report_{datetime.now().strftime('%Y%m%d')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report

def main():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始策略效果追踪...")
    
    # 更新统计
    stats = update_stats()
    print(f"  ✅ 统计数据已更新")
    print(f"     总期数：{stats['total_periods']}")
    print(f"     总投入：¥{stats['total_invested']}")
    print(f"     总奖金：¥{stats['total_prize']}")
    
    # 生成报告
    report = generate_report(stats)
    print(f"  ✅ 报告已生成")
    print(f"     总收益率：{report['overall']['roi']:.2f}%")
    print(f"     趋势：{report['trend']}")
    
    if report['alerts']:
        print(f"\n  ⚠️ 告警：")
        for alert in report['alerts']:
            print(f"     {alert}")
    
    print(f"\n  报告文件：reports/strategy_report_{datetime.now().strftime('%Y%m%d')}.json")


if __name__ == "__main__":
    main()
