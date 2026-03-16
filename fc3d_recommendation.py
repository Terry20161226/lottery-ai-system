#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 推荐号码生成器
基于历史数据分析和策略权重
"""

import sys
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from fc3d_strategy import generate_fc3d_recommendation, analyze_fc3d_pattern


def load_fc3d_history():
    """加载福彩 3D 历史数据"""
    data_file = Path('/root/.openclaw/workspace/lottery/data/fc3d_history.json')
    if data_file.exists():
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('records', [])
    return []


def analyze_hot_cold(history, lookback=30):
    """分析冷热号"""
    if not history:
        return list(range(10)), list(range(10))
    
    # 统计近 30 期频率
    freq = Counter()
    for draw in history[:lookback]:
        for num in draw.get('numbers', []):
            freq[num] += 1
    
    # 热号（频率前 5）
    hot = [num for num, _ in freq.most_common(5)]
    
    # 冷号（频率后 5）
    cold = [num for num, _ in freq.most_common()[:-6:-1]]
    
    # 补齐到 10 个
    while len(hot) < 10:
        for i in range(10):
            if i not in hot:
                hot.append(i)
    while len(cold) < 10:
        for i in range(9, -1, -1):
            if i not in cold:
                cold.append(i)
    
    return hot, cold


def predict_pattern(history, lookback=20):
    """预测形态"""
    if len(history) < lookback:
        return "组六", 0.6
    
    # 统计近期形态
    patterns = []
    for draw in history[:lookback]:
        nums = draw.get('numbers', [])
        patterns.append(analyze_fc3d_pattern(nums))
    
    group6_count = patterns.count("组六")
    group3_count = patterns.count("组三")
    baozi_count = patterns.count("豹子")
    
    # 预测
    if group3_count > 8:
        return "组六", 0.7  # 组三过热，可能转组六
    elif group6_count > 16:
        return "组三", 0.4  # 组六过热，可能转组三
    else:
        return "组六", 0.65  # 默认组六


def generate_recommendations():
    """生成福彩 3D 推荐"""
    history = load_fc3d_history()
    
    if not history:
        print("❌ 无历史数据")
        return
    
    print(f"✅ 加载历史数据：{len(history)} 期")
    
    # 分析冷热号
    hot_nums, cold_nums = analyze_hot_cold(history)
    
    # 预测形态
    predicted_pattern, confidence = predict_pattern(history)
    
    print(f"\n📊 形态预测：{predicted_pattern} (置信度：{confidence:.0%})")
    print(f"🔥 热号：{hot_nums[:5]}")
    print(f"❄️ 冷号：{cold_nums[:5]}")
    
    # 生成推荐
    print(f"\n🎯 福彩 3D 推荐号码")
    print("=" * 50)
    
    # 策略 1：热号追踪
    hot_recs = generate_fc3d_recommendation("hot_number", 2)
    print("\n【热号追踪】")
    for i, rec in enumerate(hot_recs, 1):
        nums_str = ' '.join(str(n) for n in rec['numbers'])
        print(f"   第{i}注：{nums_str} (和值:{rec['sum']}, 形态:{rec['pattern']})")
    
    # 策略 2：冷号反弹
    cold_recs = generate_fc3d_recommendation("cold_number", 2)
    print("\n【冷号反弹】")
    for i, rec in enumerate(cold_recs, 1):
        nums_str = ' '.join(str(n) for n in rec['numbers'])
        print(f"   第{i}注：{nums_str} (和值:{rec['sum']}, 形态:{rec['pattern']})")
    
    # 策略 3：形态追踪
    pattern_recs = generate_fc3d_recommendation("pattern_follow", 2)
    print("\n【形态追踪】")
    for i, rec in enumerate(pattern_recs, 1):
        nums_str = ' '.join(str(n) for n in rec['numbers'])
        print(f"   第{i}注：{nums_str} (和值:{rec['sum']}, 形态:{rec['pattern']})")
    
    # 策略 4：均衡策略
    balanced_recs = generate_fc3d_recommendation("balanced", 2)
    print("\n【均衡策略】")
    for i, rec in enumerate(balanced_recs, 1):
        nums_str = ' '.join(str(n) for n in rec['numbers'])
        print(f"   第{i}注：{nums_str} (和值:{rec['sum']}, 形态:{rec['pattern']})")
    
    # 保存推荐
    report = {
        'timestamp': datetime.now().isoformat(),
        'model': 'fc3d_recommendation',
        'predicted_pattern': predicted_pattern,
        'confidence': confidence,
        'hot_nums': hot_nums[:5],
        'cold_nums': cold_nums[:5],
        'recommendations': {
            'hot': hot_recs,
            'cold': cold_recs,
            'pattern': pattern_recs,
            'balanced': balanced_recs
        }
    }
    
    report_file = Path('/root/.openclaw/workspace/lottery/reports/fc3d_recommendation.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已保存：reports/fc3d_recommendation.json")
    print("=" * 50)
    
    return report


if __name__ == "__main__":
    generate_recommendations()
