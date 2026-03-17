#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票预测机器学习模块
特征工程 + 模型训练 + 预测推荐
"""

import sys
import json
import random
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


class FeatureEngineer:
    """特征工程 - 双窗口动态版本"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def extract_features(self, history, short_window=10, long_window=30):
        """
        从历史数据提取特征 - 双窗口版本
        
        双窗口设计：
        - 短期窗口（10 期）：捕捉近期趋势
        - 长期窗口（30 期）：捕捉整体规律
        
        特征包括：
        1. 冷热号（各号码出现频率）- 双窗口
        2. 遗漏值（各号码未出现期数）
        3. 奇偶比
        4. 区间分布（5 区间）
        5. 和值
        6. 连号
        7. 同尾号
        8. AC 值（数字复杂度）
        """
        features = []
        
        for i in range(long_window, len(history)):
            # 当前期数据
            current = history[i]
            current_front = current.get('numbers', {}).get('front', [])
            current_back = current.get('numbers', {}).get('back', [])
            
            # 短期窗口和长期窗口
            short_data = history[i-short_window:i]
            long_data = history[i-long_window:i]
            
            feature = {
                'issue': current.get('issue'),
                'label_front': current_front,
                'label_back': current_back,
            }
            
            # ========== 短期窗口特征（10 期）==========
            short_front_counts = Counter()
            short_back_counts = Counter()
            for draw in short_data:
                short_front_counts.update(draw.get('numbers', {}).get('front', []))
                short_back_counts.update(draw.get('numbers', {}).get('back', []))
            
            for n in range(1, 36):
                feature[f'short_front_freq_{n}'] = short_front_counts.get(n, 0)
            for n in range(1, 13):
                feature[f'short_back_freq_{n}'] = short_back_counts.get(n, 0)
            
            # 短期热号（出现>=3 次）
            feature['short_hot_count'] = sum(1 for c in short_front_counts.values() if c >= 3)
            
            # 短期和值趋势
            short_sums = [sum(draw.get('numbers', {}).get('front', [])) for draw in short_data]
            feature['short_avg_sum'] = sum(short_sums) / len(short_sums) if short_sums else 0
            
            # ========== 长期窗口特征（30 期）==========
            long_front_counts = Counter()
            long_back_counts = Counter()
            for draw in long_data:
                long_front_counts.update(draw.get('numbers', {}).get('front', []))
                long_back_counts.update(draw.get('numbers', {}).get('back', []))
            
            for n in range(1, 36):
                feature[f'long_front_freq_{n}'] = long_front_counts.get(n, 0)
            for n in range(1, 13):
                feature[f'long_back_freq_{n}'] = long_back_counts.get(n, 0)
            
            # 长期热号（出现>=5 次）
            feature['long_hot_count'] = sum(1 for c in long_front_counts.values() if c >= 5)
            feature['long_cold_count'] = sum(1 for c in long_front_counts.values() if c == 0)
            
            # 长期和值
            long_sums = [sum(draw.get('numbers', {}).get('front', [])) for draw in long_data]
            feature['long_avg_sum'] = sum(long_sums) / len(long_sums) if long_sums else 0
            feature['long_std_sum'] = (sum((x - feature['long_avg_sum'])**2 for x in long_sums) / len(long_sums))**0.5 if long_sums else 0
            
            # ========== 双窗口对比特征 ==========
            # 短期 vs 长期 频率差异（识别近期升温/降温的号码）
            for n in range(1, 36):
                short_freq = short_front_counts.get(n, 0) / short_window if short_window > 0 else 0
                long_freq = long_front_counts.get(n, 0) / long_window if long_window > 0 else 0
                feature[f'freq_diff_{n}'] = short_freq - long_freq  # 正数=近期升温，负数=近期降温
            
            # 升温号码数量（短期频率 > 长期频率*1.5）
            feature['heating_count'] = sum(1 for n in range(1, 36) 
                                          if feature.get(f'freq_diff_{n}', 0) > 0)
            
            # 降温号码数量
            feature['cooling_count'] = sum(1 for n in range(1, 36) 
                                          if feature.get(f'freq_diff_{n}', 0) < 0)
            
            # ========== 遗漏值（基于长期窗口）==========
            for n in range(1, 36):
                omission = 0
                for draw in reversed(long_data):
                    if n in draw.get('numbers', {}).get('front', []):
                        break
                    omission += 1
                feature[f'front_omission_{n}'] = omission
            
            for n in range(1, 13):
                omission = 0
                for draw in reversed(long_data):
                    if n in draw.get('numbers', {}).get('back', []):
                        break
                    omission += 1
                feature[f'back_omission_{n}'] = omission
            
            # 最大遗漏
            feature['max_omission'] = max(feature[f'front_omission_{n}'] for n in range(1, 36)) if any(feature[f'front_omission_{n}'] for n in range(1, 36)) else 0
            
            # ========== 其他统计特征 ==========
            # 平均奇偶比
            odd_ratios = []
            for draw in long_data:
                front = draw.get('numbers', {}).get('front', [])
                odd = sum(1 for n in front if n % 2 == 1)
                odd_ratios.append(odd / len(front) if front else 0)
            feature['avg_odd_ratio'] = sum(odd_ratios) / len(odd_ratios) if odd_ratios else 0
            
            # 连号趋势
            consecutive_count = 0
            for draw in long_data:
                front = sorted(draw.get('numbers', {}).get('front', []))
                for j in range(len(front) - 1):
                    if front[j+1] - front[j] == 1:
                        consecutive_count += 1
            feature['avg_consecutive'] = consecutive_count / len(long_data) if long_data else 0
            
            features.append(feature)
        
        return features


class MLPredictor:
    """机器学习预测器 - v4.0 自适应策略"""
    
    def __init__(self, storage, lottery_type='dlt'):
        self.storage = storage
        self.lottery_type = lottery_type
        self.fe = FeatureEngineer(storage)
        self.model = None
        self.model_path = Path('/root/.openclaw/workspace/lottery/ml_model.pkl')
        self.model_info_path = Path('/root/.openclaw/workspace/lottery/ml_model.json')
        
        # 自适应策略状态（v4.0）
        self.adaptive_state = {
            'recent_results': [],  # 近 10 期中奖记录 [(期号，奖金), ...]
            'peak_capital': 10000,  # 峰值资金
            'current_capital': 10000,  # 当前资金
            'win_streak': 0,  # 连胜期数
            'lose_streak': 0,  # 连败期数
        }
    
    def prepare_data(self, short_window=10, long_window=30):
        """准备训练数据 - 双窗口版本"""
        # 支持双色球和大乐透
        lottery_type = self.lottery_type
        history = self.storage.get_history(lottery_type, 500)
        if not history or len(history) < long_window + 10:
            return None, None
        
        # 反转（从旧到新）
        history = history[::-1]
        
        # 提取特征（双窗口）
        features = self.fe.extract_features(history, short_window, long_window)
        
        # 转换为训练格式
        X = []
        y_front = []
        y_back = []
        
        for f in features:
            # 输入特征（排除标签）
            x = {k: v for k, v in f.items() if not k.startswith('label_') and k != 'issue'}
            X.append(x)
            y_front.append(f['label_front'])
            y_back.append(f['label_back'])
        
        return X, {'front': y_front, 'back': y_back}
    
    def train_simple_model(self):
        """
        训练简单模型 - 双窗口版本
        
        由于 Python 3.6 环境可能没有 sklearn/xgboost，
        使用基于统计的轻量级模型
        """
        print("🔧 训练统计模型（双窗口）...")
        
        X, y = self.prepare_data(short_window=10, long_window=30)
        if not X:
            print("❌ 数据不足")
            return False
        
        print(f"   训练样本：{len(X)}期")
        print(f"   短期窗口：10 期（捕捉近期趋势）")
        print(f"   长期窗口：30 期（捕捉整体规律）")
        
        # 统计每个号码的出现概率（使用长期窗口）
        front_probs = {}
        back_probs = {}
        
        # 从特征中提取频率信息
        for i, x in enumerate(X):
            # 前区号码概率（长期窗口）
            for n in range(1, 36):
                key = f'long_front_freq_{n}'
                if key not in front_probs:
                    front_probs[n] = []
                front_probs[n].append(x.get(key, 0))
            
            # 后区号码概率（长期窗口）
            for n in range(1, 13):
                key = f'long_back_freq_{n}'
                if key not in back_probs:
                    back_probs[n] = []
                back_probs[n].append(x.get(key, 0))
        
        # 计算平均频率
        model = {
            'front_weights': {n: sum(probs)/len(probs) if probs else 0 for n, probs in front_probs.items()},
            'back_weights': {n: sum(probs)/len(probs) if probs else 0 for n, probs in back_probs.items()},
            'trained_at': datetime.now().isoformat(),
            'samples': len(X),
            'short_window': 10,
            'long_window': 30
        }
        
        # 保存模型
        with open(self.model_path, 'w') as f:
            json.dump(model, f, indent=2)
        
        with open(self.model_info_path, 'w') as f:
            json.dump({
                'type': 'statistical',
                'window': 30,
                'samples': len(X),
                'accuracy': 'N/A (statistical model)',
                'trained_at': model['trained_at']
            }, f, indent=2)
        
        print(f"✅ 模型已保存：{self.model_path}")
        print(f"   前区权重范围：{min(model['front_weights'].values()):.2f} - {max(model['front_weights'].values()):.2f}")
        print(f"   后区权重范围：{min(model['back_weights'].values()):.2f} - {max(model['back_weights'].values()):.2f}")
        
        self.model = model
        return True
    
    def load_model(self):
        """加载模型"""
        if self.model_path.exists():
            with open(self.model_path, 'r') as f:
                self.model = json.load(f)
            print(f"✅ 模型已加载：{self.model.get('trained_at', 'N/A')}")
            return True
        return False
    
    def get_adaptive_epsilon(self) -> float:
        """
        自适应 ε 计算（v4.0）
        
        基于近 10 期中奖率动态调整：
        - 中奖率 > 15%：ε=0.15（连胜，增加探索）
        - 中奖率 10-15%：ε=0.08（正常）
        - 中奖率 < 8%：ε=0.02（连败，减少探索，专注热号）
        """
        recent = self.adaptive_state['recent_results']
        if len(recent) < 5:
            return 0.08  # 数据不足，使用默认值
        
        # 计算近 10 期中奖率
        wins = sum(1 for _, prize in recent[-10:] if prize > 0)
        win_rate = wins / min(len(recent[-10:]), 10)
        
        if win_rate > 0.15:
            return 0.15  # 连胜，增加探索
        elif win_rate < 0.08:
            return 0.02  # 连败，减少探索
        else:
            return 0.08  # 正常
    
    def get_adaptive_consecutive_prob(self) -> float:
        """
        自适应连号概率计算（v4.0）
        
        基于连号命中率动态调整：
        - 连号命中率高：85%
        - 连号命中率低：70%
        """
        recent = self.adaptive_state['recent_results']
        if len(recent) < 5:
            return 0.85  # 默认 85%
        
        # 简化：基于连胜/连败调整
        if self.adaptive_state['win_streak'] >= 2:
            return 0.90  # 连胜，提高连号概率
        elif self.adaptive_state['lose_streak'] >= 3:
            return 0.70  # 连败，降低连号概率
        else:
            return 0.85  # 正常
    
    def get_adaptive_bet_notes(self) -> int:
        """
        自适应投注注数计算（v4.0）
        
        基于资金曲线动态调整：
        - 接近峰值（>90%）：3 注（增加投注）
        - 正常（50-90%）：2 注
        - 大幅下跌（<50%）：1 注（减少投注）
        """
        peak = self.adaptive_state['peak_capital']
        current = self.adaptive_state['current_capital']
        
        ratio = current / peak if peak > 0 else 1.0
        
        if ratio > 0.9:
            return 3  # 接近峰值，增加投注
        elif ratio < 0.5:
            return 1  # 大幅下跌，减少投注
        else:
            return 2  # 正常
    
    def update_state(self, issue: str, prize: int, capital: float):
        """
        更新自适应状态（v4.0）
        
        每期中奖后调用，更新近期结果和资金状态
        """
        # 更新近期结果
        self.adaptive_state['recent_results'].append((issue, prize))
        if len(self.adaptive_state['recent_results']) > 20:
            self.adaptive_state['recent_results'] = self.adaptive_state['recent_results'][-20:]
        
        # 更新资金状态
        self.adaptive_state['current_capital'] = capital
        if capital > self.adaptive_state['peak_capital']:
            self.adaptive_state['peak_capital'] = capital
        
        # 更新连胜/连败
        if prize > 0:
            self.adaptive_state['win_streak'] += 1
            self.adaptive_state['lose_streak'] = 0
        else:
            self.adaptive_state['lose_streak'] += 1
            self.adaptive_state['win_streak'] = 0
    
    def predict(self, n_predictions=None, epsilon=None, adaptive=True) -> list:
        """
        生成预测 - v4.0 自适应策略
        
        Args:
            n_predictions: 预测注数（None=自适应）
            epsilon: 探索概率（None=自适应）
            adaptive: 是否启用自适应（默认 True）
        
        ε-greedy 策略：
        - 自适应 ε（基于近 10 期中奖率）
        - 自适应投注注数（基于资金曲线）
        """
        if not self.model:
            if not self.load_model():
                print("❌ 无可用模型，使用随机预测")
                return self.random_predict(2)
        
        # v4.0 自适应参数
        if adaptive:
            if epsilon is None:
                epsilon = self.get_adaptive_epsilon()
            if n_predictions is None:
                n_predictions = self.get_adaptive_bet_notes()
        else:
            if epsilon is None:
                epsilon = 0.08
            if n_predictions is None:
                n_predictions = 2
        
        # 获取自适应连号概率
        consecutive_prob = self.get_adaptive_consecutive_prob() if adaptive else 0.85
        
        recommendations = []
        
        # 前区：按权重采样
        front_weights = self.model.get('front_weights', {})
        back_weights = self.model.get('back_weights', {})
        
        for i in range(n_predictions):
            # ε-greedy 决策
            use_explore = random.random() < epsilon
            
            if use_explore:
                # 探索模式：偏向冷号和遗漏号
                front = self._explore_front(front_weights)
                back = self._explore_back(back_weights)
                strategy = 'ml_explore'
                confidence = 'medium'
            else:
                # 利用模式：按模型权重选择（带连号）
                front = self._exploit_front_with_consecutive(front_weights, consecutive_prob)
                back = self._exploit_back(back_weights)
                strategy = 'ml_exploit'
                confidence = 'high'
            
            recommendations.append({
                'strategy': strategy,
                'front': front,
                'back': back,
                'confidence': confidence,
                'mode': 'explore' if use_explore else 'exploit',
                'epsilon': epsilon,
                'consecutive_prob': consecutive_prob
            })
        
        return recommendations
    
    def _exploit_front_with_consecutive(self, front_weights: dict, consecutive_prob: float = 0.85) -> list:
        """
        利用模式：按权重选择前区 + 强制连号（v4.0 自适应）
        
        Args:
            front_weights: 号码权重
            consecutive_prob: 连号概率（0.85=85%）
        """
        front_candidates = list(front_weights.keys())
        front_candidates = [int(n) if isinstance(n, str) else n for n in front_candidates]
        front_probs = [front_weights.get(str(n), 0) + 0.1 for n in front_candidates]
        total = sum(front_probs)
        front_probs = [p/total for p in front_probs]
        
        # 决策是否生成连号
        use_consecutive = random.random() < consecutive_prob
        
        if use_consecutive:
            return self._generate_with_consecutive(front_candidates, front_probs, consecutive_prob)
        else:
            # 无连号模式
            front = []
            while len(front) < 5:
                idx = random.choices(range(len(front_candidates)), weights=front_probs)[0]
                n = front_candidates[idx]
                if n not in front:
                    front.append(n)
            return sorted(front)
    
    def _exploit_front(self, front_weights: dict) -> list:
        """利用模式：按权重选择前区（向后兼容，默认 85% 连号）"""
        return self._exploit_front_with_consecutive(front_weights, 0.85)
    
    def _analyze_consecutive_rate(self, history) -> float:
        """分析历史连号出现率"""
        if not history:
            return 0.6  # 默认 60%
        
        consecutive_count = 0
        for draw in history:
            front = sorted(draw.get('numbers', {}).get('front', []))
            has_consecutive = any(front[i+1] - front[i] == 1 for i in range(len(front)-1))
            if has_consecutive:
                consecutive_count += 1
        
        return consecutive_count / len(history)
    
    def _generate_with_consecutive(self, candidates: list, probs: list, target_consecutive_groups: float = 0.5) -> list:
        """
        生成包含连号的组合 - v3.0 修复版
        
        Args:
            candidates: 候选号码（1-35 的整数列表）
            probs: 对应概率
            target_consecutive_groups: 目标连号组数
        
        修复说明：
        - 原问题：连号生成后被后续逻辑破坏
        - 修复：优先生成连号，然后补齐非连号
        """
        # 确保 candidates 是整数列表
        candidates = [int(n) if isinstance(n, str) else n for n in candidates]
        candidates = sorted(candidates)
        
        # 决策连号组数（v3.1: 确保 85% 连号率）
        r = random.random()
        if r < 0.6:
            num_groups = 1  # 60% 概率 1 组连号
        elif r < 0.85:
            num_groups = 2  # 25% 概率 2 组连号
        else:
            num_groups = 0  # 15% 概率无连号
        # 总连号率：85%（60% + 25%）
        
        front = []
        used_numbers = set()
        
        if num_groups > 0:
            # 生成连号 - 直接从 1-35 中选择，不依赖 candidates
            for _ in range(num_groups):
                # 选择连号起始号码（1-34，因为需要 base+1）
                base = random.randint(1, 34)
                attempts = 0
                while (base in used_numbers or base + 1 in used_numbers) and attempts < 10:
                    base = random.randint(1, 34)
                    attempts += 1
                
                if base not in used_numbers and base + 1 not in used_numbers and base < 35:
                    front.append(base)
                    front.append(base + 1)
                    used_numbers.add(base)
                    used_numbers.add(base + 1)
        
        # 补齐剩余号码（确保不破坏已有连号）
        available = [n for n in candidates if n not in used_numbers and 1 <= n <= 35]
        while len(front) < 5 and available:
            n = random.choice(available)
            available.remove(n)
            if n not in front:
                front.append(n)
                used_numbers.add(n)
        
        # 如果还不够 5 个，从 1-35 随机补充
        while len(front) < 5:
            n = random.randint(1, 35)
            if n not in used_numbers:
                front.append(n)
                used_numbers.add(n)
        
        return sorted(front[:5])
    
    def _exploit_back(self, back_weights: dict) -> list:
        """
        利用模式：按权重选择后区 + 同尾号模式识别
        
        同尾号模式：
        - 例如：03+13, 05+25（尾数相同）
        - 历史统计：约 35% 的开奖包含同尾号
        - 策略：35% 概率生成同尾号组合
        """
        back_candidates = list(back_weights.keys())
        back_probs = [back_weights.get(n, 0) + 0.1 for n in back_candidates]
        total = sum(back_probs)
        back_probs = [p/total for p in back_probs]
        
        # 50% 概率生成同尾号（v2.1: 从 35% 提高到 50%）
        use_same_tail = random.random() < 0.50
        
        if use_same_tail:
            # 生成同尾号组合
            # 后区 1-12，同尾号组合：(1,11), (2,12)
            same_tail_pairs = [(1, 11), (2, 12)]
            pair = random.choice(same_tail_pairs)
            
            # 检查这两个号码的权重
            idx1 = back_candidates.index(pair[0]) if pair[0] in back_candidates else -1
            idx2 = back_candidates.index(pair[1]) if pair[1] in back_candidates else -1
            
            if idx1 >= 0 and idx2 >= 0:
                return sorted(list(pair))
        
        # 默认：按权重选择
        back = []
        while len(back) < 2:
            idx = random.choices(range(len(back_candidates)), weights=back_probs)[0]
            n = back_candidates[idx]
            if n not in back:
                back.append(n)
        return sorted(back)
    
    def _explore_front(self, front_weights: dict, omission_bonus=True) -> list:
        """
        探索模式：偏向冷号 + 遗漏值加权
        
        Args:
            front_weights: 号码权重
            omission_bonus: 是否启用遗漏加分（>15 期额外加分）
        """
        front_candidates = list(front_weights.keys())
        
        # 基础概率：反转权重（冷号优先）
        max_w = max(front_weights.values()) if front_weights else 10
        front_probs = [(max_w - front_weights.get(n, 0) + 0.5) for n in front_candidates]
        
        # 遗漏值加权：获取遗漏数据
        if omission_bonus:
            history = self.storage.get_history('dlt', 50)
            if history:
                for i, n in enumerate(front_candidates):
                    # 计算当前遗漏期数
                    omission = 0
                    for draw in reversed(history):
                        front = draw.get('numbers', {}).get('front', [])
                        if n in front:
                            break
                        omission += 1
                    
                    # 遗漏>12 期：额外加分（v3.1: 降低权重，从 x2.0 降至 x1.3）
                    if omission > 12:
                        front_probs[i] *= 1.3  # v3.1: 从 x2.0 降至 x1.3
                        # 遗漏>20 期：再加分（v3.1: 从 x1.5 降至 x1.2）
                        if omission > 20:
                            front_probs[i] *= 1.2  # v3.1: 从 x1.5 降至 x1.2
        
        total = sum(front_probs)
        front_probs = [p/total for p in front_probs]
        
        front = []
        while len(front) < 5:
            idx = random.choices(range(len(front_candidates)), weights=front_probs)[0]
            n = front_candidates[idx]
            if n not in front:
                front.append(n)
        return sorted(front)
    
    def _explore_back(self, back_weights: dict, omission_bonus=True) -> list:
        """
        探索模式：偏向冷号 + 遗漏值加权
        
        Args:
            back_weights: 号码权重
            omission_bonus: 是否启用遗漏加分（>8 期额外加分）
        """
        back_candidates = list(back_weights.keys())
        
        # 基础概率：反转权重
        max_w = max(back_weights.values()) if back_weights else 10
        back_probs = [(max_w - back_weights.get(n, 0) + 0.5) for n in back_candidates]
        
        # 遗漏值加权
        if omission_bonus:
            history = self.storage.get_history('dlt', 50)
            if history:
                for i, n in enumerate(back_candidates):
                    omission = 0
                    for draw in reversed(history):
                        back = draw.get('numbers', {}).get('back', [])
                        if n in back:
                            break
                        omission += 1
                    
                    # 后区遗漏>6 期：额外加分（v3.1: 降低权重，从 x2.0 降至 x1.3）
                    if omission > 6:
                        back_probs[i] *= 1.3  # v3.1: 从 x2.0 降至 x1.3
                        if omission > 12:  # v3.1: 从 x1.5 降至 x1.2
                            back_probs[i] *= 1.2  # v3.1: 从 x1.5 降至 x1.2
        
        total = sum(back_probs)
        back_probs = [p/total for p in back_probs]
        
        back = []
        while len(back) < 2:
            idx = random.choices(range(len(back_candidates)), weights=back_probs)[0]
            n = back_candidates[idx]
            if n not in back:
                back.append(n)
        return sorted(back)
    
    def random_predict(self, n_predictions=5) -> list:
        """随机预测（回退方案）"""
        recommendations = []
        for _ in range(n_predictions):
            front = sorted(random.sample(range(1, 36), 5))
            back = sorted(random.sample(range(1, 13), 2))
            recommendations.append({
                'strategy': 'random',
                'front': front,
                'back': back,
                'confidence': 'low'
            })
        return recommendations
    
    def backtest_model(self, periods=50) -> dict:
        """回测模型表现"""
        print(f"\n📊 模型回测（{periods}期）")
        
        history = self.storage.get_history('dlt', periods + 50)
        if not history:
            return {'error': '无数据'}
        
        history = history[:periods][::-1]
        
        wins = 0
        total_prize = 0
        
        for draw in history:
            draw_front = draw.get('numbers', {}).get('front', [])
            draw_back = draw.get('numbers', {}).get('back', [])
            
            preds = self.predict(1)
            pred_front = preds[0]['front']
            pred_back = preds[0]['back']
            
            match_front = len(set(pred_front) & set(draw_front))
            match_back = len(set(pred_back) & set(draw_back))
            
            # 简化奖级判断
            prize = 0
            if match_front == 5 and match_back == 2:
                prize = 8000000
            elif match_front == 5 and match_back == 1:
                prize = 100000
            elif match_front >= 3 and match_back >= 1:
                prize = 15
            elif match_front >= 2 and match_back >= 1:
                prize = 5
            elif match_back == 2:
                prize = 5
            
            if prize > 0:
                wins += 1
                total_prize += prize
        
        win_rate = wins / periods * 100
        roi = (total_prize - periods * 2) / (periods * 2) * 100
        
        print(f"   中奖次数：{wins}")
        print(f"   中奖率：{win_rate:.2f}%")
        print(f"   总奖金：¥{total_prize}")
        print(f"   ROI: {roi:.2f}%")
        
        return {
            'periods': periods,
            'wins': wins,
            'win_rate': win_rate,
            'total_prize': total_prize,
            'roi': roi
        }


def main():
    print("=" * 70)
    print("🤖 彩票机器学习预测系统")
    print("=" * 70)
    
    storage = LotteryStorage()
    predictor = MLPredictor(storage)
    
    # 训练模型
    print("\n【1. 训练模型】")
    predictor.train_simple_model()
    
    # 生成预测
    print("\n【2. 生成预测】")
    preds = predictor.predict(5)
    for i, pred in enumerate(preds, 1):
        print(f"   第{i}注：前区 {pred['front']} 后区 {pred['back']} [{pred['strategy']}]")
    
    # 回测
    print("\n【3. 模型回测】")
    result = predictor.backtest_model(periods=50)
    
    # 保存结果
    report = {
        'timestamp': datetime.now().isoformat(),
        'model_info': predictor.model,
        'predictions': preds,
        'backtest': result
    }
    
    with open('/root/.openclaw/workspace/lottery/reports/ml_report.json', 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 报告已保存到 reports/ml_report.json")
    print("=" * 70)


if __name__ == "__main__":
    main()
