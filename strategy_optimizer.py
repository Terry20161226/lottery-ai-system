#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略优化器 - 基于历史表现动态调整策略权重
"""

import os
import json
from datetime import datetime
from pathlib import Path

# 配置
LOTTERY_DIR = "/root/.openclaw/workspace/lottery"
STATS_DIR = os.path.join(LOTTERY_DIR, "stats")
CONFIG_DIR = os.path.join(LOTTERY_DIR, "config")

def load_json_file(filepath):
    """加载 JSON 文件"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json_file(filepath, data):
    """保存 JSON 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_strategy_weights(lottery_type):
    """获取策略权重配置"""
    filepath = os.path.join(CONFIG_DIR, f"{lottery_type}_strategy_weights.json")
    default_weights = {
        "balanced": 1.0,
        "hot_tracking": 1.0,
        "cold_rebound": 1.0,
        "odd_even": 1.0,
        "zone_distribution": 1.0,
        "consecutive": 1.0,
        "warm_balance": 1.0
    }
    
    if os.path.exists(filepath):
        data = load_json_file(filepath)
        return data.get("weights", default_weights)
    return default_weights

def calculate_dynamic_weights(lottery_type):
    """
    根据历史表现计算动态权重
    
    规则：
    - ROI 前 3 名：权重 1.5
    - ROI 中等：权重 1.0
    - ROI 后 2 名：权重 0.5
    - 新策略（无数据）：权重 1.0
    """
    stats_file = os.path.join(STATS_DIR, f"{lottery_type}_strategy_stats.json")
    
    if not os.path.exists(stats_file):
        return get_strategy_weights(lottery_type)
    
    stats = load_json_file(stats_file)
    strategies = stats.get("strategies", {})
    
    if not strategies:
        return get_strategy_weights(lottery_type)
    
    # 按 ROI 排序
    sorted_strats = sorted(
        strategies.items(),
        key=lambda x: x[1].get("roi", -100),
        reverse=True
    )
    
    weights = {}
    total_strats = len(sorted_strats)
    
    for i, (strat_id, data) in enumerate(sorted_strats):
        # 前 30% 高权重
        if i < total_strats * 0.3:
            weights[strat_id] = 1.5
        # 后 20% 低权重
        elif i >= total_strats * 0.8:
            weights[strat_id] = 0.5
        else:
            weights[strat_id] = 1.0
    
    # 保存权重配置
    weight_config = {
        "lottery_type": lottery_type,
        "last_update": datetime.now().isoformat(),
        "total_draws": stats.get("total_draws", 0),
        "weights": weights
    }
    
    filepath = os.path.join(CONFIG_DIR, f"{lottery_type}_strategy_weights.json")
    save_json_file(filepath, weight_config)
    
    return weights

def analyze_number_patterns(lottery_type, recent_periods=30):
    """
    分析近期开奖号码形态
    
    返回：
    - 和值范围
    - 跨度范围
    - 奇偶比趋势
    - 连号出现频率
    """
    if lottery_type == "ssq":
        filepath = os.path.join(LOTTERY_DIR, "data", "ssq_history.json")
    else:
        filepath = os.path.join(LOTTERY_DIR, "data", "dlt_history.json")
    
    if not os.path.exists(filepath):
        return None
    
    data = load_json_file(filepath)
    records = data.get("records", [])[:recent_periods]
    
    if not records:
        return None
    
    patterns = {
        "sum_range": {"min": 999, "max": 0, "avg": 0},
        "span_range": {"min": 999, "max": 0, "avg": 0},
        "odd_even_ratio": [],
        "consecutive_count": 0
    }
    
    sum_values = []
    span_values = []
    
    for record in records:
        if lottery_type == "ssq":
            nums = record.get("numbers", {}).get("red", [])
        else:
            nums = record.get("numbers", {}).get("front", [])
        
        if not nums:
            continue
        
        # 和值
        sum_val = sum(nums)
        sum_values.append(sum_val)
        patterns["sum_range"]["min"] = min(patterns["sum_range"]["min"], sum_val)
        patterns["sum_range"]["max"] = max(patterns["sum_range"]["max"], sum_val)
        
        # 跨度
        span_val = max(nums) - min(nums)
        span_values.append(span_val)
        patterns["span_range"]["min"] = min(patterns["span_range"]["min"], span_val)
        patterns["span_range"]["max"] = max(patterns["span_range"]["max"], span_val)
        
        # 奇偶比
        odd_count = len([n for n in nums if n % 2 == 1])
        even_count = len(nums) - odd_count
        patterns["odd_even_ratio"].append(f"{odd_count}:{even_count}")
        
        # 连号检测
        sorted_nums = sorted(nums)
        for i in range(len(sorted_nums) - 1):
            if sorted_nums[i + 1] - sorted_nums[i] == 1:
                patterns["consecutive_count"] += 1
                break
    
    # 计算平均值
    if sum_values:
        patterns["sum_range"]["avg"] = round(sum(sum_values) / len(sum_values))
    if span_values:
        patterns["span_range"]["avg"] = round(sum(span_values) / len(span_values))
    
    # 统计最常见的奇偶比
    if patterns["odd_even_ratio"]:
        from collections import Counter
        ratio_counter = Counter(patterns["odd_even_ratio"])
        patterns["most_common_ratio"] = ratio_counter.most_common(1)[0][0]
    
    patterns["consecutive_frequency"] = round(patterns["consecutive_count"] / len(records) * 100, 1)
    
    return patterns

def generate_optimized_recommendation(lottery_type, base_recommendations):
    """
    基于权重生成优化推荐
    
    根据策略权重调整推荐数量：
    - 高权重策略：生成更多推荐
    - 低权重策略：生成较少推荐
    """
    weights = get_strategy_weights(lottery_type)
    
    optimized = []
    total_weight = sum(weights.values())
    
    # 计算每种策略应生成的注数
    total_notes = len(base_recommendations)
    
    for strategy, recs in base_recommendations.items():
        weight = weights.get(strategy, 1.0)
        note_count = max(1, round(total_notes * weight / total_weight))
        
        for i in range(min(note_count, len(recs))):
            optimized.append({
                "strategy": strategy,
                "weight": weight,
                "numbers": recs[i]
            })
    
    return optimized

def generate_pattern_report(lottery_type):
    """生成形态分析报告"""
    patterns = analyze_number_patterns(lottery_type)
    
    if not patterns:
        return "⏳ 暂无足够数据生成形态分析"
    
    lottery_name = "双色球" if lottery_type == "ssq" else "大乐透"
    
    report = []
    report.append(f"📐 {lottery_name} 形态分析（近 30 期）")
    report.append("=" * 50)
    report.append("")
    report.append("📊 和值分析")
    report.append(f"   范围：{patterns['sum_range']['min']} - {patterns['sum_range']['max']}")
    report.append(f"   平均：{patterns['sum_range']['avg']}")
    report.append("")
    report.append("📏 跨度分析")
    report.append(f"   范围：{patterns['span_range']['min']} - {patterns['span_range']['max']}")
    report.append(f"   平均：{patterns['span_range']['avg']}")
    report.append("")
    report.append("⚖️ 奇偶比")
    report.append(f"   最常见：{patterns.get('most_common_ratio', 'N/A')}")
    report.append("")
    report.append("🔗 连号频率")
    report.append(f"   出现率：{patterns['consecutive_frequency']}%")
    
    return "\n".join(report)

def main():
    print("🚀 策略优化器")
    print("=" * 50)
    
    # 1. 计算动态权重
    print("\n📊 计算策略权重...")
    
    for lottery_type in ["ssq", "dlt"]:
        weights = calculate_dynamic_weights(lottery_type)
        lottery_name = "双色球" if lottery_type == "ssq" else "大乐透"
        
        print(f"\n{lottery_name}:")
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        for strat_id, weight in sorted_weights:
            icon = "🔥" if weight > 1.0 else "❄️" if weight < 1.0 else "⚖️"
            print(f"   {icon} {strat_id}: {weight}")
    
    # 2. 形态分析
    print("\n" + "=" * 50)
    print("📐 形态分析")
    print("=" * 50)
    
    for lottery_type in ["ssq", "dlt"]:
        print("\n" + generate_pattern_report(lottery_type))
    
    print("\n" + "=" * 50)
    print("✅ 优化完成！权重配置已保存")

if __name__ == "__main__":
    main()
