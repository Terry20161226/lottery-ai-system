#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快三彩票策略与中奖核对
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

# 快三奖级规则（标准奖金）
KS3_PRIZES = {
    "三同号单选": {"condition": "三同号单选", "amount": 240},      # 指定豹子号，如 111
    "三同号通选": {"condition": "三同号通选", "amount": 40},      # 所有豹子号
    "二同号单选": {"condition": "二同号单选", "amount": 80},      # 指定对子 + 单号，如 112
    "二同号复选": {"condition": "二同号复选", "amount": 15},      # 指定对子，第三号任意
    "三不同号": {"condition": "三不同号", "amount": 40},          # 三个号都不同
    "二不同号": {"condition": "二不同号", "amount": 8},           # 指定两个不同号
    "三连号通选": {"condition": "三连号通选", "amount": 10},      # 123/234/345/456
    "和值 4": {"condition": "和值", "value": 4, "amount": 80},
    "和值 5": {"condition": "和值", "value": 5, "amount": 40},
    "和值 6": {"condition": "和值", "value": 6, "amount": 25},
    "和值 7": {"condition": "和值", "value": 7, "amount": 16},
    "和值 8": {"condition": "和值", "value": 8, "amount": 12},
    "和值 9": {"condition": "和值", "value": 9, "amount": 10},
    "和值 10": {"condition": "和值", "value": 10, "amount": 9},
    "和值 11": {"condition": "和值", "value": 11, "amount": 9},
    "和值 12": {"condition": "和值", "value": 12, "amount": 10},
    "和值 13": {"condition": "和值", "value": 13, "amount": 12},
    "和值 14": {"condition": "和值", "value": 14, "amount": 16},
    "和值 15": {"condition": "和值", "value": 15, "amount": 25},
    "和值 16": {"condition": "和值", "value": 16, "amount": 40},
    "和值 17": {"condition": "和值", "value": 17, "amount": 80},
}

# 快三策略名称
KS3_STRATEGY_NAMES = {
    "hot_number": "热号追踪",
    "cold_number": "冷号反弹",
    "sum_trend": "和值趋势",
    "pattern_follow": "形态追踪",
    "balanced": "均衡策略",
}


def analyze_dice_pattern(numbers):
    """分析快三号码形态"""
    counter = Counter(numbers)
    values = list(counter.values())
    
    if len(counter) == 1:
        return "三同号"  # 豹子号
    elif len(counter) == 2:
        if 2 in values:
            return "二同号"  # 对子
        else:
            return "二不同号"
    elif len(counter) == 3:
        if max(numbers) - min(numbers) == 2:
            return "三连号"  # 连号
        else:
            return "三不同号"
    return "未知"


def check_ks3_prize(bet, draw):
    """
    核对快三中奖
    
    bet: 投注信息
        {
            "type": "和值|三同号单选|三同号通选|二同号单选|二同号复选|三不同号|二不同号|三连号通选",
            "numbers": [1, 2, 3],  # 投注号码
            "sum": 10,  # 和值投注时使用
        }
    
    draw: 开奖信息
        {
            "numbers": [1, 2, 3],
            "sum": 6,
            "pattern": "三不同号"
        }
    """
    bet_type = bet.get("type")
    bet_numbers = bet.get("numbers", [])
    bet_sum = bet.get("sum")
    
    draw_numbers = draw.get("numbers", [])
    draw_sum = sum(draw_numbers)
    draw_pattern = analyze_dice_pattern(draw_numbers)
    
    result = {"win": False, "prize_name": None, "prize_amount": 0}
    
    # 和值投注
    if bet_type == "和值":
        if bet_sum == draw_sum:
            prize_name = f"和值 {bet_sum}"
            prize_amount = KS3_PRIZES.get(prize_name, {}).get("amount", 0)
            result = {"win": True, "prize_name": prize_name, "prize_amount": prize_amount}
    
    # 三同号单选
    elif bet_type == "三同号单选":
        if len(set(bet_numbers)) == 1 and bet_numbers == draw_numbers:
            result = {"win": True, "prize_name": "三同号单选", "prize_amount": 240}
    
    # 三同号通选
    elif bet_type == "三同号通选":
        if draw_pattern == "三同号":
            result = {"win": True, "prize_name": "三同号通选", "prize_amount": 40}
    
    # 二同号单选
    elif bet_type == "二同号单选":
        if len(bet_numbers) == 3:
            bet_counter = Counter(bet_numbers)
            draw_counter = Counter(draw_numbers)
            if bet_counter == draw_counter:
                result = {"win": True, "prize_name": "二同号单选", "prize_amount": 80}
    
    # 二同号复选
    elif bet_type == "二同号复选":
        if len(bet_numbers) == 2 and bet_numbers[0] == bet_numbers[1]:
            pair = bet_numbers[0]
            if Counter(draw_numbers).get(pair, 0) >= 2:
                result = {"win": True, "prize_name": "二同号复选", "prize_amount": 15}
    
    # 三不同号
    elif bet_type == "三不同号":
        if len(set(bet_numbers)) == 3 and set(bet_numbers) == set(draw_numbers):
            result = {"win": True, "prize_name": "三不同号", "prize_amount": 40}
    
    # 二不同号
    elif bet_type == "二不同号":
        if len(bet_numbers) == 2 and bet_numbers[0] != bet_numbers[1]:
            if bet_numbers[0] in draw_numbers and bet_numbers[1] in draw_numbers:
                result = {"win": True, "prize_name": "二不同号", "prize_amount": 8}
    
    # 三连号通选
    elif bet_type == "三连号通选":
        if draw_pattern == "三连号":
            result = {"win": True, "prize_name": "三连号通选", "prize_amount": 10}
    
    return result


def generate_ks3_recommendation(strategy="balanced", count=5):
    """
    生成快三推荐号码
    
    strategy: 策略类型
        - hot_number: 热号追踪
        - cold_number: 冷号反弹
        - sum_trend: 和值趋势
        - pattern_follow: 形态追踪
        - balanced: 均衡策略
    """
    recommendations = []
    
    for _ in range(count):
        if strategy == "hot_number":
            # 热号：倾向于出现频率高的号码（简化版，随机生成）
            weights = [1.2, 1.1, 1.0, 1.0, 1.1, 1.2]  # 1 和 6 权重高
            numbers = random.choices([1, 2, 3, 4, 5, 6], weights=weights, k=3)
        
        elif strategy == "cold_number":
            # 冷号：倾向于出现频率低的号码（简化版）
            weights = [0.9, 1.0, 1.1, 1.1, 1.0, 0.9]  # 3 和 4 权重高
            numbers = random.choices([1, 2, 3, 4, 5, 6], weights=weights, k=3)
        
        elif strategy == "sum_trend":
            # 和值趋势：倾向于中间和值（9-12）
            target_sum = random.randint(9, 12)
            # 生成接近目标和值的号码
            numbers = [random.randint(1, 6) for _ in range(2)]
            third = max(1, min(6, target_sum - sum(numbers)))
            numbers.append(third)
        
        elif strategy == "pattern_follow":
            # 形态追踪：随机选择一种形态
            patterns = ["三同号", "二同号", "三不同号", "三连号"]
            pattern = random.choice(patterns)
            
            if pattern == "三同号":
                num = random.randint(1, 6)
                numbers = [num, num, num]
            elif pattern == "二同号":
                pair = random.randint(1, 6)
                single = random.choice([i for i in range(1, 7) if i != pair])
                numbers = [pair, pair, single]
                random.shuffle(numbers)
            elif pattern == "三连号":
                start = random.randint(1, 4)
                numbers = [start, start + 1, start + 2]
            else:
                numbers = random.sample(range(1, 7), 3)
        
        else:  # balanced
            # 均衡策略：完全随机
            numbers = [random.randint(1, 6) for _ in range(3)]
        
        recommendations.append({
            "numbers": numbers,
            "sum": sum(numbers),
            "pattern": analyze_dice_pattern(numbers),
            "strategy": strategy
        })
    
    return recommendations


def load_ks3_history():
    """加载快三历史数据"""
    filepath = os.path.join(DATA_DIR, "ks3_history.json")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"records": []}


def save_ks3_history(data):
    """保存快三历史数据"""
    filepath = os.path.join(DATA_DIR, "ks3_history.json")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_ks3_recommendations(recommendations):
    """保存快三推荐数据"""
    filepath = os.path.join(DATA_DIR, "ks3_recommend.json")
    data = {
        "generated_at": datetime.now().isoformat(),
        "lottery_type": "ks3",
        "recommendations": recommendations
    }
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def analyze_ks3_hot_cold(history, last_n=50):
    """分析快三热号冷号"""
    if not history or len(history) < last_n:
        return {"hot": [], "cold": []}
    
    # 统计每个号码出现次数
    counter = Counter()
    for record in history[:last_n]:
        numbers = record.get("numbers", [])
        counter.update(numbers)
    
    # 排序
    sorted_nums = sorted(counter.items(), key=lambda x: x[1], reverse=True)
    hot = [num for num, count in sorted_nums[:3]]
    cold = [num for num, count in sorted_nums[-3:]]
    
    return {"hot": hot, "cold": cold}


def main():
    """主函数 - 生成快三推荐"""
    print("=" * 50)
    print("快三彩票智能推荐")
    print("=" * 50)
    
    # 1. 加载历史数据
    print("\n📖 加载历史数据...")
    history_data = load_ks3_history()
    history = history_data.get("records", [])
    print(f"   历史期数：{len(history)}")
    
    # 2. 分析热号冷号
    print("\n📊 分析热号冷号...")
    analysis = analyze_ks3_hot_cold(history)
    print(f"   热号：{analysis.get('hot', [])}")
    print(f"   冷号：{analysis.get('cold', [])}")
    
    # 3. 生成各策略推荐
    print("\n💡 生成推荐号码...")
    all_recommendations = []
    
    for strategy in KS3_STRATEGY_NAMES.keys():
        recs = generate_ks3_recommendation(strategy, count=3)
        for rec in recs:
            rec["strategy_cn"] = KS3_STRATEGY_NAMES.get(strategy, strategy)
        all_recommendations.extend(recs)
        print(f"   {KS3_STRATEGY_NAMES.get(strategy, strategy)}: {len(recs)} 注")
    
    # 4. 保存推荐
    print("\n💾 保存推荐...")
    save_ks3_recommendations(all_recommendations)
    print(f"   已保存到：{DATA_DIR}/ks3_recommend.json")
    
    # 5. 显示部分推荐
    print("\n" + "=" * 50)
    print("📋 推荐预览（前 5 注）")
    print("=" * 50)
    for i, rec in enumerate(all_recommendations[:5], 1):
        nums = rec.get("numbers", [])
        print(f"{i}. [{', '.join(map(str, nums))}] 和值:{rec.get('sum')} 形态:{rec.get('pattern')} 策略:{rec.get('strategy_cn')}")
    
    print("\n" + "=" * 50)
    print(f"✅ 生成完成，共 {len(all_recommendations)} 注推荐")
    print("=" * 50)
    
    return all_recommendations


if __name__ == "__main__":
    main()
