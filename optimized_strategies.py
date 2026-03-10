#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化后的彩票策略模块
基于回测结果改进：
1. 减少投注数量（从 5 注减到 2 注）
2. 提高单注质量
3. 结合多种策略信号
4. 增加止损机制
"""

import random
from typing import Dict, List, Tuple
from datetime import datetime
from collections import Counter


class OptimizedStrategies:
    """优化后的彩票策略类"""
    
    def __init__(self, storage):
        self.storage = storage
        self.last_investment = {}  # 追踪投入
        self.stop_loss_limit = 0.7  # 止损线：亏损 70% 时减少投注
    
    def get_cold_hot_numbers(self, lottery_type: str, period: int = 30) -> Dict:
        """获取冷热号"""
        return self.storage.get_cold_hot_numbers(lottery_type, period)
    
    def get_omission_data(self, lottery_type: str, period: int = 50) -> Dict:
        """获取遗漏数据"""
        history = self.storage.get_history(lottery_type, period)
        if not history:
            return {}
        
        omission = {}
        if lottery_type == 'dlt':
            # 前区遗漏
            for i in range(1, 36):
                count = 0
                for h in history:
                    front = h.get('numbers', {}).get('front', [])
                    if i in front:
                        omission[f'front_{i}'] = count
                        break
                    count += 1
                else:
                    omission[f'front_{i}'] = count
            
            # 后区遗漏
            for i in range(1, 13):
                count = 0
                for h in history:
                    back = h.get('numbers', {}).get('back', [])
                    if i in back:
                        omission[f'back_{i}'] = count
                        break
                    count += 1
                else:
                    omission[f'back_{i}'] = count
        
        return omission
    
    def dlt_optimized(self, capital: float = 10000, total_invested: float = 0) -> List[Dict]:
        """
        优化策略 1: 智能冷热 + 遗漏分析
        
        核心思路：
        - 热号（近期频繁出现）保持关注
        - 冷号遗漏超过 15 期时重点关注（可能反弹）
        - 每期只投 2 注，提高质量
        """
        cold_hot = self.get_cold_hot_numbers('dlt', 50)
        omission = self.get_omission_data('dlt', 50)
        
        recommendations = []
        
        # 前区热号（出现频率高）
        front_hot = cold_hot.get('hot', [])[:15]
        # 前区冷号（出现频率低）
        front_cold = cold_hot.get('cold', [])[:10]
        # 前区遗漏>15 的号码（可能反弹）
        front_omission_high = [int(k.replace('front_', '')) 
                               for k, v in omission.items() 
                               if k.startswith('front_') and v > 15][:8]
        
        # 后区热号
        back_hot = [n for n in cold_hot.get('hot', []) if n <= 12][:8]
        # 后区冷号
        back_cold = [n for n in cold_hot.get('cold', []) if n <= 12][:6]
        # 后区遗漏>8 的号码
        back_omission_high = [int(k.replace('back_', '')) 
                              for k, v in omission.items() 
                              if k.startswith('back_') and v > 8][:4]
        
        # 根据资金状况调整投注
        loss_rate = total_invested / capital if capital > 0 else 0
        num_bets = 2 if loss_rate < self.stop_loss_limit else 1  # 亏损严重时减为 1 注
        
        for _ in range(num_bets):
            # 策略 A: 3 热 +1 冷 +1 遗漏反弹
            front_a = []
            if len(front_hot) >= 3:
                front_a.extend(random.sample(front_hot, 3))
            if len(front_cold) >= 1:
                front_a.append(random.choice(front_cold))
            if len(front_omission_high) >= 1:
                front_a.append(random.choice(front_omission_high))
            
            # 补齐 5 个
            while len(front_a) < 5:
                n = random.randint(1, 35)
                if n not in front_a:
                    front_a.append(n)
            front_a = sorted(list(set(front_a)))[:5]
            
            # 后区：1 热 +1 遗漏（确保 2 个）
            back_a = []
            if len(back_hot) >= 1:
                back_a.append(random.choice(back_hot))
            if len(back_omission_high) >= 1:
                candidate = random.choice(back_omission_high)
                if candidate not in back_a:
                    back_a.append(candidate)
            if len(back_a) < 2:
                back_a.append(random.choice(back_cold) if back_cold else random.randint(1, 12))
            back_a = sorted(list(set(back_a)))[:2]
            # 确保至少 2 个
            while len(back_a) < 2:
                n = random.randint(1, 12)
                if n not in back_a:
                    back_a.append(n)
            
            recommendations.append({
                'strategy': 'optimized_v1',
                'front': front_a,
                'back': back_a,
                'confidence': 'high' if len(front_omission_high) > 0 else 'medium'
            })
            
            # 第二注：偏冷号策略（博反弹）
            if num_bets > 1:
                front_b = []
                if len(front_cold) >= 3:
                    front_b.extend(random.sample(front_cold, 3))
                if len(front_omission_high) >= 2:
                    front_b.extend(random.sample(front_omission_high, 2))
                while len(front_b) < 5:
                    n = random.randint(1, 35)
                    if n not in front_b:
                        front_b.append(n)
                front_b = sorted(list(set(front_b)))[:5]
                
                back_b = []
                if len(back_cold) >= 1:
                    back_b.append(random.choice(back_cold))
                if len(back_omission_high) >= 1:
                    back_b.append(random.choice(back_omission_high))
                else:
                    back_b.append(random.randint(1, 12))
                back_b = sorted(list(set(back_b)))[:2]
                
                recommendations.append({
                    'strategy': 'optimized_v2_cold_rebound',
                    'front': front_b,
                    'back': back_b,
                    'confidence': 'medium'
                })
        
        return recommendations
    
    def dlt_ml_enhanced(self, ml_model=None) -> List[Dict]:
        """
        优化策略 2: 机器学习增强
        
        如果有 ML 模型，使用模型预测；否则回退到统计策略
        """
        if ml_model:
            # TODO: 集成 ML 预测
            pass
        
        # 回退到统计策略
        return self.dlt_optimized()
    
    def get_adaptive_bet_amount(self, capital: float, total_invested: float, 
                                 recent_win: float) -> int:
        """
        自适应投注金额
        
        根据资金状况和中奖情况调整每期投注：
        - 连胜时保持
        - 连败时减少
        - 接近止损线时大幅减少
        """
        base_bet = 4  # 基础投注 2 注 x2 元
        
        loss_rate = total_invested / capital if capital > 0 else 0
        win_rate = recent_win / total_invested if total_invested > 0 else 0
        
        if loss_rate > 0.8:
            return 2  # 亏损 80% 时，只投 1 注
        elif loss_rate > 0.6:
            return 4  # 亏损 60-80% 时，投 2 注
        elif win_rate > 0.3:
            return 6  # 中奖率>30% 时，投 3 注
        else:
            return 4  # 正常情况 2 注
    
    def generate_report(self, results: Dict) -> str:
        """生成回测报告"""
        report = []
        report.append("=" * 70)
        report.append("📊 优化策略回测报告")
        report.append("=" * 70)
        
        for strategy, data in results.items():
            report.append(f"\n【{strategy}】")
            report.append(f"   最终资金：¥{data.get('final_capital', 0)}")
            report.append(f"   收益率：{data.get('roi', 0):.2f}%")
            report.append(f"   中奖率：{data.get('win_rate', 0):.2f}%")
        
        report.append("\n" + "=" * 70)
        return "\n".join(report)
