#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票策略回测系统
- 回测历史区间的策略表现
- 计算收益率、中奖率、最大回撤等指标
- 对比不同策略的表现
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from lottery_strategies import LotteryStrategies
from strategy_tracker import StrategyTracker
from datetime import datetime
from typing import Dict, List
import json


class Backtest:
    """回测系统"""
    
    PRIZE_RULES = {
        'ssq': {
            1: {'match': '6+1', 'amount': 5000000},
            2: {'match': '6+0', 'amount': 100000},
            3: {'match': '5+1', 'amount': 3000},
            4: {'match': '5+0|4+1', 'amount': 200},
            5: {'match': '4+0|3+1', 'amount': 10},
            6: {'match': '0+1|1+1|2+1', 'amount': 5},
        },
        'dlt': {
            1: {'match': '5+2', 'amount': 8000000},
            2: {'match': '5+1', 'amount': 100000},
            3: {'match': '5+0|4+2', 'amount': 10000},
            4: {'match': '4+1|3+2', 'amount': 300},
            5: {'match': '4+0|3+1|2+2', 'amount': 15},
            6: {'match': '3+0|1+2|2+1|0+2', 'amount': 5},
        }
    }
    
    def __init__(self):
        self.storage = LotteryStorage()
        self.strategies = LotteryStrategies(self.storage)
        self.tracker = StrategyTracker()
    
    def run(self, lottery_type: str, start_issue: str = None, end_issue: str = None, 
            strategy_name: str = 'all', initial_capital: int = 10000) -> Dict:
        """
        运行回测
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            start_issue: 开始期号（默认最早）
            end_issue: 结束期号（默认最新）
            strategy_name: 策略名（默认全部）
            initial_capital: 初始资金
        
        Returns:
            回测结果字典
        """
        # 获取历史数据
        history = self.storage.get_history(lottery_type, 1000)
        if not history:
            return {'error': '无历史数据'}
        
        # 反转顺序（从旧到新）
        history = history[::-1]
        
        # 筛选期号区间
        if start_issue:
            history = [h for h in history if h['issue'] >= start_issue]
        if end_issue:
            history = [h for h in history if h['issue'] <= end_issue]
        
        if len(history) < 2:
            return {'error': '数据不足'}
        
        print(f"\n📊 回测区间：{history[0]['issue']} - {history[-1]['issue']}")
        print(f"   总期数：{len(history)} 期")
        print(f"   彩种：{'双色球' if lottery_type == 'ssq' else '大乐透'}")
        
        # 获取所有策略
        all_strategies = self.strategies.get_all_strategies(lottery_type)
        if strategy_name != 'all':
            if strategy_name in all_strategies:
                all_strategies = {strategy_name: all_strategies[strategy_name]}
            else:
                return {'error': f'未知策略：{strategy_name}'}
        
        # 回测结果
        results = {}
        
        for strat_name, strat_func in all_strategies.items():
            print(f"\n🔍 回测策略：{strat_name}")
            
            capital = initial_capital
            total_invested = 0
            total_prize = 0
            win_periods = 0
            win_details = []
            
            for i, period in enumerate(history[:-1]):  # 最后一期不测（用来预测）
                issue = period['issue']
                next_issue = history[i+1]['issue']
                winning_numbers = history[i+1]['numbers']
                
                # 生成推荐（用当期数据预测下期）
                recs = strat_func()
                if not recs:
                    continue
                
                # 计算投入（每注 2 元，每策略 5 注）
                period_cost = len(recs) * 2
                total_invested += period_cost
                capital -= period_cost
                
                # 检查中奖
                period_prize = 0
                period_win = False
                
                for rec in recs:
                    prize_info = self._check_prize(lottery_type, rec, winning_numbers)
                    if prize_info['level'] > 0:
                        period_prize += prize_info['amount']
                        period_win = True
                
                if period_win:
                    win_periods += 1
                    win_details.append({
                        'issue': next_issue,
                        'prize': period_prize
                    })
                
                total_prize += period_prize
                capital += period_prize
            
            # 计算指标
            results[strat_name] = {
                'initial_capital': initial_capital,
                'final_capital': capital,
                'total_invested': total_invested,
                'total_prize': total_prize,
                'net_return': capital - initial_capital,
                'return_rate': (capital - initial_capital) / initial_capital * 100,
                'win_rate': win_periods / len(history[:-1]) * 100 if history else 0,
                'win_periods': win_periods,
                'total_periods': len(history[:-1]),
                'win_details': win_details[-5:],  # 最近 5 次中奖
            }
        
        return results
    
    def _check_prize(self, lottery_type: str, recommendation: Dict, winning: Dict) -> Dict:
        """检查单注中奖"""
        if lottery_type == 'ssq':
            red_match = len(set(recommendation.get('red', [])) & set(winning.get('red', [])))
            blue_match = 1 if recommendation.get('blue', [])[0] in winning.get('blue', []) else 0
            
            if red_match == 6 and blue_match == 1:
                return {'level': 1, 'amount': 5000000}
            elif red_match == 6 and blue_match == 0:
                return {'level': 2, 'amount': 100000}
            elif red_match == 5 and blue_match == 1:
                return {'level': 3, 'amount': 3000}
            elif red_match == 5 or (red_match == 4 and blue_match == 1):
                return {'level': 4, 'amount': 200}
            elif red_match == 4 or (red_match == 3 and blue_match == 1):
                return {'level': 5, 'amount': 10}
            elif blue_match == 1:
                return {'level': 6, 'amount': 5}
        
        elif lottery_type == 'dlt':
            front_match = len(set(recommendation.get('front', [])) & set(winning.get('front', [])))
            back_match = len(set(recommendation.get('back', [])) & set(winning.get('back', [])))
            
            if front_match == 5 and back_match == 2:
                return {'level': 1, 'amount': 8000000}
            elif front_match == 5 and back_match == 1:
                return {'level': 2, 'amount': 100000}
            elif front_match == 5 or (front_match == 4 and back_match == 2):
                return {'level': 3, 'amount': 10000}
            elif front_match == 4 and back_match == 1 or front_match == 3 and back_match == 2:
                return {'level': 4, 'amount': 300}
            elif front_match == 4 or front_match == 3 and back_match == 1 or front_match == 2 and back_match == 2:
                return {'level': 5, 'amount': 15}
            elif front_match == 3 or front_match == 1 and back_match == 2 or front_match == 2 and back_match == 1 or front_match == 0 and back_match == 2:
                return {'level': 6, 'amount': 5}
        
        return {'level': 0, 'amount': 0}
    
    def print_results(self, results: Dict):
        """打印回测结果"""
        if 'error' in results:
            print(f"❌ {results['error']}")
            return
        
        print("\n" + "=" * 70)
        print("📊 回测结果汇总")
        print("=" * 70)
        
        # 按收益率排序
        sorted_results = sorted(results.items(), key=lambda x: x[1]['return_rate'], reverse=True)
        
        for strat_name, metrics in sorted_results:
            print(f"\n【{strat_name}】")
            print(f"   初始资金：¥{metrics['initial_capital']:,}")
            print(f"   最终资金：¥{metrics['final_capital']:,}")
            print(f"   总投入：¥{metrics['total_invested']:,}")
            print(f"   总奖金：¥{metrics['total_prize']:,}")
            print(f"   净收益：¥{metrics['net_return']:,}")
            print(f"   收益率：{metrics['return_rate']:.2f}%")
            print(f"   中奖率：{metrics['win_rate']:.2f}% ({metrics['win_periods']}/{metrics['total_periods']})")
            
            if metrics['win_details']:
                print(f"   最近中奖：")
                for detail in metrics['win_details'][-3:]:
                    print(f"      - {detail['issue']} 期：¥{detail['prize']:,}")
        
        # 最佳策略
        best = sorted_results[0]
        print(f"\n⭐ 最佳策略：{best[0]}")
        print(f"   收益率：{best[1]['return_rate']:.2f}%")
        
        print("\n" + "=" * 70)


def main():
    """主函数"""
    backtest = Backtest()
    
    print("=" * 70)
    print("🎰 彩票策略回测系统")
    print("=" * 70)
    
    # 双色球回测
    print("\n【双色球回测】")
    ssq_results = backtest.run('ssq')
    backtest.print_results(ssq_results)
    
    # 大乐透回测
    print("\n【大乐透回测】")
    dlt_results = backtest.run('dlt')
    backtest.print_results(dlt_results)
    
    print("\n✅ 回测完成！")


if __name__ == "__main__":
    main()
