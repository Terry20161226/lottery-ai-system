#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化策略回测系统
对比原策略 vs 优化策略的表现
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from optimized_strategies import OptimizedStrategies
from datetime import datetime
import json
import random


class OptimizedBacktest:
    """优化策略回测"""
    
    PRIZE_RULES_DLT = {
        1: {'match': '5+2', 'amount': 8000000},
        2: {'match': '5+1', 'amount': 100000},
        3: {'match': '5+0|4+2', 'amount': 10000},
        4: {'match': '4+1|3+2', 'amount': 300},
        5: {'match': '4+0|3+1|2+2', 'amount': 15},
        6: {'match': '3+0|1+2|2+1|0+2', 'amount': 5},
    }
    
    def __init__(self):
        self.storage = LotteryStorage()
        self.opt = OptimizedStrategies(self.storage)
    
    def check_prize(self, bet_front, bet_back, draw_front, draw_back) -> int:
        """检查中奖金额"""
        match_front = len(set(bet_front) & set(draw_front))
        match_back = len(set(bet_back) & set(draw_back))
        
        # 简化奖级判断
        if match_front == 5 and match_back == 2:
            return 8000000
        elif match_front == 5 and match_back == 1:
            return 100000
        elif match_front == 5 and match_back == 0:
            return 10000
        elif match_front == 4 and match_back >= 1:
            return 300
        elif match_front >= 3 and match_back >= 1:
            return 15
        elif match_front >= 2 and match_back >= 1:
            return 5
        elif match_back == 2:
            return 5
        return 0
    
    def run(self, periods: int = 100, initial_capital: int = 10000) -> dict:
        """
        运行优化策略回测
        
        Args:
            periods: 回测期数
            initial_capital: 初始资金
        """
        history = self.storage.get_history('dlt', periods + 50)
        if not history:
            return {'error': '无历史数据'}
        
        history = history[:periods][::-1]  # 从旧到新
        
        print(f"\n📊 优化策略回测")
        print(f"   回测期数：{periods}期")
        print(f"   初始资金：¥{initial_capital}")
        
        capital = initial_capital
        total_invested = 0
        total_prize = 0
        wins = 0
        details = []
        
        for i, draw in enumerate(history):
            draw_issue = draw.get('issue', '')
            draw_front = draw.get('numbers', {}).get('front', [])
            draw_back = draw.get('numbers', {}).get('back', [])
            
            # 获取优化策略推荐
            recs = self.opt.dlt_optimized(capital, total_invested)
            
            # 计算本期投注
            bet_amount = len(recs) * 2  # 每注 2 元
            capital -= bet_amount
            total_invested += bet_amount
            
            # 检查中奖
            period_prize = 0
            for rec in recs:
                bet_front = rec.get('front', [])
                bet_back = rec.get('back', [])
                prize = self.check_prize(bet_front, bet_back, draw_front, draw_back)
                period_prize += prize
                if prize > 0:
                    wins += 1
            
            capital += period_prize
            total_prize += period_prize
            
            if period_prize > 0:
                details.append({
                    'issue': draw_issue,
                    'prize': period_prize,
                    'capital': capital
                })
        
        # 计算指标
        roi = (total_prize - total_invested) / total_invested * 100 if total_invested > 0 else 0
        win_rate = wins / periods * 100
        
        result = {
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_invested': total_invested,
            'total_prize': total_prize,
            'net_profit': total_prize - total_invested,
            'roi': roi,
            'win_rate': win_rate,
            'total_wins': wins,
            'periods': periods,
            'details': details[-10:]  # 最近 10 次中奖
        }
        
        # 打印结果
        print(f"\n{'=' * 60}")
        print("📊 回测结果")
        print(f"{'=' * 60}")
        print(f"   最终资金：¥{capital}")
        print(f"   总投入：¥{total_invested}")
        print(f"   总奖金：¥{total_prize}")
        print(f"   净收益：¥{total_prize - total_invested}")
        print(f"   收益率：{roi:.2f}%")
        print(f"   中奖率：{win_rate:.2f}% ({wins}/{periods})")
        
        if details:
            print(f"\n   最近中奖：")
            for d in details[-5:]:
                print(f"      - {d['issue']}期：¥{d['prize']}")
        
        print(f"{'=' * 60}")
        
        return result


def compare_strategies():
    """对比原策略和优化策略"""
    print("\n" + "=" * 70)
    print("🎯 策略对比：原策略 vs 优化策略")
    print("=" * 70)
    
    print("\n【原策略表现】（来自 backtest.py）")
    print("   最佳策略：consecutive")
    print("   收益率：-71.95%")
    print("   中奖率：26.63%")
    print("   问题：投注过多（5 注/期），无止损")
    
    print("\n【优化策略改进】")
    print("   1. 投注从 5 注减到 2 注（成本 -60%）")
    print("   2. 增加止损机制（亏损 70% 时减为 1 注）")
    print("   3. 结合热号 + 冷号 + 遗漏反弹")
    print("   4. 遗漏>15 期号码重点关注")
    
    # 运行优化策略回测
    backtest = OptimizedBacktest()
    result = backtest.run(periods=100, initial_capital=10000)
    
    print("\n【预期改进】")
    if result.get('roi', -100) > -72:
        print("   ✅ 优化策略收益率优于原策略")
    else:
        print("   ⚠️ 需要进一步优化")


def main():
    print("=" * 70)
    print("📊 彩票策略优化回测系统")
    print("=" * 70)
    
    compare_strategies()
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'optimized_result': '见上文',
        'improvements': [
            '投注数量从 5 注减到 2 注',
            '增加止损机制',
            '结合多种信号（热号 + 冷号 + 遗漏）',
            '遗漏>15 期重点关注'
        ]
    }
    
    with open('reports/optimization_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 优化报告已保存到 reports/optimization_report.json")


if __name__ == "__main__":
    main()
