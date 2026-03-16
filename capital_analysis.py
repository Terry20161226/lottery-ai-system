#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票资金曲线分析
生成资金报告，计算最大回撤，给出投注建议
"""

import json
from datetime import datetime
from pathlib import Path


def load_capital_data():
    """加载资金数据"""
    stats_file = Path('/root/.openclaw/workspace/lottery/stats/capital_stats.json')
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'history': [], 'initial': 10000}


def calculate_max_drawdown(history):
    """计算最大回撤"""
    if not history:
        return 0
    
    peak = history[0]
    max_dd = 0
    
    for value in history:
        if value > peak:
            peak = value
        drawdown = (peak - value) / peak * 100
        if drawdown > max_dd:
            max_dd = drawdown
    
    return max_dd


def get_risk_level(max_dd, current_roi):
    """获取风险级别"""
    if max_dd > 70 or current_roi < -70:
        return '🔴', '危险'
    elif max_dd > 50 or current_roi < -50:
        return '🟡', '关注'
    else:
        return '🟢', '安全'


def suggest_bet(current_capital, initial_capital, max_dd):
    """建议投注金额"""
    if current_capital < initial_capital * 0.3:
        return "⚠️ 建议暂停投注，等待资金恢复"
    elif current_capital < initial_capital * 0.5:
        return "💡 建议降低投注，每期¥2-4 元"
    elif max_dd > 50:
        return "💡 建议保守投注，每期¥4-6 元"
    else:
        return "✅ 可正常投注，每期¥6-10 元"


def main():
    """主函数"""
    print("=" * 60)
    print("💰 彩票资金曲线分析")
    print(f"【分析时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    data = load_capital_data()
    history = data.get('history', [])
    initial = data.get('initial', 10000)
    
    if not history:
        print("\n⚠️ 数据不足，需要更多历史数据")
        return
    
    current = history[-1] if history else initial
    total_roi = (current - initial) / initial * 100
    max_dd = calculate_max_drawdown(history)
    risk_level, risk_text = get_risk_level(max_dd, total_roi)
    bet_suggestion = suggest_bet(current, initial, max_dd)
    
    print(f"\n【初始资金】¥{initial:,}")
    print(f"【当前资金】¥{current:,}")
    print(f"【累计收益】¥{current - initial:,} ({total_roi:.1f}%)")
    print(f"【最大回撤】{max_dd:.1f}%")
    print(f"【风险级别】{risk_level} {risk_text}")
    print(f"\n【投注建议】{bet_suggestion}")
    
    # 资金趋势
    if len(history) >= 7:
        week_ago = history[-7]
        week_change = (current - week_ago) / week_ago * 100
        trend = "📈 上升" if week_change > 0 else "📉 下降"
        print(f"\n【周趋势】{trend} ({week_change:.1f}%)")
    
    print("\n" + "=" * 60)
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'initial': initial,
        'current': current,
        'roi': total_roi,
        'max_drawdown': max_dd,
        'risk_level': risk_level,
        'bet_suggestion': bet_suggestion
    }
    
    report_file = Path('/root/.openclaw/workspace/lottery/reports/capital_report.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


if __name__ == "__main__":
    main()
