#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票形态趋势预测
预测下周可能出现的形态
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter


def load_history(lottery_type='ssq'):
    """加载历史数据"""
    data_file = Path(f'/root/.openclaw/workspace/lottery/data/{lottery_type}_history.json')
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('records', [])[:50]  # 近 50 期
    return []


def analyze_consecutive(history):
    """分析连号趋势"""
    consecutive_count = 0
    for draw in history[:20]:
        numbers = draw.get('red', []) or draw.get('front', [])
        if len(numbers) > 1:
            numbers = sorted([int(n) for n in numbers])
            for i in range(len(numbers) - 1):
                if numbers[i+1] - numbers[i] == 1:
                    consecutive_count += 1
                    break
    
    rate = consecutive_count / min(20, len(history)) * 100
    
    if rate > 60:
        return '高', '连号频繁，建议关注'
    elif rate > 40:
        return '中', '连号正常'
    else:
        return '低', '连号较少，可能反弹'


def analyze_same_tail(history):
    """分析同尾号趋势"""
    same_tail_count = 0
    for draw in history[:20]:
        numbers = draw.get('red', []) or draw.get('front', [])
        if len(numbers) > 2:
            tails = [int(n) % 10 for n in numbers]
            if len(tails) != len(set(tails)):
                same_tail_count += 1
    
    rate = same_tail_count / min(20, len(history)) * 100
    
    if rate > 70:
        return '高', '同尾号频繁'
    elif rate > 50:
        return '中', '同尾号正常'
    else:
        return '低', '同尾号较少'


def predict_sum_range(history):
    """预测和值范围"""
    sums = []
    for draw in history[:30]:
        numbers = draw.get('red', []) or draw.get('front', [])
        s = sum(int(n) for n in numbers)
        sums.append(s)
    
    if not sums:
        return '90-120', '数据不足'
    
    avg = sum(sums) / len(sums)
    std = (sum((x - avg) ** 2 for x in sums) / len(sums)) ** 0.5
    
    low = int(avg - std)
    high = int(avg + std)
    
    return f'{low}-{high}', f'平均和值{avg:.0f}'


def analyze_hot_cold(history):
    """分析冷热号转换"""
    freq = Counter()
    for draw in history[:30]:
        numbers = draw.get('red', []) or draw.get('front', [])
        for n in numbers:
            freq[int(n)] += 1
    
    # 热号（出现 8 次以上）
    hot = [n for n, c in freq.most_common(10) if c >= 8]
    # 冷号（出现 3 次以下）
    cold = [n for n, c in freq.items() if c <= 3]
    
    return hot[:5], cold[:5]


def analyze_odd_even(history):
    """分析奇偶比"""
    odd_counts = []
    for draw in history[:30]:
        numbers = draw.get('red', []) or draw.get('front', [])
        odd = sum(1 for n in numbers if int(n) % 2 == 1)
        odd_counts.append(odd)
    
    avg_odd = sum(odd_counts) / len(odd_counts) if odd_counts else 3
    
    if avg_odd > 3.5:
        return '3:2', '奇数偏多，建议关注偶数'
    elif avg_odd < 2.5:
        return '2:3', '偶数偏多，建议关注奇数'
    else:
        return '3:2', '奇偶均衡'


def main():
    """主函数"""
    print("=" * 60)
    print("📈 彩票形态趋势预测")
    print(f"【预测时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"【预测周期】下周 ({(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')})")
    print("=" * 60)
    
    # 双色球
    print("\n【双色球预测】")
    ssq_history = load_history('ssq')
    if ssq_history:
        consec_level, consec_desc = analyze_consecutive(ssq_history)
        print(f"  连号趋势：{consec_level} - {consec_desc}")
        
        tail_level, tail_desc = analyze_same_tail(ssq_history)
        print(f"  同尾趋势：{tail_level} - {tail_desc}")
        
        sum_range, sum_desc = predict_sum_range(ssq_history)
        print(f"  和值范围：{sum_range} ({sum_desc})")
        
        hot, cold = analyze_hot_cold(ssq_history)
        print(f"  热号：{hot}")
        print(f"  冷号：{cold} (可能反弹)")
        
        odd_even, odd_desc = analyze_odd_even(ssq_history)
        print(f"  奇偶建议：{odd_even} - {odd_desc}")
    else:
        print("  ⚠️ 数据不足")
    
    # 大乐透
    print("\n【大乐透预测】")
    dlt_history = load_history('dlt')
    if dlt_history:
        consec_level, consec_desc = analyze_consecutive(dlt_history)
        print(f"  连号趋势：{consec_level} - {consec_desc}")
        
        tail_level, tail_desc = analyze_same_tail(dlt_history)
        print(f"  同尾趋势：{tail_level} - {tail_desc}")
        
        sum_range, sum_desc = predict_sum_range(dlt_history)
        print(f"  和值范围：{sum_range} ({sum_desc})")
        
        hot, cold = analyze_hot_cold(dlt_history)
        print(f"  热号：{hot}")
        print(f"  冷号：{cold} (可能反弹)")
    else:
        print("  ⚠️ 数据不足")
    
    print("\n" + "=" * 60)
    print("💡 提示：预测仅供参考，实际开奖是随机的")
    print("=" * 60)
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'period': 'next_week',
        'ssq': {
            'consecutive': consec_level if ssq_history else None,
            'same_tail': tail_level if ssq_history else None,
            'sum_range': sum_range if ssq_history else None
        } if ssq_history else None
    }
    
    report_file = Path('/root/.openclaw/workspace/lottery/reports/trend_prediction.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    return report


if __name__ == "__main__":
    main()
