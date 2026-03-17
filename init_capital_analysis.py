#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化资金分析数据
从历史开奖和推荐数据回测生成初始资金记录
"""

import json
import os
from datetime import datetime
from pathlib import Path

LOTTERY_DIR = Path('/root/.openclaw/workspace/lottery')
DATA_DIR = LOTTERY_DIR / 'data'
STATS_DIR = LOTTERY_DIR / 'stats'
FEEDBACK_DIR = LOTTERY_DIR / 'feedback'


def load_history(lottery_type: str, limit: int = 50):
    """加载历史开奖数据"""
    filepath = DATA_DIR / f'{lottery_type}_history.json'
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data.get('records', [])
    return records[:limit]


def load_recommendations(lottery_type: str, limit: int = 50):
    """加载历史推荐数据"""
    filepath = DATA_DIR / f'{lottery_type}_recommend.json'
    if not filepath.exists():
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    recs = data.get('recommendations', [])
    return recs[:limit]


def calculate_prize(lottery_type: str, rec_numbers: dict, draw_numbers: dict) -> int:
    """计算单注奖金（简化版）"""
    if lottery_type == 'dlt':
        rec_front = set(rec_numbers.get('front', []))
        rec_back = set(rec_numbers.get('back', []))
        draw_front = set(draw_numbers.get('front', draw_numbers.get('red', [])))
        draw_back = set(draw_numbers.get('back', draw_numbers.get('blue', [])))
        
        front_hit = len(rec_front & draw_front)
        back_hit = len(rec_back & draw_back)
        
        # 简化奖级表
        prizes = {
            (5, 2): 5000000,  # 一等奖
            (5, 1): 100000,   # 二等奖
            (5, 0): 10000,    # 三等奖
            (4, 2): 3000,     # 四等奖
            (4, 1): 300,      # 五等奖
            (3, 2): 200,      # 六等奖
            (4, 0): 100,      # 七等奖
            (3, 1): 15,       # 八等奖
            (2, 2): 15,       # 八等奖
            (3, 0): 5,        # 九等奖
            (1, 2): 5,        # 九等奖
            (2, 1): 5,        # 九等奖
            (0, 2): 5,        # 九等奖
        }
        return prizes.get((front_hit, back_hit), 0)
    
    elif lottery_type == 'ssq':
        rec_red = set(rec_numbers.get('red', []))
        rec_blue = set(rec_numbers.get('blue', []))
        draw_red = set(draw_numbers.get('red', []))
        draw_blue = set(draw_numbers.get('blue', []))
        
        red_hit = len(rec_red & draw_red)
        blue_hit = 1 if rec_blue and draw_blue and list(rec_blue)[0] == list(draw_blue)[0] else 0
        
        # 简化奖级表
        if red_hit == 6 and blue_hit == 1:
            return 5000000  # 一等奖
        elif red_hit == 6 and blue_hit == 0:
            return 100000   # 二等奖
        elif red_hit == 5 and blue_hit == 1:
            return 3000     # 三等奖
        elif red_hit == 5 or (red_hit == 4 and blue_hit == 1):
            return 200      # 四等奖
        elif red_hit == 4 or (red_hit == 3 and blue_hit == 1):
            return 10       # 五等奖
        elif blue_hit == 1:
            return 5        # 六等奖
        return 0
    
    return 0


def simulate_backtest(lottery_type: str, initial_capital: int = 10000):
    """回测历史数据生成资金记录"""
    print(f"\n【{lottery_type.upper()} 回测】")
    
    history = load_history(lottery_type, 30)
    recommendations = load_recommendations(lottery_type, 30)
    
    if not history or not recommendations:
        print(f"   ⚠️ 数据不足")
        return []
    
    # 按时间排序（从旧到新）
    history = history[::-1]
    recommendations = recommendations[::-1]
    
    capital = initial_capital
    capital_history = [initial_capital]
    bet_history = []
    
    total_bet = 0
    total_prize = 0
    
    # 回测最近 30 期
    for i in range(min(len(history), len(recommendations))):
        draw = history[i]
        rec = recommendations[i]
        
        # 获取开奖号码
        draw_nums = draw.get('numbers', {})
        
        # 获取推荐号码（取第一注）
        rec_nums_list = rec.get('numbers', [])
        if not rec_nums_list:
            continue
        
        # 每注 2 元，每期 5 注
        bet_amount = 5 * 2  # 10 元
        total_bet += bet_amount
        capital -= bet_amount
        
        # 计算中奖
        prize = 0
        for rec_nums in rec_nums_list[:5]:  # 最多 5 注
            prize += calculate_prize(lottery_type, rec_nums, draw_nums)
        
        total_prize += prize
        capital += prize
        capital_history.append(capital)
        
        bet_history.append({
            'issue': draw.get('issue'),
            'date': draw.get('draw_date', datetime.now().strftime('%Y-%m-%d')),
            'bet': bet_amount,
            'prize': prize,
            'capital': capital,
            'roi': (capital - initial_capital) / initial_capital * 100
        })
    
    print(f"   回测期数：{len(bet_history)}")
    print(f"   总投入：¥{total_bet}")
    print(f"   总奖金：¥{total_prize}")
    print(f"   净收益：¥{total_prize - total_bet}")
    print(f"   最终资金：¥{capital}")
    
    return {
        'history': capital_history,
        'bets': bet_history,
        'initial': initial_capital,
        'final': capital,
        'total_bet': total_bet,
        'total_prize': total_prize
    }


def main():
    """主函数"""
    print("=" * 60)
    print("📊 初始化资金分析数据")
    print("=" * 60)
    
    initial_capital = 10000
    
    # 回测大乐透
    dlt_result = simulate_backtest('dlt', initial_capital)
    
    # 回测双色球
    ssq_result = simulate_backtest('ssq', initial_capital)
    
    # 合并结果
    combined_history = []
    if dlt_result.get('history') and ssq_result.get('history'):
        # 简单平均（实际应该按时间合并）
        min_len = min(len(dlt_result['history']), len(ssq_result['history']))
        combined_history = [
            (dlt_result['history'][i] + ssq_result['history'][i]) / 2
            for i in range(min_len)
        ]
    elif dlt_result.get('history'):
        combined_history = dlt_result['history']
    elif ssq_result.get('history'):
        combined_history = ssq_result['history']
    
    # 保存数据
    stats_file = STATS_DIR / 'capital_stats.json'
    stats_file.parent.mkdir(parents=True, exist_ok=True)
    
    capital_data = {
        'history': combined_history,
        'initial': initial_capital,
        'current': combined_history[-1] if combined_history else initial_capital,
        'created_at': datetime.now().isoformat(),
        'backtest': {
            'dlt': dlt_result,
            'ssq': ssq_result
        }
    }
    
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(capital_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"💾 数据已保存：{stats_file}")
    print(f"📈 资金曲线点数：{len(combined_history)}")
    print(f"💰 当前资金：¥{capital_data['current']:,.0f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
