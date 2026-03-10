#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自适应策略生成模块
根据特征分析结果动态调整策略权重，生成最优推荐
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from lottery_strategies import LotteryStrategies
from feature_analyzer import FeatureAnalyzer
from strategy_tracker import StrategyTracker
import random
from typing import Dict, List

STRATEGY_NAMES = {
    'balanced': '均衡策略',
    'hot_tracking': '热号追踪',
    'cold_rebound': '冷号反弹',
    'odd_even': '奇偶均衡',
    'zone_distribution': '区间分布',
    'consecutive': '连号追踪',
    'warm_balance': '温号搭配',
}


class AdaptiveStrategy:
    """自适应策略生成器"""
    
    def __init__(self):
        self.storage = LotteryStorage()
        self.strategies = LotteryStrategies(self.storage)
        self.analyzer = FeatureAnalyzer()
        self.tracker = StrategyTracker()
    
    def get_adaptive_weights(self, lottery_type: str) -> Dict[str, float]:
        """获取自适应权重 - 多因子加权"""
        # 1. 优先使用回测结果（最可靠）
        backtest_weights = self._get_backtest_weights(lottery_type)
        if backtest_weights:
            return backtest_weights
        
        # 2. 使用历史中奖统计
        stats = self.tracker.get_summary(lottery_type)
        if stats and stats.get('strategy_stats'):
            strategy_stats = stats['strategy_stats']
            total_hit_rate = sum(s.get('hit_rate', 0) for s in strategy_stats.values())
            
            if total_hit_rate > 0:
                weights = {}
                for strategy_name, data in strategy_stats.items():
                    hit_rate = data.get('hit_rate', 0)
                    weights[strategy_name] = round(hit_rate / total_hit_rate, 2)
                
                total = sum(weights.values())
                if total > 0:
                    return {k: round(v/total, 2) for k, v in weights.items()}
        
        # 3. 使用特征分析结果
        return self.analyzer.get_strategy_weights(lottery_type)
    
    def _get_backtest_weights(self, lottery_type: str) -> Dict[str, float]:
        """
        根据回测结果计算权重 - 多因子加权（基于最新回测 2026-03-06）
        
        权重 = 0.5 × 收益率分 + 0.3 × 中奖率分 + 0.2 × 稳定性分
        """
        # 回测结果（基于最新回测数据 - 2026-03-06）
        # 双色球：热号追踪 +3390% 遥遥领先
        # 大乐透：热号追踪 -19% 相对最佳
        backtest_results = {
            'ssq': {
                # 基于最新回测：热号追踪收益率 +3390%，中奖率 39.87%
                'hot_tracking': {'return_rank': 1, 'hit_rate_rank': 1, 'return_rate': 3390.40, 'hit_rate': 39.87},
                'balanced': {'return_rank': 2, 'hit_rate_rank': 2, 'return_rate': 72.20, 'hit_rate': 35.51},
                'warm_balance': {'return_rank': 3, 'hit_rate_rank': 3, 'return_rate': -29.15, 'hit_rate': 30.28},
                'consecutive': {'return_rank': 4, 'hit_rate_rank': 4, 'return_rate': -33.70, 'hit_rate': 28.32},
                'odd_even': {'return_rank': 5, 'hit_rate_rank': 5, 'return_rate': -36.10, 'hit_rate': 26.58},
                'zone_distribution': {'return_rank': 6, 'hit_rate_rank': 5, 'return_rate': -38.50, 'hit_rate': 26.58},
                'cold_rebound': {'return_rank': 7, 'hit_rate_rank': 7, 'return_rate': -37.05, 'hit_rate': 23.31},
            },
            'dlt': {
                # 基于最新回测：热号追踪 -19% 相对最佳
                'hot_tracking': {'return_rank': 1, 'hit_rate_rank': 1, 'return_rate': -19.10, 'hit_rate': 26.48},
                'odd_even': {'return_rank': 2, 'hit_rate_rank': 3, 'return_rate': -27.10, 'hit_rate': 22.82},
                'warm_balance': {'return_rank': 3, 'hit_rate_rank': 2, 'return_rate': -28.80, 'hit_rate': 28.17},
                'balanced': {'return_rank': 4, 'hit_rate_rank': 4, 'return_rate': -29.25, 'hit_rate': 24.51},
                'zone_distribution': {'return_rank': 5, 'hit_rate_rank': 4, 'return_rate': -29.65, 'hit_rate': 24.51},
                'consecutive': {'return_rank': 6, 'hit_rate_rank': 6, 'return_rate': -30.50, 'hit_rate': 21.13},
                'cold_rebound': {'return_rank': 7, 'hit_rate_rank': 7, 'return_rate': -30.50, 'hit_rate': 19.72},
            }
        }
        
        results = backtest_results.get(lottery_type)
        if not results:
            return None
        
        # 多因子计算综合得分
        scores = {}
        total_score = 0
        
        for strategy, data in results.items():
            # 收益率排名分（7 分制）
            return_score = (8 - data['return_rank']) / 7
            # 中奖率排名分
            hit_score = (8 - data['hit_rate_rank']) / 7
            # 综合得分
            score = 0.5 * return_score + 0.3 * hit_score + 0.2 * 0.5  # 稳定性基础分
            scores[strategy] = score
            total_score += score
        
        # 归一化为权重
        if total_score > 0:
            weights = {k: round(v / total_score, 2) for k, v in scores.items()}
            return weights
        
        return None
    
    def generate_adaptive_recommendation(self, lottery_type: str, num_recommendations: int = 5) -> List[Dict]:
        """
        生成自适应推荐号码
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            num_recommendations: 推荐注数
        
        Returns:
            推荐号码列表
        """
        weights = self.get_adaptive_weights(lottery_type)
        all_strategies = self.strategies.get_all_strategies(lottery_type)
        
        recommendations = []
        
        for _ in range(num_recommendations):
            # 根据权重随机选择策略
            strategy_name = self._weighted_choice(weights)
            strategy_func = all_strategies.get(strategy_name)
            
            if strategy_func:
                # 生成该策略的 1 注推荐
                strategy_recs = strategy_func()
                if strategy_recs:
                    rec = strategy_recs[0]  # 取第 1 注
                    rec['strategy'] = strategy_name
                    rec['strategy_name'] = STRATEGY_NAMES.get(strategy_name, strategy_name)
                    recommendations.append(rec)
        
        return recommendations
    
    def _weighted_choice(self, weights: Dict[str, float]) -> str:
        """根据权重随机选择策略"""
        import random
        
        items = list(weights.keys())
        weight_values = list(weights.values())
        
        return random.choices(items, weights=weight_values, k=1)[0]
    
    def get_weights_explanation(self, lottery_type: str) -> str:
        """获取权重说明"""
        weights = self.get_adaptive_weights(lottery_type)
        
        lines = ["【策略权重分析】"]
        
        sorted_weights = sorted(weights.items(), key=lambda x: x[1], reverse=True)
        
        for strategy_name, weight in sorted_weights:
            cn_name = STRATEGY_NAMES.get(strategy_name, strategy_name)
            percentage = round(weight * 100, 1)
            lines.append(f"  {cn_name}: {percentage}%")
        
        best_strategy = self.tracker.get_best_strategy(lottery_type)
        if best_strategy:
            lines.append("")
            lines.append(f"⭐ 历史最佳策略：{best_strategy.get('name_cn', '均衡策略')}")
            lines.append(f"   累计奖金：¥{best_strategy.get('total_prize', 0):,}")
        
        return "\n".join(lines)


def test_adaptive():
    """测试自适应策略"""
    adaptive = AdaptiveStrategy()
    
    print("=" * 50)
    print("自适应策略测试")
    print("=" * 50)
    
    # 双色球
    print("\n【双色球】")
    print(adaptive.get_weights_explanation('ssq'))
    ssq_recs = adaptive.generate_adaptive_recommendation('ssq', 5)
    
    for i, rec in enumerate(ssq_recs, 1):
        red = ' '.join(f"{n:02d}" for n in rec['red'])
        blue = ' '.join(f"{n:02d}" for n in rec['blue'])
        strategy = rec.get('strategy_name', '未知')
        print(f"  {i}. [{strategy}] 🔴 {red} + 🔵 {blue}")
    
    # 大乐透
    print("\n【大乐透】")
    print(adaptive.get_weights_explanation('dlt'))
    dlt_recs = adaptive.generate_adaptive_recommendation('dlt', 5)
    
    for i, rec in enumerate(dlt_recs, 1):
        front = ' '.join(f"{n:02d}" for n in rec['front'])
        back = ' '.join(f"{n:02d}" for n in rec['back'])
        strategy = rec.get('strategy_name', '未知')
        print(f"  {i}. [{strategy}] 🔴 {front} + 🔵 {back}")


if __name__ == "__main__":
    test_adaptive()
