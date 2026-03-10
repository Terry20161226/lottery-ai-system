#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
推送优化后的策略推荐
根据历史表现和形态分析，生成最佳推荐
"""

import os
import sys
import json
from datetime import datetime

# 添加路径
LOTTERY_DIR = "/root/.openclaw/workspace/lottery"
sys.path.insert(0, LOTTERY_DIR)

from lottery_storage import LotteryStorage
from lottery_strategies import LotteryStrategies
from strategy_optimizer import calculate_dynamic_weights, analyze_number_patterns

def load_json_file(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def generate_optimized_recommendations(lottery_type):
    """生成优化推荐"""
    storage = LotteryStorage()
    strategies = LotteryStrategies(storage)
    
    # 获取策略权重
    weights = calculate_dynamic_weights(lottery_type)
    
    # 获取形态分析
    patterns = analyze_number_patterns(lottery_type)
    
    # 获取所有策略
    all_strats = strategies.get_all_strategies(lottery_type)
    
    # 添加优化策略
    if lottery_type == "ssq":
        all_strats["sum_optimized"] = strategies.ssq_sum_optimized
        all_strats["span_optimized"] = strategies.ssq_span_optimized
    else:
        all_strats["sum_optimized"] = strategies.dlt_sum_optimized
        all_strats["span_optimized"] = strategies.dlt_span_optimized
    
    recommendations = []
    
    # 按权重排序策略
    sorted_strats = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    
    # 为高权重策略生成更多推荐
    for strat_id, weight in sorted_strats:
        if strat_id in all_strats:
            try:
                recs = all_strats[strat_id]()
                for rec in recs:
                    recommendations.append({
                        "strategy": strat_id,
                        "weight": weight,
                        "numbers": rec
                    })
            except Exception as e:
                print(f"⚠️ 策略 {strat_id} 生成失败：{e}")
    
    return recommendations, weights, patterns

def format_recommendations(lottery_type, recommendations, weights, patterns):
    """格式化推荐输出"""
    lottery_name = "双色球" if lottery_type == "ssq" else "大乐透"
    
    output = []
    output.append(f"🎯 {lottery_name} 优化推荐")
    output.append("=" * 50)
    output.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    output.append("")
    
    # 形态分析摘要
    if patterns:
        output.append("📐 形态参考")
        if lottery_type == "ssq":
            output.append(f"   和值范围：{patterns['sum_range']['min']}-{patterns['sum_range']['max']} (平均{patterns['sum_range']['avg']})")
            output.append(f"   跨度范围：{patterns['span_range']['min']}-{patterns['span_range']['max']} (平均{patterns['span_range']['avg']})")
        else:
            output.append(f"   和值范围：{patterns['sum_range']['min']}-{patterns['sum_range']['max']} (平均{patterns['sum_range']['avg']})")
            output.append(f"   跨度范围：{patterns['span_range']['min']}-{patterns['span_range']['max']} (平均{patterns['span_range']['avg']})")
        output.append(f"   常见奇偶比：{patterns.get('most_common_ratio', 'N/A')}")
        output.append("")
    
    # 策略权重
    output.append("🏆 策略权重")
    sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    for i, (strat_id, weight) in enumerate(sorted_weights[:5], 1):
        icon = "🔥" if weight > 1.0 else "❄️" if weight < 1.0 else "⚖️"
        strat_name = strat_id.replace("_", " ").title()
        output.append(f"   {i}. {icon} {strat_name}: {weight}")
    output.append("")
    
    # 推荐号码（按权重分组）
    output.append("🎫 推荐号码")
    output.append("-" * 50)
    
    # 高权重推荐（权重 >= 1.5）
    high_weight_recs = [r for r in recommendations if r["weight"] >= 1.5]
    if high_weight_recs:
        output.append("\n🔥 高权重推荐:")
        for i, rec in enumerate(high_weight_recs[:5], 1):
            strat_name = rec["strategy"].replace("_", " ").title()
            if lottery_type == "ssq":
                reds = " ".join(f"{n:02d}" for n in rec["numbers"]["red"])
                blue = f"{rec['numbers']['blue']:02d}"
                output.append(f"   {i}. [{strat_name}] 红球：{reds} + 蓝球：{blue}")
            else:
                fronts = " ".join(f"{n:02d}" for n in rec["numbers"]["front"])
                backs = " ".join(f"{n:02d}" for n in rec["numbers"]["back"])
                output.append(f"   {i}. [{strat_name}] 前区：{fronts} + 后区：{backs}")
    
    # 普通权重推荐
    normal_weight_recs = [r for r in recommendations if 1.0 <= r["weight"] < 1.5]
    if normal_weight_recs:
        output.append("\n⚖️ 普通推荐:")
        for i, rec in enumerate(normal_weight_recs[:5], 1):
            strat_name = rec["strategy"].replace("_", " ").title()
            if lottery_type == "ssq":
                reds = " ".join(f"{n:02d}" for n in rec["numbers"]["red"])
                blue = f"{rec['numbers']['blue']:02d}"
                output.append(f"   {i}. [{strat_name}] 红球：{reds} + 蓝球：{blue}")
            else:
                fronts = " ".join(f"{n:02d}" for n in rec["numbers"]["front"])
                backs = " ".join(f"{n:02d}" for n in rec["numbers"]["back"])
                output.append(f"   {i}. [{strat_name}] 前区：{fronts} + 后区：{backs}")
    
    output.append("")
    output.append("=" * 50)
    output.append("⚠️ 彩票有风险，购买需谨慎")
    
    return "\n".join(output)

def main():
    print("🚀 生成优化推荐")
    print("=" * 50)
    
    for lottery_type in ["ssq", "dlt"]:
        print(f"\n{lottery_type.upper()}:")
        recs, weights, patterns = generate_optimized_recommendations(lottery_type)
        print(f"   生成 {len(recs)} 注推荐")
        print(f"   策略权重：{len(weights)} 种")
    
    print("\n✅ 完成！")

if __name__ == "__main__":
    main()
