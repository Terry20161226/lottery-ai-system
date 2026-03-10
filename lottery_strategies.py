#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票推荐策略模块 - 7 种策略（支持动态权重优化）
"""

import random
from typing import Dict, List, Tuple
from datetime import datetime


class LotteryStrategies:
    """彩票推荐策略类"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def get_cold_hot_numbers(self, lottery_type: str, period: int = 30) -> Dict:
        """获取冷热号"""
        return self.storage.get_cold_hot_numbers(lottery_type, period)
    
    def get_recent_patterns(self, lottery_type: str, periods: int = 30) -> Dict:
        """获取近期形态特征"""
        return self.storage.get_recent_patterns(lottery_type, periods)
    
    # ========== 双色球策略 ==========
    
    def ssq_balanced(self) -> List[Dict]:
        """策略 1: 均衡策略 - 4 热 2 冷"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        red_hot = [n for n in cold_hot["hot"] if n <= 33][:15]
        red_cold = [n for n in cold_hot["cold"] if n <= 33][:10]
        blue_hot = [n for n in cold_hot["hot"] if n <= 16][:8]
        blue_cold = [n for n in cold_hot["cold"] if n <= 16][:5]
        
        for _ in range(5):
            red = random.sample(red_hot, 4) + random.sample(red_cold, 2)
            while len(set(red)) < 6:
                red.append(random.randint(1, 33))
            red = sorted(list(set(red)))[:6]
            
            blue = random.sample(blue_hot + blue_cold, 1)
            
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_hot_tracking(self) -> List[Dict]:
        """策略 2: 热号追踪 - 全热号"""
        cold_hot = self.get_cold_hot_numbers('ssq', 20)
        recommendations = []
        
        red_hot = [n for n in cold_hot["hot"] if n <= 33][:20]
        blue_hot = [n for n in cold_hot["hot"] if n <= 16][:10]
        
        for _ in range(5):
            red = sorted(random.sample(red_hot, 6))
            blue = [random.choice(blue_hot)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_cold_rebound(self) -> List[Dict]:
        """策略 3: 冷号反弹 - 专挑冷号"""
        cold_hot = self.get_cold_hot_numbers('ssq', 50)
        recommendations = []
        
        red_cold = [n for n in cold_hot["cold"] if n <= 33][:15]
        blue_cold = [n for n in cold_hot["cold"] if n <= 16][:8]
        
        for _ in range(5):
            red = sorted(random.sample(red_cold, 6))
            blue = [random.choice(blue_cold)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_odd_even(self) -> List[Dict]:
        """策略 4: 奇偶均衡 - 3:3 比例"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        all_red = list(range(1, 34))
        odd_red = [n for n in all_red if n % 2 == 1]
        even_red = [n for n in all_red if n % 2 == 0]
        
        all_blue = list(range(1, 17))
        odd_blue = [n for n in all_blue if n % 2 == 1]
        even_blue = [n for n in all_blue if n % 2 == 0]
        
        for _ in range(5):
            red = sorted(random.sample(odd_red, 3) + random.sample(even_red, 3))
            blue = [random.choice(random.choice([odd_blue, even_blue]))]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_zone_distribution(self) -> List[Dict]:
        """策略 5: 区间分布 - 三区各 2 码"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        zone1 = list(range(1, 12))   # 01-11
        zone2 = list(range(12, 23))  # 12-22
        zone3 = list(range(23, 34))  # 23-33
        
        blue_all = list(range(1, 17))
        
        for _ in range(5):
            red = sorted(random.sample(zone1, 2) + random.sample(zone2, 2) + random.sample(zone3, 2))
            blue = [random.choice(blue_all)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_consecutive(self) -> List[Dict]:
        """策略 6: 连号追踪 - 包含 2-3 连号"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        all_red = list(range(1, 34))
        blue_all = list(range(1, 17))
        
        for _ in range(5):
            # 生成连号起点
            start = random.randint(1, 30)
            consecutive = [start, start + 1]
            
            # 再选 4 个不重复的号码
            remaining = [n for n in all_red if n not in consecutive]
            others = random.sample(remaining, 4)
            
            red = sorted(consecutive + others)
            blue = [random.choice(blue_all)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_warm_balance(self) -> List[Dict]:
        """策略 7: 温号搭配 - 3 热 2 温 1 冷"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        hot = [n for n in cold_hot["hot"] if n <= 33][:12]
        cold = [n for n in cold_hot["cold"] if n <= 33][:10]
        all_red = list(range(1, 34))
        warm = [n for n in all_red if n not in hot and n not in cold][:15]
        
        blue_all = list(range(1, 17))
        
        for _ in range(5):
            red = sorted(random.sample(hot, 3) + random.sample(warm, 2) + random.sample(cold, 1))
            blue = [random.choice(blue_all)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    # ========== 大乐透策略 ==========
    
    def dlt_balanced(self) -> List[Dict]:
        """策略 1: 均衡策略 - 3 热 2 冷"""
        cold_hot = self.get_cold_hot_numbers('dlt', 30)
        recommendations = []
        
        front_hot = [n for n in cold_hot["hot"] if n <= 35][:15]
        front_cold = [n for n in cold_hot["cold"] if n <= 35][:10]
        back_hot = [n for n in cold_hot["hot"] if n <= 12][:6]
        back_cold = [n for n in cold_hot["cold"] if n <= 12][:5]
        
        for _ in range(5):
            front = random.sample(front_hot, 3) + random.sample(front_cold, 2)
            while len(set(front)) < 5:
                front.append(random.randint(1, 35))
            front = sorted(list(set(front)))[:5]
            
            back = sorted(random.sample(back_hot + back_cold, 2))
            
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_hot_tracking(self) -> List[Dict]:
        """策略 2: 热号追踪"""
        cold_hot = self.get_cold_hot_numbers('dlt', 20)
        recommendations = []
        
        front_hot = [n for n in cold_hot["hot"] if n <= 35][:18]
        back_hot = [n for n in cold_hot["hot"] if n <= 12][:8]
        
        for _ in range(5):
            front = sorted(random.sample(front_hot, 5))
            back = sorted(random.sample(back_hot, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_cold_rebound(self) -> List[Dict]:
        """策略 3: 冷号反弹"""
        cold_hot = self.get_cold_hot_numbers('dlt', 50)
        recommendations = []
        
        front_cold = [n for n in cold_hot["cold"] if n <= 35][:15]
        back_cold = [n for n in cold_hot["cold"] if n <= 12][:8]
        
        # 确保样本足够
        all_front = list(range(1, 36))
        all_back = list(range(1, 13))
        while len(front_cold) < 20:
            n = random.choice(all_front)
            if n not in front_cold:
                front_cold.append(n)
        while len(back_cold) < 10:
            n = random.choice(all_back)
            if n not in back_cold:
                back_cold.append(n)
        
        for _ in range(5):
            front = sorted(random.sample(front_cold, 5))
            back = sorted(random.sample(back_cold, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_odd_even(self) -> List[Dict]:
        """策略 4: 奇偶均衡"""
        all_front = list(range(1, 36))
        odd_front = [n for n in all_front if n % 2 == 1]
        even_front = [n for n in all_front if n % 2 == 0]
        
        all_back = list(range(1, 13))
        odd_back = [n for n in all_back if n % 2 == 1]
        even_back = [n for n in all_back if n % 2 == 0]
        
        recommendations = []
        for _ in range(5):
            front = sorted(random.sample(odd_front, 3) + random.sample(even_front, 2))
            back = sorted([random.choice(odd_back), random.choice(even_back)])
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_zone_distribution(self) -> List[Dict]:
        """策略 5: 区间分布"""
        zone1 = list(range(1, 13))   # 01-12
        zone2 = list(range(13, 24))  # 13-23
        zone3 = list(range(24, 36))  # 24-35
        
        all_back = list(range(1, 13))
        
        recommendations = []
        for _ in range(5):
            front = sorted(random.sample(zone1, 2) + random.sample(zone2, 2) + random.sample(zone3, 1))
            back = sorted(random.sample(all_back, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_consecutive(self) -> List[Dict]:
        """策略 6: 连号追踪"""
        all_front = list(range(1, 36))
        all_back = list(range(1, 13))
        
        recommendations = []
        for _ in range(5):
            start = random.randint(1, 32)
            consecutive = [start, start + 1]
            
            remaining = [n for n in all_front if n not in consecutive]
            others = random.sample(remaining, 3)
            
            front = sorted(consecutive + others)
            back = sorted(random.sample(all_back, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_warm_balance(self) -> List[Dict]:
        """策略 7: 温号搭配 - 3 热 1 温 1 冷"""
        cold_hot = self.get_cold_hot_numbers('dlt', 30)
        recommendations = []
        
        hot = [n for n in cold_hot["hot"] if n <= 35][:12]
        cold = [n for n in cold_hot["cold"] if n <= 35][:10]
        all_front = list(range(1, 36))
        warm = [n for n in all_front if n not in hot and n not in cold][:15]
        
        back_hot = [n for n in cold_hot["hot"] if n <= 12][:6]
        back_cold = [n for n in cold_hot["cold"] if n <= 12][:5]
        
        for _ in range(5):
            front = sorted(random.sample(hot, 3) + random.sample(warm, 1) + random.sample(cold, 1))
            back = sorted(random.sample(back_hot + back_cold, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def get_all_strategies(self, lottery_type: str) -> Dict[str, callable]:
        """获取所有策略"""
        if lottery_type == 'ssq':
            return {
                'balanced': self.ssq_balanced,
                'hot_tracking': self.ssq_hot_tracking,
                'cold_rebound': self.ssq_cold_rebound,
                'odd_even': self.ssq_odd_even,
                'zone_distribution': self.ssq_zone_distribution,
                'consecutive': self.ssq_consecutive,
                'warm_balance': self.ssq_warm_balance,
            }
        elif lottery_type == 'dlt':
            return {
                'balanced': self.dlt_balanced,
                'hot_tracking': self.dlt_hot_tracking,
                'cold_rebound': self.dlt_cold_rebound,
                'odd_even': self.dlt_odd_even,
                'zone_distribution': self.dlt_zone_distribution,
                'consecutive': self.dlt_consecutive,
                'warm_balance': self.dlt_warm_balance,
            }
        
        return {}
    
    # ========== 优化策略 ==========
    
    def ssq_sum_optimized(self, target_sum_range=(80, 120)) -> List[Dict]:
        """策略 8: 和值优化 - 控制和值在目标范围"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        all_red = list(range(1, 34))
        blue_all = list(range(1, 17))
        
        for _ in range(5):
            # 尝试生成符合和值范围的号码
            for _ in range(10):  # 最多尝试 10 次
                red = sorted(random.sample(all_red, 6))
                if target_sum_range[0] <= sum(red) <= target_sum_range[1]:
                    break
            blue = [random.choice(blue_all)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def ssq_span_optimized(self, target_span_range=(20, 30)) -> List[Dict]:
        """策略 9: 跨度优化 - 控制跨度在目标范围"""
        cold_hot = self.get_cold_hot_numbers('ssq', 30)
        recommendations = []
        
        all_red = list(range(1, 34))
        blue_all = list(range(1, 17))
        
        for _ in range(5):
            for _ in range(10):
                red = sorted(random.sample(all_red, 6))
                span = red[-1] - red[0]
                if target_span_range[0] <= span <= target_span_range[1]:
                    break
            blue = [random.choice(blue_all)]
            recommendations.append({"red": red, "blue": blue})
        
        return recommendations
    
    def dlt_sum_optimized(self, target_sum_range=(60, 100)) -> List[Dict]:
        """策略 8: 和值优化（大乐透）"""
        cold_hot = self.get_cold_hot_numbers('dlt', 30)
        recommendations = []
        
        all_front = list(range(1, 36))
        all_back = list(range(1, 13))
        
        for _ in range(5):
            for _ in range(10):
                front = sorted(random.sample(all_front, 5))
                if target_sum_range[0] <= sum(front) <= target_sum_range[1]:
                    break
            back = sorted(random.sample(all_back, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
    
    def dlt_span_optimized(self, target_span_range=(15, 30)) -> List[Dict]:
        """策略 9: 跨度优化（大乐透）"""
        recommendations = []
        
        all_front = list(range(1, 36))
        all_back = list(range(1, 13))
        
        for _ in range(5):
            for _ in range(10):
                front = sorted(random.sample(all_front, 5))
                span = front[-1] - front[0]
                if target_span_range[0] <= span <= target_span_range[1]:
                    break
            back = sorted(random.sample(all_back, 2))
            recommendations.append({"front": front, "back": back})
        
        return recommendations
