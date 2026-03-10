#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 彩票策略与推荐
"""

import os
import json
import random
from datetime import datetime
from collections import Counter

# 配置
LOTTERY_DIR = "/root/.openclaw/workspace/lottery"
DATA_DIR = os.path.join(LOTTERY_DIR, "data")
STATS_DIR = os.path.join(LOTTERY_DIR, "stats")

# 福彩 3D 奖级规则
FC3D_PRIZES = {
    "直选": {"amount": 1040},
    "组三": {"amount": 346},
    "组六": {"amount": 173},
}

# 福彩 3D 策略名称
FC3D_STRATEGY_NAMES = {
    "hot_number": "热号追踪",
    "cold_number": "冷号反弹",
    "sum_trend": "和值趋势",
    "pattern_follow": "形态追踪",
    "balanced": "均衡策略",
}


def analyze_fc3d_pattern(numbers):
    """分析福彩 3D 号码形态"""
    counter = Counter(numbers)
    values = list(counter.values())
    
    if len(counter) == 1:
        return "豹子"
    elif len(counter) == 2:
        return "组三"
    elif len(counter) == 3:
        return "组六"
    return "未知"


def generate_fc3d_recommendation(strategy="balanced", count=5):
    """
    生成福彩 3D 推荐号码（0-9）
    """
    recommendations = []
    
    for _ in range(count):
        if strategy == "hot_number":
            # 热号：倾向于出现频率高的号码
            weights = [1.0, 1.3, 1.1, 1.0, 0.8, 1.2, 1.1, 1.4, 1.3, 1.2]
            numbers = random.choices(range(10), weights=weights, k=3)
        
        elif strategy == "cold_number":
            # 冷号：倾向于出现频率低的号码
            weights = [1.2, 0.8, 1.0, 1.2, 1.4, 0.9, 1.0, 0.7, 0.8, 0.9]
            numbers = random.choices(range(10), weights=weights, k=3)
        
        elif strategy == "sum_trend":
            # 和值趋势：倾向于中间和值（9-14）
            target_sum = random.randint(9, 14)
            numbers = [random.randint(0, 9) for _ in range(2)]
            third = max(0, min(9, target_sum - sum(numbers)))
            numbers.append(third)
        
        elif strategy == "pattern_follow":
            # 形态追踪
            patterns = ["豹子", "组三", "组六"]
            pattern = random.choice(patterns)
            
            if pattern == "豹子":
                num = random.randint(0, 9)
                numbers = [num, num, num]
            elif pattern == "组三":
                pair = random.randint(0, 9)
                single = random.choice([i for i in range(10) if i != pair])
                numbers = [pair, pair, single]
                random.shuffle(numbers)
            else:
                numbers = random.sample(range(10), 3)
        
        else:  # balanced
            numbers = [random.randint(0, 9) for _ in range(3)]
        
        recommendations.append({
            "numbers": numbers,
            "sum": sum(numbers),
            "pattern": analyze_fc3d_pattern(numbers),
            "strategy": strategy
        })
    
    return recommendations


def load_fc3d_history():
    """加载福彩 3D 历史数据"""
    filepath = os.path.join(DATA_DIR, "fc3d_history.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"records": []}


def save_fc3d_recommendations(recommendations):
    """保存福彩 3D 推荐数据"""
    filepath = os.path.join(DATA_DIR, "fc3d_recommend.json")
    data = {
        "generated_at": datetime.now().isoformat(),
        "lottery_type": "fc3d",
        "recommendations": recommendations
    }
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   文件：{filepath}")


def analyze_fc3d_omission(history, last_n=100):
    """
    分析福彩 3D 遗漏值（每个号码多少期未出现）
    遗漏值 = 从最新一期开始，该号码多少期没有出现
    """
    if not history or len(history) == 0:
        return {str(i): 0 for i in range(10)}
    
    omission = {}
    
    # 从最新一期开始往前统计，计算每个号码连续多少期未出现
    for num in range(10):
        num_str = str(num)
        count = 0
        for record in history[:last_n]:
            numbers = record.get("numbers", [])
            if num in numbers:
                # 号码出现，停止计数
                break
            else:
                # 号码未出现，计数 +1
                count += 1
        omission[num_str] = count
    
    return omission


def analyze_fc3d_span(history, last_n=50):
    """
    分析和值跨度（最大值 - 最小值）
    """
    if not history or len(history) == 0:
        return {"avg_span": 0, "max_span": 0, "min_span": 0, "spans": []}
    
    spans = []
    for record in history[:last_n]:
        numbers = record.get("numbers", [])
        if len(numbers) == 3:
            span = max(numbers) - min(numbers)
            spans.append(span)
    
    if not spans:
        return {"avg_span": 0, "max_span": 0, "min_span": 0, "spans": []}
    
    return {
        "avg_span": sum(spans) / len(spans),
        "max_span": max(spans),
        "min_span": min(spans),
        "spans": spans,
        "span_counts": {i: spans.count(i) for i in range(10)}
    }


def analyze_fc3d_pattern_probability(history, last_n=100):
    """
    分析形态出现概率（豹子/组三/组六）
    """
    if not history or len(history) == 0:
        return {"豹子": 0, "组三": 0, "组六": 0}
    
    counter = Counter()
    for record in history[:last_n]:
        numbers = record.get("numbers", [])
        pattern = analyze_fc3d_pattern(numbers)
        counter[pattern] += 1
    
    total = sum(counter.values())
    if total == 0:
        return {"豹子": 0, "组三": 0, "组六": 0}
    
    return {
        "豹子": counter["豹子"] / total * 100,
        "组三": counter["组三"] / total * 100,
        "组六": counter["组六"] / total * 100,
        "counts": dict(counter)
    }


def analyze_fc3d_hot_cold(history, last_n=50):
    """分析福彩 3D 热号冷号（0-9）"""
    if not history or len(history) == 0:
        return {"hot": [], "cold": []}
    
    counter = Counter()
    actual_count = min(len(history), last_n)
    for record in history[:actual_count]:
        numbers = record.get("numbers", [])
        counter.update(numbers)
    
    if not counter:
        return {"hot": [], "cold": []}
    
    sorted_nums = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    hot = [num for num, count in sorted_nums[:3]]
    cold = [num for num, count in sorted_nums[-3:]]
    
    return {"hot": hot, "cold": cold, "stats": dict(counter)}


def main():
    """主函数 - 生成福彩 3D 推荐（增强版）"""
    print("=" * 60)
    print("福彩 3D 智能推荐（增强版）")
    print("=" * 60)
    
    # 1. 加载历史数据
    print("\n📖 加载历史数据...")
    history_data = load_fc3d_history()
    history = history_data.get("records", [])
    print(f"   历史期数：{len(history)}")
    
    # 2. 热号冷号分析
    print("\n📊 热号冷号分析...")
    hot_cold = analyze_fc3d_hot_cold(history)
    print(f"   🔥 热号：{hot_cold.get('hot', [])}")
    print(f"   ❄️ 冷号：{hot_cold.get('cold', [])}")
    
    # 3. 遗漏值分析（新增）
    print("\n🔍 遗漏值分析...")
    omission = analyze_fc3d_omission(history)
    sorted_omission = sorted(omission.items(), key=lambda x: x[1], reverse=True)
    max_omission = sorted_omission[:3]
    min_omission = sorted_omission[-3:]
    print(f"   ⏳ 最大遗漏：{max_omission}")
    print(f"   ⏱️ 最小遗漏：{min_omission}")
    
    # 4. 和值跨度分析（新增）
    print("\n📏 和值跨度分析...")
    span_stats = analyze_fc3d_span(history)
    print(f"   平均跨度：{span_stats.get('avg_span', 0):.1f}")
    print(f"   最大跨度：{span_stats.get('max_span', 0)}")
    print(f"   最小跨度：{span_stats.get('min_span', 0)}")
    
    # 5. 形态概率分析（新增）
    print("\n🎲 形态概率分析...")
    pattern_prob = analyze_fc3d_pattern_probability(history)
    print(f"   豹子概率：{pattern_prob.get('豹子', 0):.1f}%")
    print(f"   组三概率：{pattern_prob.get('组三', 0):.1f}%")
    print(f"   组六概率：{pattern_prob.get('组六', 0):.1f}%")
    
    # 6. 生成各策略推荐
    print("\n💡 生成推荐号码...")
    all_recommendations = []
    
    for strategy in FC3D_STRATEGY_NAMES.keys():
        recs = generate_fc3d_recommendation(strategy, count=3)
        for rec in recs:
            rec["strategy_cn"] = FC3D_STRATEGY_NAMES.get(strategy, strategy)
        all_recommendations.extend(recs)
        print(f"   {FC3D_STRATEGY_NAMES.get(strategy, strategy)}: {len(recs)} 注")
    
    # 7. 保存推荐
    print("\n💾 保存推荐...")
    save_fc3d_recommendations(all_recommendations)
    
    # 8. 显示推荐
    print("\n" + "=" * 60)
    print("📋 推荐预览（前 5 注）")
    print("=" * 60)
    for i, rec in enumerate(all_recommendations[:5], 1):
        nums = rec.get("numbers", [])
        print(f"{i}. [{', '.join(map(str, nums))}] 和值:{rec.get('sum')} 形态:{rec.get('pattern')} 策略:{rec.get('strategy_cn')}")
    
    # 9. 保存完整分析报告
    report_file = "/root/.openclaw/workspace/lottery/stats/fc3d_analysis_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("福彩 3D 分析报告\n")
        f.write(f"生成时间：{datetime.now().isoformat()}\n")
        f.write(f"历史期数：{len(history)}\n\n")
        f.write(f"热号：{hot_cold.get('hot', [])}\n")
        f.write(f"冷号：{hot_cold.get('cold', [])}\n\n")
        f.write(f"遗漏值分析:\n")
        for num, val in sorted_omission:
            f.write(f"   号码{num}: {val}期未出现\n")
        f.write(f"\n和值跨度:\n")
        f.write(f"   平均：{span_stats.get('avg_span', 0):.1f}\n")
        f.write(f"   最大：{span_stats.get('max_span', 0)}\n")
        f.write(f"   最小：{span_stats.get('min_span', 0)}\n\n")
        f.write(f"形态概率:\n")
        f.write(f"   豹子：{pattern_prob.get('豹子', 0):.1f}%\n")
        f.write(f"   组三：{pattern_prob.get('组三', 0):.1f}%\n")
        f.write(f"   组六：{pattern_prob.get('组六', 0):.1f}%\n")
    
    print(f"\n📄 分析报告：{report_file}")
    print("\n" + "=" * 60)
    print(f"✅ 生成完成，共 {len(all_recommendations)} 注推荐")
    print("=" * 60)
    
    return all_recommendations


if __name__ == "__main__":
    main()
