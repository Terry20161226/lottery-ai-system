#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 动态策略调整系统 V2
改进版：更智能的调整逻辑 + 形态预测
"""

import json
from collections import Counter
from datetime import datetime

DATA_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_history.json"
STRATEGY_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_dynamic_strategy.json"


def load_history():
    """加载福彩 3D 历史数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f).get('records', [])


def load_strategy_config():
    """加载策略配置"""
    try:
        with open(STRATEGY_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 确保关键字段存在
            if 'trend_weight' not in config:
                config['trend_weight'] = 0.2
            if 'hot_weight' not in config:
                config['hot_weight'] = 0.5
            if 'cold_weight' not in config:
                config['cold_weight'] = 0.3
            return config
    except:
        return {
            "version": "v2.0",
            "base_bet": {"group6": 3, "group3": 2, "direct": 1},
            "hot_weight": 0.5,
            "cold_weight": 0.3,
            "trend_weight": 0.2,
            "performance": {"total_periods": 0, "wins": 0},
            "adjustments": []
        }


def analyze_pattern_trend(history, last_n=20):
    """分析形态趋势"""
    patterns = []
    for draw in history[:last_n]:
        nums = draw['numbers']
        counter = Counter(nums)
        if len(counter) == 1:
            patterns.append("豹子")
        elif len(counter) == 2:
            patterns.append("组三")
        else:
            patterns.append("组六")
    
    # 统计近期形态
    group6_count = patterns.count("组六")
    group3_count = patterns.count("组三")
    
    # 预测下期形态
    if group3_count > 8:  # 组三过热，可能转组六
        return "组六", 0.7
    elif group6_count > 16:  # 组六过热，可能转组三
        return "组三", 0.4
    else:
        return "组六", 0.65  # 默认组六概率高


def get_dynamic_nums(history, config, lookback=30):
    """动态选号"""
    candidates = []
    for num in range(10):
        # 频率
        freq = sum(1 for d in history[:lookback] if num in d['numbers'])
        # 遗漏
        omission = 0
        for d in history[:lookback]:
            if num in d['numbers']:
                break
            omission += 1
        # 近期趋势
        recent = sum(1 for d in history[:10] if num in d['numbers'])
        
        score = (
            freq * config['hot_weight'] +
            omission * config['cold_weight'] +
            recent * config['trend_weight']
        )
        candidates.append((num, score))
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    return [n[0] for n in candidates]


def generate_smart_bets(nums, bet_config, predicted_pattern):
    """智能生成投注"""
    from itertools import combinations
    
    bets = []
    
    # 根据预测形态调整
    if predicted_pattern == "组三":
        # 增加组三投注
        bet_config['group3'] = min(4, bet_config['group3'] + 1)
    
    # 组六
    for combo in combinations(nums[:6], 3):
        bets.append({'type': '组六', 'numbers': list(combo), 'cost': 2})
        if len([b for b in bets if b['type'] == '组六']) >= bet_config['group6']:
            break
    
    # 组三
    group3_count = 0
    for num in nums[:4]:
        for other in nums[4:7]:
            if num != other:
                bets.append({'type': '组三', 'numbers': [num, num, other], 'cost': 2})
                group3_count += 1
                if group3_count >= bet_config['group3']:
                    break
        if group3_count >= bet_config['group3']:
            break
    
    # 直选
    if bet_config.get('direct', 0) > 0:
        bets.append({'type': '直选', 'numbers': nums[:3], 'cost': 2})
    
    return bets


def adjust_strategy(config, recent_results):
    """智能调整策略"""
    if len(recent_results) < 10:
        return "观察期", config
    
    last_10 = recent_results[-10:]
    roi_10 = (sum(r['prize'] for r in last_10) - sum(r['invested'] for r in last_10)) / max(1, sum(r['invested'] for r in last_10)) * 100
    
    adjustment = {"date": datetime.now().isoformat(), "roi_10": roi_10, "action": ""}
    
    if roi_10 < -60:
        config['hot_weight'] = min(0.7, config['hot_weight'] + 0.1)
        config['cold_weight'] = max(0.2, config['cold_weight'] - 0.1)
        config['base_bet']['direct'] = 1  # 恢复直选博高奖金
        adjustment['action'] = "严重亏损 - 增加热号 + 恢复直选"
    
    elif roi_10 < -30:
        config['hot_weight'] = min(0.6, config['hot_weight'] + 0.05)
        adjustment['action'] = "中度亏损 - 微调热号权重"
    
    elif roi_10 > 20:
        config['base_bet']['group6'] = min(4, config['base_bet']['group6'] + 1)
        adjustment['action'] = "盈利 - 适度增加组六"
    
    else:
        adjustment['action'] = "稳定 - 保持当前"
    
    config['adjustments'].append(adjustment)
    if len(config['adjustments']) > 10:
        config['adjustments'] = config['adjustments'][-10:]
    
    return adjustment['action'], config


def run_dynamic_v2(periods=100):
    """运行 V2 动态策略"""
    print("=" * 70)
    print("福彩 3D 动态策略调整系统 V2")
    print("=" * 70)
    
    history = load_history()
    config = load_strategy_config()
    
    print(f"\n📖 历史数据：{len(history)} 期")
    print(f"   策略版本：{config['version']}")
    print(f"   初始配置：组六{config['base_bet']['group6']} + 组三{config['base_bet']['group3']} + 直选{config['base_bet'].get('direct', 0)}")
    
    recent = history[:periods][::-1]
    results = []
    
    initial_capital = 10000
    capital = initial_capital
    total_invested = 0
    total_prize = 0
    
    print("\n📊 开始执行...")
    
    for i, draw in enumerate(recent):
        draw_numbers = draw['numbers']
        past_data = history[max(0, i-30):i] if i > 0 else []
        
        # 形态预测
        if len(past_data) >= 10:
            predicted_pattern, confidence = analyze_pattern_trend(past_data)
        else:
            predicted_pattern, confidence = "组六", 0.65
        
        # 动态选号
        if len(past_data) >= 10:
            nums = get_dynamic_nums(past_data, config)
        else:
            nums = list(range(10))
        
        # 生成投注
        bets = generate_smart_bets(nums, config['base_bet'].copy(), predicted_pattern)
        
        # 统计
        period_invested = sum(b['cost'] for b in bets)
        period_prize = 0
        period_wins = 0
        
        for bet in bets:
            if Counter(bet['numbers']) == Counter(draw_numbers):
                if bet['type'] == '组六' and len(set(draw_numbers)) == 3:
                    period_prize += 173
                    period_wins += 1
                elif bet['type'] == '组三' and len(set(draw_numbers)) == 2:
                    period_prize += 346
                    period_wins += 1
                elif bet['type'] == '直选' and bet['numbers'] == draw_numbers:
                    period_prize += 1040
                    period_wins += 1
        
        total_invested += period_invested
        total_prize += period_prize
        capital = initial_capital - total_invested + total_prize
        
        results.append({
            "period": i+1,
            "invested": period_invested,
            "prize": period_prize,
            "wins": period_wins
        })
        
        # 每 10 期调整
        if (i + 1) % 10 == 0:
            action, config = adjust_strategy(config, results)
            roi = (total_prize - total_invested) / max(1, total_invested) * 100
            print(f"   第{i+1}期：投入¥{period_invested} 中奖¥{period_prize} 资金¥{capital}")
            print(f"      ROI:{roi:.1f}% | 调整:{action} | 预测:{predicted_pattern}({confidence:.0%})")
    
    # 最终统计
    roi = (total_prize - total_invested) / max(1, total_invested) * 100
    win_count = sum(r['wins'] for r in results)
    
    config['performance']['total_periods'] = periods
    config['performance']['wins'] = win_count
    
    with open(STRATEGY_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 70)
    print("📊 执行结果")
    print("=" * 70)
    print(f"   初始资金：¥{initial_capital:,}")
    print(f"   总投入：¥{total_invested:,}")
    print(f"   总奖金：¥{total_prize:,}")
    print(f"   净收益：¥{total_prize - total_invested:,}")
    print(f"   ROI：{roi:.2f}%")
    print(f"   中奖：{win_count} 次")
    print(f"   最终资金：¥{capital:,}")
    
    print(f"\n⚙️ 调整记录")
    for adj in config['adjustments'][-5:]:
        print(f"   {adj['date'][:10]} ROI{adj['roi_10']:.1f}% - {adj['action']}")
    
    print(f"\n📄 配置：{STRATEGY_FILE}")
    print("=" * 70)
    
    return {"roi": roi, "wins": win_count, "config": config}


if __name__ == "__main__":
    run_dynamic_v2(periods=100)
