#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 动态策略调整系统
根据实时表现动态调整投注比例和选号逻辑
"""

import json
from collections import Counter
from datetime import datetime, timedelta

DATA_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_history.json"
STRATEGY_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_dynamic_strategy.json"
LOG_FILE = "/root/.openclaw/workspace/lottery/logs/fc3d_dynamic_log.txt"


def load_history():
    """加载福彩 3D 历史数据"""
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('records', [])


def load_strategy_config():
    """加载策略配置"""
    try:
        with open(STRATEGY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        # 默认配置
        return {
            "version": "v1.0",
            "created_at": datetime.now().isoformat(),
            "base_bet": {"group6": 3, "group3": 2, "direct": 1},
            "hot_weight": 0.6,
            "cold_weight": 0.3,
            "random_weight": 0.1,
            "performance": {
                "total_periods": 0,
                "total_invested": 0,
                "total_prize": 0,
                "wins": 0,
                "last_10_roi": 0,
                "last_20_roi": 0
            },
            "adjustments": []
        }


def save_strategy_config(config):
    """保存策略配置"""
    config['last_update'] = datetime.now().isoformat()
    with open(STRATEGY_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def calculate_omission(history, num, max_lookback=30):
    """计算遗漏期数"""
    omission = 0
    for draw in history[:max_lookback]:
        if num in draw['numbers']:
            break
        omission += 1
    return omission


def calculate_frequency(history, num, max_lookback=30):
    """计算出现频率"""
    return sum(1 for draw in history[:max_lookback] if num in draw['numbers'])


def get_scored_nums(history, lookback=30, hot_weight=0.6, cold_weight=0.3, random_weight=0.1):
    """综合评分选号"""
    candidates = []
    for num in range(10):
        frequency = calculate_frequency(history, num, lookback)
        omission = calculate_omission(history, num, lookback)
        recent = sum(1 for draw in history[:10] if num in draw['numbers'])
        
        # 动态权重评分
        score = (
            frequency * hot_weight +
            omission * cold_weight +
            recent * random_weight
        )
        candidates.append((num, score, omission, frequency))
    
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates


def generate_bets(nums, bet_config):
    """生成投注"""
    from itertools import combinations
    
    bets = []
    
    # 组六投注
    for combo in combinations(nums[:6], 3):
        bets.append({
            'type': '组六',
            'numbers': list(combo),
            'cost': 2
        })
        if len([b for b in bets if b['type'] == '组六']) >= bet_config['group6']:
            break
    
    # 组三投注
    group3_count = 0
    for num in nums[:3]:
        for other in nums[3:6]:
            if num != other:
                bets.append({
                    'type': '组三',
                    'numbers': [num, num, other],
                    'cost': 2
                })
                group3_count += 1
                if group3_count >= bet_config['group3']:
                    break
        if group3_count >= bet_config['group3']:
            break
    
    # 直选投注
    if bet_config['direct'] > 0:
        bets.append({
            'type': '直选',
            'numbers': nums[:3],
            'cost': 2
        })
    
    return bets


def analyze_performance(config, recent_results):
    """分析近期表现"""
    if len(recent_results) < 10:
        return "观察期", config
    
    # 计算近 10 期和近 20 期 ROI
    last_10 = recent_results[-10:]
    last_20 = recent_results[-20:] if len(recent_results) >= 20 else last_10
    
    roi_10 = (sum(r['prize'] for r in last_10) - sum(r['invested'] for r in last_10)) / sum(r['invested'] for r in last_10) * 100
    roi_20 = (sum(r['prize'] for r in last_20) - sum(r['invested'] for r in last_20)) / sum(r['invested'] for r in last_20) * 100
    
    config['performance']['last_10_roi'] = roi_10
    config['performance']['last_20_roi'] = roi_20
    
    # 动态调整策略
    adjustment = {
        "date": datetime.now().isoformat(),
        "periods": len(recent_results),
        "roi_10": roi_10,
        "roi_20": roi_20,
        "action": ""
    }
    
    # 调整逻辑
    if roi_10 < -50:
        # 严重亏损，减少投注
        config['base_bet']['group6'] = max(2, config['base_bet']['group6'] - 1)
        config['base_bet']['direct'] = 0
        adjustment['action'] = "严重亏损 - 减少投注"
    
    elif roi_10 < -20:
        # 轻度亏损，调整权重
        config['hot_weight'] = min(0.7, config['hot_weight'] + 0.1)
        config['cold_weight'] = max(0.2, config['cold_weight'] - 0.1)
        adjustment['action'] = "轻度亏损 - 增加热号权重"
    
    elif roi_10 > 30:
        # 表现良好，适度增加
        config['base_bet']['group6'] = min(5, config['base_bet']['group6'] + 1)
        config['base_bet']['direct'] = 1
        adjustment['action'] = "表现良好 - 适度增加"
    
    elif roi_10 > 10:
        # 稳定盈利，保持当前
        adjustment['action'] = "稳定盈利 - 保持当前"
    
    else:
        adjustment['action'] = "观察期 - 暂不调整"
    
    config['adjustments'].append(adjustment)
    
    # 保留最近 20 次调整记录
    if len(config['adjustments']) > 20:
        config['adjustments'] = config['adjustments'][-20:]
    
    return adjustment['action'], config


def log_result(period, invested, prize, wins, details):
    """记录结果"""
    log_entry = {
        "period": period,
        "date": datetime.now().isoformat(),
        "invested": invested,
        "prize": prize,
        "wins": wins,
        "details": details
    }
    
    # 追加到日志
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except:
        pass
    
    return log_entry


def run_dynamic_strategy(periods=50):
    """
    运行动态策略系统
    """
    print("=" * 70)
    print("福彩 3D 动态策略调整系统")
    print("=" * 70)
    
    # 加载数据
    print("\n📖 加载数据...")
    history = load_history()
    config = load_strategy_config()
    
    print(f"   历史数据：{len(history)} 期")
    print(f"   策略版本：{config['version']}")
    print(f"   当前配置：组六{config['base_bet']['group6']}注 + 组三{config['base_bet']['group3']}注 + 直选{config['base_bet']['direct']}注")
    
    # 回测模拟
    recent = history[:periods][::-1]
    results = []
    
    initial_capital = 10000
    capital = initial_capital
    total_invested = 0
    total_prize = 0
    
    print("\n📊 开始动态策略执行...")
    
    for i, draw in enumerate(recent):
        draw_numbers = draw['numbers']
        draw_date = draw['draw_date']
        issue = draw['issue']
        
        # 获取历史数据用于选号
        start_idx = max(0, i - 30)
        past_data = history[start_idx:i] if i > 0 else []
        
        # 动态权重选号
        if len(past_data) >= 10:
            scored = get_scored_nums(
                past_data,
                lookback=30,
                hot_weight=config['hot_weight'],
                cold_weight=config['cold_weight'],
                random_weight=config['random_weight']
            )
            nums = [n[0] for n in scored]
        else:
            nums = list(range(10))
        
        # 生成投注
        bets = generate_bets(nums, config['base_bet'])
        
        # 统计本期
        period_invested = sum(b['cost'] for b in bets)
        period_prize = 0
        period_wins = 0
        details = []
        
        for bet in bets:
            # 简单中奖检查
            if Counter(bet['numbers']) == Counter(draw_numbers):
                if bet['type'] == '组六' and len(set(draw_numbers)) == 3:
                    period_prize += 173
                    period_wins += 1
                    details.append(f"组六¥173")
                elif bet['type'] == '组三' and len(set(draw_numbers)) == 2:
                    period_prize += 346
                    period_wins += 1
                    details.append(f"组三¥346")
                elif bet['type'] == '直选' and bet['numbers'] == draw_numbers:
                    period_prize += 1040
                    period_wins += 1
                    details.append(f"直选¥1040")
        
        total_invested += period_invested
        total_prize += period_prize
        capital = initial_capital - total_invested + total_prize
        
        # 记录结果
        result = {
            "period": i + 1,
            "issue": issue,
            "date": draw_date,
            "invested": period_invested,
            "prize": period_prize,
            "wins": period_wins
        }
        results.append(result)
        
        # 每 10 期分析并调整
        if (i + 1) % 10 == 0:
            action, config = analyze_performance(config, results)
            roi = (total_prize - total_invested) / total_invested * 100 if total_invested > 0 else 0
            
            print(f"   第{i+1}期：投入¥{period_invested} 中奖¥{period_prize} 资金¥{capital}")
            print(f"      累计 ROI：{roi:.2f}% | 调整：{action}")
            print(f"      当前配置：组六{config['base_bet']['group6']} 组三{config['base_bet']['group3']} 直选{config['base_bet']['direct']}")
    
    # 最终统计
    roi = (total_prize - total_invested) / total_invested * 100 if total_invested > 0 else 0
    win_rate = sum(r['wins'] for r in results) / (periods * sum(config['base_bet'].values())) * 100
    
    # 更新配置
    config['performance']['total_periods'] = periods
    config['performance']['total_invested'] = total_invested
    config['performance']['total_prize'] = total_prize
    config['performance']['wins'] = sum(r['wins'] for r in results)
    
    save_strategy_config(config)
    
    # 生成报告
    print("\n" + "=" * 70)
    print("📊 执行结果")
    print("=" * 70)
    
    print(f"\n💰 总体表现")
    print(f"   初始资金：¥{initial_capital:,}")
    print(f"   总投入：¥{total_invested:,}")
    print(f"   总奖金：¥{total_prize:,}")
    print(f"   净收益：¥{total_prize - total_invested:,}")
    print(f"   ROI：{roi:.2f}%")
    print(f"   中奖次数：{sum(r['wins'] for r in results)} 次")
    print(f"   中奖率：{win_rate:.2f}%")
    print(f"   最终资金：¥{capital:,}")
    
    print(f"\n⚙️ 策略调整记录")
    for adj in config['adjustments'][-5:]:
        print(f"   {adj['date'][:10]} 第{adj['periods']}期 ROI{adj['roi_10']:.1f}% - {adj['action']}")
    
    print(f"\n📄 配置文件：{STRATEGY_FILE}")
    print("=" * 70)
    
    return {
        "periods": periods,
        "roi": roi,
        "config": config,
        "results": results
    }


if __name__ == "__main__":
    run_dynamic_strategy(periods=50)
