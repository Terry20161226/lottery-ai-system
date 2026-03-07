#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成策略模块 - Ensemble Learning
- 多策略投票
- 加权融合
- 模型堆叠
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
from lottery_strategies import LotteryStrategies
from adaptive_strategy import AdaptiveStrategy
from collections import Counter
import random


class EnsembleStrategy:
    """集成策略生成器"""
    
    def __init__(self):
        self.storage = LotteryStorage()
        self.strategies = LotteryStrategies(self.storage)
        self.adaptive = AdaptiveStrategy()
    
    def generate_ensemble(self, lottery_type: str, num_recommendations: int = 5,
                         method: str = 'voting') -> list:
        """
        生成集成推荐
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            num_recommendations: 推荐注数
            method: 'voting'(投票) / 'weighted'(加权) / 'stacking'(堆叠)
        
        Returns:
            推荐号码列表
        """
        if method == 'voting':
            return self._voting_ensemble(lottery_type, num_recommendations)
        elif method == 'weighted':
            return self._weighted_ensemble(lottery_type, num_recommendations)
        elif method == 'stacking':
            return self._stacking_ensemble(lottery_type, num_recommendations)
        else:
            return self._voting_ensemble(lottery_type, num_recommendations)
    
    def _voting_ensemble(self, lottery_type: str, num: int = 5) -> list:
        """
        投票机制集成
        每个策略生成 10 注，统计每个号码出现频率，选得票最高的组合
        """
        all_strategies = self.strategies.get_all_strategies(lottery_type)
        
        # 每个策略生成 10 注
        all_predictions = []
        for strategy_name, strategy_func in all_strategies.items():
            recs = strategy_func()
            if recs:
                # 扩展为 10 注
                while len(recs) < 10:
                    recs.extend(strategy_func())
                all_predictions.extend(recs[:10])
        
        # 统计号码频率
        if lottery_type == 'ssq':
            red_freq = Counter()
            blue_freq = Counter()
            
            for rec in all_predictions:
                for n in rec.get('red', []):
                    red_freq[n] += 1
                for n in rec.get('blue', []):
                    blue_freq[n] += 1
            
            # 选择频率最高的号码
            top_red = [n for n, _ in red_freq.most_common(18)]  # 前 18 个热号
            top_blue = [n for n, _ in blue_freq.most_common(6)]  # 前 6 个热号
            
            # 生成推荐组合
            recommendations = []
            for _ in range(num):
                red = sorted(random.sample(top_red, 6))
                blue = random.sample(top_blue, 1)
                recommendations.append({'red': red, 'blue': blue})
        
        else:  # dlt
            front_freq = Counter()
            back_freq = Counter()
            
            for rec in all_predictions:
                for n in rec.get('front', []):
                    front_freq[n] += 1
                for n in rec.get('back', []):
                    back_freq[n] += 1
            
            top_front = [n for n, _ in front_freq.most_common(18)]
            top_back = [n for n, _ in back_freq.most_common(8)]
            
            recommendations = []
            for _ in range(num):
                front = sorted(random.sample(top_front, 5))
                back = random.sample(top_back, 2)
                recommendations.append({'front': front, 'back': back})
        
        return recommendations
    
    def _weighted_ensemble(self, lottery_type: str, num: int = 5) -> list:
        """
        加权集成
        根据策略权重生成推荐，权重高的策略贡献更多号码
        """
        weights = self.adaptive.get_adaptive_weights(lottery_type)
        all_strategies = self.strategies.get_all_strategies(lottery_type)
        
        # 根据权重决定每个策略生成多少注
        strategy_counts = {}
        total_weight = sum(weights.values())
        
        for strategy, weight in weights.items():
            count = max(1, round((weight / total_weight) * num * 2))
            strategy_counts[strategy] = count
        
        # 生成推荐池
        prediction_pool = []
        for strategy_name, count in strategy_counts.items():
            strategy_func = all_strategies.get(strategy_name)
            if strategy_func:
                for _ in range(count):
                    recs = strategy_func()
                    if recs:
                        rec = recs[0].copy()
                        rec['strategy'] = strategy_name
                        prediction_pool.append(rec)
        
        # 从池中随机选择 num 注
        if len(prediction_pool) >= num:
            recommendations = random.sample(prediction_pool, num)
        else:
            recommendations = prediction_pool
            # 补充到 num 注
            while len(recommendations) < num:
                recs = self.strategies.balanced()
                if recs:
                    recommendations.append(recs[0])
        
        return recommendations
    
    def _stacking_ensemble(self, lottery_type: str, num: int = 5) -> list:
        """
        堆叠集成
        第一层：各策略生成推荐
        第二层：基于特征选择最优组合
        """
        # 获取特征分析
        features = self.adaptive.analyzer.run_full_analysis(lottery_type)
        
        # 根据特征调整选择策略
        if 'error' in features:
            return self._weighted_ensemble(lottery_type, num)
        
        feature_features = features.get('features', {})
        
        # 特征指导策略选择
        preferred_strategies = []
        
        # 冷热号特征
        cold_hot = feature_features.get('cold_hot', {})
        if cold_hot.get('hot_weight', 0.5) > 0.6:
            preferred_strategies.append('hot_tracking')
        elif cold_hot.get('hot_weight', 0.5) < 0.4:
            preferred_strategies.append('cold_rebound')
        
        # 连号特征
        consecutive = feature_features.get('consecutive', {})
        if consecutive.get('consecutive_rate', 0) > 60:
            preferred_strategies.append('consecutive')
        
        # 区间特征
        zone = feature_features.get('zone_distribution', {})
        if zone.get('best_zone'):
            preferred_strategies.append('zone_distribution')
        
        # 遗漏值特征
        omission = feature_features.get('omission', {})
        if omission.get('max_omission', 0) > 20:
            preferred_strategies.append('cold_rebound')
        
        # 如果没有偏好，使用均衡策略
        if not preferred_strategies:
            preferred_strategies = ['balanced', 'warm_balance']
        
        # 生成推荐
        recommendations = []
        all_strategies = self.strategies.get_all_strategies(lottery_type)
        
        for strategy_name in preferred_strategies[:num]:
            strategy_func = all_strategies.get(strategy_name)
            if strategy_func:
                recs = strategy_func()
                if recs:
                    rec = recs[0].copy()
                    rec['strategy'] = strategy_name
                    recommendations.append(rec)
        
        # 补充到 num 注
        all_strategies = self.strategies.get_all_strategies(lottery_type)
        while len(recommendations) < num:
            strategy_func = all_strategies.get('balanced')
            if strategy_func:
                recs = strategy_func()
                if recs:
                    recommendations.append(recs[0])
            else:
                break
        
        return recommendations
    
    def get_ensemble_explanation(self, recommendations: list, method: str) -> str:
        """获取集成策略说明"""
        lines = [f"【集成策略 - {method}】"]
        
        if method == 'voting':
            lines.append("   机制：7 种策略各生成 10 注，投票选出高频号码")
            lines.append("   优势：综合所有策略，避免单一策略偏差")
        elif method == 'weighted':
            lines.append("   机制：按回测权重分配，表现好的策略贡献更多")
            lines.append("   优势：兼顾历史表现和多样性")
        elif method == 'stacking':
            lines.append("   机制：根据特征分析选择最优策略组合")
            lines.append("   优势：动态适应数据特征")
        
        # 策略分布
        strategy_dist = Counter(rec.get('strategy', 'unknown') for rec in recommendations)
        lines.append("   策略分布：")
        for strategy, count in strategy_dist.most_common():
            lines.append(f"      - {strategy}: {count}注")
        
        return "\n".join(lines)


def main():
    """主函数"""
    ensemble = EnsembleStrategy()
    
    print("=" * 70)
    print("🎰 集成策略推荐系统")
    print("=" * 70)
    
    # 测试三种方法
    methods = ['voting', 'weighted', 'stacking']
    
    for method in methods:
        print(f"\n【{method.upper()} 集成】")
        
        # 双色球
        print("\n双色球推荐：")
        ssq_recs = ensemble.generate_ensemble('ssq', 5, method)
        
        for i, rec in enumerate(ssq_recs, 1):
            red = ' '.join(f"{n:02d}" for n in rec['red'])
            blue = ' '.join(f"{n:02d}" for n in rec['blue'])
            strategy = rec.get('strategy', 'ensemble')
            print(f"  {i}. [{strategy}] 🔴 {red} + 🔵 {blue}")
        
        # 大乐透
        print("\n大乐透推荐：")
        dlt_recs = ensemble.generate_ensemble('dlt', 5, method)
        
        for i, rec in enumerate(dlt_recs, 1):
            front = ' '.join(f"{n:02d}" for n in rec['front'])
            back = ' '.join(f"{n:02d}" for n in rec['back'])
            strategy = rec.get('strategy', 'ensemble')
            print(f"  {i}. [{strategy}] 🔴 {front} + 🔵 {back}")
    
    print("\n" + "=" * 70)
    print("✅ 集成推荐完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
