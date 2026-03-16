#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票策略预警系统
监控策略表现，发出预警信号
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


def load_strategy_stats():
    """加载策略统计数据"""
    stats_file = Path('/root/.openclaw/workspace/lottery/stats/strategy_stats.json')
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def check_warnings(stats):
    """检查预警条件"""
    warnings = []
    
    for strategy_name, data in stats.items():
        recent = data.get('recent', [])
        
        # 1. 连续 5 期未中奖
        lose_streak = 0
        for period in recent[:5]:
            if not period.get('win', False):
                lose_streak += 1
            else:
                break
        
        if lose_streak >= 5:
            warnings.append({
                'level': '🔴',
                'type': '连续未中奖',
                'strategy': strategy_name,
                'detail': f'连续{lose_streak}期未中奖'
            })
        
        # 2. ROI 连续 3 期下降
        roi_trend = []
        for period in recent[:3]:
            roi = period.get('roi', 0)
            roi_trend.append(roi)
        
        if len(roi_trend) == 3 and roi_trend[0] > roi_trend[1] > roi_trend[2]:
            warnings.append({
                'level': '🟡',
                'type': 'ROI 下降',
                'strategy': strategy_name,
                'detail': f'ROI 连续 3 期下降：{roi_trend}'
            })
        
        # 3. 单策略亏损超 80%
        total_roi = data.get('total_roi', 0)
        if total_roi < -80:
            warnings.append({
                'level': '🟠',
                'type': '严重亏损',
                'strategy': strategy_name,
                'detail': f'累计亏损{abs(total_roi):.1f}%'
            })
    
    return warnings


def main():
    """主函数"""
    print("=" * 60)
    print("🚨 彩票策略预警")
    print(f"【检查时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    stats = load_strategy_stats()
    
    if not stats:
        print("⚠️ 无统计数据，无法检查预警")
        return
    
    warnings = check_warnings(stats)
    
    if not warnings:
        print("\n🟢 策略运行正常，无预警")
    else:
        print(f"\n⚠️ 发现 {len(warnings)} 个预警\n")
        
        # 按级别排序
        level_order = {'🔴': 0, '🟠': 1, '🟡': 2, '🟢': 3}
        warnings.sort(key=lambda x: level_order.get(x['level'], 99))
        
        for w in warnings:
            print(f"{w['level']} {w['type']} - {w['strategy']}")
            print(f"   {w['detail']}\n")
    
    print("=" * 60)
    
    # 保存预警记录
    report = {
        'timestamp': datetime.now().isoformat(),
        'warnings': warnings,
        'status': 'warning' if warnings else 'normal'
    }
    
    report_file = Path('/root/.openclaw/workspace/lottery/reports/strategy_warning.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


if __name__ == "__main__":
    main()
