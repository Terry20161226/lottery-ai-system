#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后模型回测验证
对比优化前 vs 优化后的表现
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from ml_predictor import MLPredictor
from datetime import datetime
import json


class BacktestV2:
    """优化后模型回测"""
    
    PRIZE_RULES_DLT = {
        1: {'match': '5+2', 'amount': 8000000},
        2: {'match': '5+1', 'amount': 100000},
        3: {'match': '5+0|4+2', 'amount': 10000},
        4: {'match': '4+1|3+2', 'amount': 300},
        5: {'match': '4+0|3+1|2+2', 'amount': 15},
        6: {'match': '3+0|1+2|2+1|0+2', 'amount': 5},
    }
    
    def __init__(self, storage=None):
        self.storage = storage if storage else LotteryStorage()
        self.ml = MLPredictor(self.storage)
    
    def check_prize(self, bet_front, bet_back, draw_front, draw_back) -> tuple:
        """检查中奖金额和奖级"""
        # 确保是整数
        bet_front = [int(n) if isinstance(n, str) else n for n in bet_front]
        bet_back = [int(n) if isinstance(n, str) else n for n in bet_back]
        
        match_front = len(set(bet_front) & set(draw_front))
        match_back = len(set(bet_back) & set(draw_back))
        
        # 奖级判断
        if match_front == 5 and match_back == 2:
            return 8000000, 1
        elif match_front == 5 and match_back == 1:
            return 100000, 2
        elif match_front == 5 and match_back == 0:
            return 10000, 3
        elif match_front == 4 and match_back >= 1:
            return 300, 4
        elif match_front >= 3 and match_back >= 1:
            return 15, 5
        elif match_front >= 2 and match_back >= 1:
            return 5, 6
        elif match_back == 2:
            return 5, 6
        return 0, 0
    
    def run(self, periods=100, initial_capital=10000, epsilon=0.3) -> dict:
        """
        运行回测
        
        Args:
            periods: 回测期数
            initial_capital: 初始资金
            epsilon: 探索概率
        """
        history = self.storage.get_history('dlt', periods + 50)
        if not history:
            return {'error': '无历史数据'}
        
        history = history[:periods][::-1]  # 从旧到新
        
        print(f"\n📊 优化模型回测")
        print(f"   回测期数：{periods}期")
        print(f"   初始资金：¥{initial_capital}")
        print(f"   探索概率：ε={epsilon}")
        
        capital = initial_capital
        total_invested = 0
        total_prize = 0
        wins = 0
        win_details = []
        max_drawdown = 0
        peak_capital = initial_capital
        
        # 统计连号出现
        consecutive_count = 0
        
        for i, draw in enumerate(history):
            draw_issue = draw.get('issue', '')
            draw_front = draw.get('numbers', {}).get('front', [])
            draw_back = draw.get('numbers', {}).get('back', [])
            
            # 获取优化模型预测（2 注）
            preds = self.ml.predict(n_predictions=2, epsilon=epsilon)
            
            # 计算本期投注
            bet_amount = len(preds) * 2  # 每注 2 元
            capital -= bet_amount
            total_invested += bet_amount
            
            # 检查中奖
            period_prize = 0
            best_match = 0
            for pred in preds:
                pred_front = pred.get('front', [])
                pred_back = pred.get('back', [])
                prize, level = self.check_prize(pred_front, pred_back, draw_front, draw_back)
                period_prize += prize
                best_match = max(best_match, level)
                
                # 统计连号
                front_nums = [int(n) if isinstance(n, str) else n for n in pred_front]
                has_consecutive = any(front_nums[j+1] - front_nums[j] == 1 for j in range(len(front_nums)-1))
                if has_consecutive:
                    consecutive_count += 1
            
            capital += period_prize
            total_prize += period_prize
            
            if period_prize > 0:
                wins += 1
                win_details.append({
                    'issue': draw_issue,
                    'prize': period_prize,
                    'level': best_match,
                    'capital': capital
                })
            
            # 计算最大回撤
            if capital > peak_capital:
                peak_capital = capital
            drawdown = (peak_capital - capital) / peak_capital * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 计算指标
        roi = (total_prize - total_invested) / total_invested * 100 if total_invested > 0 else 0
        win_rate = wins / periods * 100
        
        # 连号率
        total_predictions = periods * 2
        consecutive_rate = consecutive_count / total_predictions * 100 if total_predictions > 0 else 0
        
        result = {
            'periods': periods,
            'initial_capital': initial_capital,
            'final_capital': capital,
            'total_invested': total_invested,
            'total_prize': total_prize,
            'net_profit': total_prize - total_invested,
            'roi': roi,
            'win_rate': win_rate,
            'total_wins': wins,
            'max_drawdown': max_drawdown,
            'consecutive_rate': consecutive_rate,
            'details': win_details[-10:]  # 最近 10 次中奖
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
        print(f"   最大回撤：{max_drawdown:.2f}%")
        print(f"   连号率：{consecutive_rate:.1f}% (目标 60%)")
        
        if win_details:
            print(f"\n   中奖明细：")
            for d in win_details[-5:]:
                prize_emoji = '🎉' if d['prize'] >= 15 else '✨'
                print(f"      {prize_emoji} {d['issue']}期：¥{d['prize']} (奖级{d['level']})")
        
        print(f"{'=' * 60}")
        
        return result
    
    def compare_with_baseline(self, periods=100):
        """对比优化前后"""
        print("\n" + "=" * 70)
        print("📊 优化前后对比")
        print("=" * 70)
        
        # 优化前基准（来自原始回测）
        baseline = {
            'name': '原策略 (consecutive)',
            'roi': -71.95,
            'win_rate': 26.63,
            'notes': '5 注/期，无优化'
        }
        
        # 优化后（运行回测）
        print("\n【优化前】")
        print(f"   策略：{baseline['name']}")
        print(f"   收益率：{baseline['roi']:.2f}%")
        print(f"   中奖率：{baseline['win_rate']:.2f}%")
        print(f"   备注：{baseline['notes']}")
        
        print("\n【优化后】")
        result = self.run(periods=periods, epsilon=0.3)
        
        print("\n【对比分析】")
        roi_improve = result['roi'] - baseline['roi']
        win_rate_change = result['win_rate'] - baseline['win_rate']
        
        if roi_improve > 0:
            print(f"   ✅ 收益率提升：{roi_improve:.2f}%")
        else:
            print(f"   ⚠️ 收益率下降：{roi_improve:.2f}%")
        
        if win_rate_change > 0:
            print(f"   ✅ 中奖率提升：{win_rate_change:.2f}%")
        else:
            print(f"   ⚠️ 中奖率下降：{win_rate_change:.2f}%")
        
        print(f"   📉 最大回撤：{result['max_drawdown']:.2f}%")
        print(f"   🔗 连号率：{result['consecutive_rate']:.1f}% (接近 60% 为优)")
        
        return {
            'baseline': baseline,
            'optimized': result,
            'improvement': {
                'roi': roi_improve,
                'win_rate': win_rate_change
            }
        }


def main():
    print("=" * 70)
    print("🤖 ML 模型优化回测验证")
    print("=" * 70)
    
    storage = LotteryStorage()
    backtest = BacktestV2(storage)
    
    # 确保模型已加载
    if not backtest.ml.load_model():
        print("❌ 模型未加载，请先训练")
        return
    
    # 对比回测
    comparison = backtest.compare_with_baseline(periods=100)
    
    # 保存报告
    report = {
        'timestamp': datetime.now().isoformat(),
        'baseline': comparison['baseline'],
        'optimized': {
            'periods': comparison['optimized']['periods'],
            'roi': comparison['optimized']['roi'],
            'win_rate': comparison['optimized']['win_rate'],
            'max_drawdown': comparison['optimized']['max_drawdown'],
            'consecutive_rate': comparison['optimized']['consecutive_rate']
        },
        'improvement': comparison['improvement']
    }
    
    with open('/root/.openclaw/workspace/lottery/reports/backtest_v2.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 回测报告已保存到 reports/backtest_v2.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
