#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型集成投票预测器 v2 - 优化版
结合多个 ML 模型的预测结果进行投票，自适应权重调整
"""

import sys
import json
import random
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


class EnsemblePredictorV2:
    """多模型集成投票预测器 v2 - 优化版"""
    
    def __init__(self, storage):
        self.storage = storage
        # 基础权重
        self.base_weights = {
            'ml_weighted': 0.40,
            'hot_tracking': 0.25,
            'cold_rebound': 0.20,
            'balanced': 0.15
        }
        # 动态权重（根据近期表现调整）
        self.dynamic_weights = self.base_weights.copy()
        self.last_week_performance = {}
    
    def load_performance_history(self):
        """加载历史表现数据"""
        stats_file = Path('/root/.openclaw/workspace/lottery/stats/strategy_performance.json')
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def adapt_weights(self):
        """根据历史表现自适应调整权重"""
        stats = self.load_performance_history()
        if not stats or not stats.get('daily_records'):
            return
        
        recent_7d = stats['daily_records'][-7:]
        if len(recent_7d) < 3:
            return
        
        # 计算各策略表现（简化版）
        # 实际应该记录每个策略的独立表现
        # 这里使用启发式调整
        
        # 如果近期收益率低，增加冷号权重
        avg_roi = sum(d.get('roi', 0) for d in recent_7d) / len(recent_7d)
        if avg_roi < -50:
            # 表现差时，增加冷号和均衡策略权重
            self.dynamic_weights['cold_rebound'] = 0.30
            self.dynamic_weights['balanced'] = 0.20
            self.dynamic_weights['ml_weighted'] = 0.30
            self.dynamic_weights['hot_tracking'] = 0.20
        elif avg_roi > 20:
            # 表现好时，保持 ML 权重为主
            self.dynamic_weights = self.base_weights.copy()
    
    def ml_weighted_predict(self, history, n_notes=5):
        """ML 权重模型预测"""
        from ml_predictor import MLPredictor
        
        predictor = MLPredictor(self.storage)
        predictor.prepare_data()
        notes = predictor.predict(n_predictions=n_notes)
        return [{'front': note.get('front', []), 'back': note.get('back', [])} for note in notes]
    
    def hot_tracking_predict(self, history, n_notes=5):
        """热号追踪模型 - 选择近期高频号码"""
        if len(history) < 10:
            return self._random_notes(n_notes)
        
        # 统计最近 10 期热号
        recent = history[-10:]
        front_counts = Counter()
        back_counts = Counter()
        
        for draw in recent:
            front_counts.update(draw.get('numbers', {}).get('front', []))
            back_counts.update(draw.get('numbers', {}).get('back', []))
        
        # 选择热号（出现次数>=2 的）
        hot_front = [n for n, c in front_counts.items() if c >= 2]
        hot_back = [n for n, c in back_counts.items() if c >= 1]
        
        # 如果热号不足，补充随机号
        if len(hot_front) < 5:
            hot_front.extend([n for n in range(1, 36) if n not in hot_front][:10])
        if len(hot_back) < 2:
            hot_back.extend([n for n in range(1, 13) if n not in hot_back][:4])
        
        notes = []
        for _ in range(n_notes):
            front = sorted(random.sample(hot_front, 5))
            back = sorted(random.sample(hot_back, 2))
            notes.append({'front': front, 'back': back})
        
        return notes
    
    def cold_rebound_predict(self, history, n_notes=5):
        """冷号反弹模型 - 选择遗漏久的号码"""
        if len(history) < 30:
            return self._random_notes(n_notes)
        
        # 计算遗漏值
        omission = {n: 0 for n in range(1, 36)}
        for draw in reversed(history[-30:]):
            for n in draw.get('numbers', {}).get('front', []):
                omission[n] = 0
            for n in omission:
                if n not in draw.get('numbers', {}).get('front', []):
                    omission[n] += 1
        
        # 选择冷号（遗漏值>=5 的）
        cold_front = [n for n, v in omission.items() if v >= 5]
        if len(cold_front) < 5:
            cold_front = sorted(omission.keys(), key=lambda x: omission[x], reverse=True)[:15]
        
        notes = []
        for _ in range(n_notes):
            front = sorted(random.sample(cold_front, 5))
            back = sorted(random.sample(range(1, 13), 2))
            notes.append({'front': front, 'back': back})
        
        return notes
    
    def balanced_predict(self, history, n_notes=5):
        """均衡策略模型 - 奇偶/区间均衡"""
        notes = []
        for _ in range(n_notes):
            # 奇偶比 2:3 或 3:2
            odd_count = random.choice([2, 3])
            even_count = 5 - odd_count
            
            odds = random.sample(range(1, 36, 2), odd_count)
            evens = random.sample(range(2, 36, 2), even_count)
            front = sorted(odds + evens)
            
            # 大小比均衡（至少 2 个大号 2 个小号）
            small = [n for n in front if n <= 18]
            large = [n for n in front if n > 18]
            if len(small) < 2 or len(large) < 2:
                continue
            
            # 区间分布（5 区间，每区间最多 2 个）
            zones = [0] * 5
            for n in front:
                zone = (n - 1) // 7
                zones[zone] += 1
            
            if max(zones) <= 2:
                back = sorted(random.sample(range(1, 13), 2))
                notes.append({'front': front, 'back': back})
        
        # 补齐注数
        while len(notes) < n_notes:
            front = sorted(random.sample(range(1, 36), 5))
            back = sorted(random.sample(range(1, 13), 2))
            notes.append({'front': front, 'back': back})
        
        return notes[:n_notes]
    
    def _random_notes(self, n_notes=5):
        """随机生成注数"""
        notes = []
        for _ in range(n_notes):
            front = sorted(random.sample(range(1, 36), 5))
            back = sorted(random.sample(range(1, 13), 2))
            notes.append({'front': front, 'back': back})
        return notes
    
    def ensemble_vote(self, history, n_notes=5):
        """
        多模型投票集成 v2 - 优化版
        
        优化点：
        1. 自适应权重调整
        2. 增加置信度计算
        3. 避免重复号码组合
        4. 智能去重
        """
        # 自适应权重
        self.adapt_weights()
        
        # 各模型生成候选
        ml_notes = self.ml_weighted_predict(history, n_notes * 2)
        hot_notes = self.hot_tracking_predict(history, n_notes * 2)
        cold_notes = self.cold_rebound_predict(history, n_notes * 2)
        balanced_notes = self.balanced_predict(history, n_notes * 2)
        
        # 统计投票
        front_votes = Counter()
        back_votes = Counter()
        
        # 加权投票
        for note in ml_notes:
            for n in note['front']:
                front_votes[n] += self.dynamic_weights['ml_weighted']
            for n in note['back']:
                back_votes[n] += self.dynamic_weights['ml_weighted']
        
        for note in hot_notes:
            for n in note['front']:
                front_votes[n] += self.dynamic_weights['hot_tracking']
            for n in note['back']:
                back_votes[n] += self.dynamic_weights['hot_tracking']
        
        for note in cold_notes:
            for n in note['front']:
                front_votes[n] += self.dynamic_weights['cold_rebound']
            for n in note['back']:
                back_votes[n] += self.dynamic_weights['cold_rebound']
        
        for note in balanced_notes:
            for n in note['front']:
                front_votes[n] += self.dynamic_weights['balanced']
            for n in note['back']:
                back_votes[n] += self.dynamic_weights['balanced']
        
        # 生成最终推荐
        final_notes = []
        seen_combinations = set()
        
        for _ in range(n_notes * 2):  # 生成更多候选，然后筛选
            # 选择得票最多的前区号码
            top_front = [int(n) for n, v in front_votes.most_common(12)]
            front = sorted(random.sample(top_front, min(5, len(top_front))))
            
            # 选择得票最多的后区号码
            top_back = [int(n) for n, v in back_votes.most_common(8)]
            back = sorted(random.sample(top_back, min(2, len(top_back))))
            
            # 确保号码有效
            if len(front) < 5:
                front = sorted(random.sample(range(1, 36), 5))
            if len(back) < 2:
                back = sorted(random.sample(range(1, 13), 2))
            
            # 去重
            combo_key = f"{front}+{back}"
            if combo_key in seen_combinations:
                continue
            seen_combinations.add(combo_key)
            
            # 计算置信度
            confidence = sum(front_votes.get(n, 0) for n in front) / 5
            
            final_notes.append({
                'front': front,
                'back': back,
                'confidence': confidence
            })
            
            if len(final_notes) >= n_notes:
                break
        
        # 按置信度排序
        final_notes.sort(key=lambda x: x['confidence'], reverse=True)
        
        return final_notes
    
    def get_weight_report(self):
        """获取权重报告"""
        return {
            'base_weights': self.base_weights,
            'dynamic_weights': self.dynamic_weights,
            'adapted': self.dynamic_weights != self.base_weights
        }


def main():
    print("=" * 70)
    print("🤖 多模型集成投票预测 v2 - 优化版")
    print("=" * 70)
    
    storage = LotteryStorage()
    history = storage.get_history('dlt', 50)
    
    if not history:
        print("❌ 无历史数据")
        return
    
    print(f"✅ 加载历史数据：{len(history)} 期")
    
    predictor = EnsemblePredictorV2(storage)
    
    # 显示权重配置
    weight_report = predictor.get_weight_report()
    print(f"\n📊 模型权重配置：")
    for model, weight in weight_report['base_weights'].items():
        dynamic = weight_report['dynamic_weights'][model]
        adapted = "✨" if dynamic != weight else ""
        print(f"   {model}: {weight*100:.0f}% → {dynamic*100:.0f}% {adapted}")
    
    if weight_report['adapted']:
        print(f"   💡 权重已根据近期表现自适应调整")
    
    # 生成推荐
    notes = predictor.ensemble_vote(history, n_notes=5)
    
    print(f"\n🎯 推荐号码（按置信度排序）：")
    for i, note in enumerate(notes, 1):
        front_str = ' '.join(f"{n:02d}" for n in note['front'])
        back_str = ' '.join(f"{n:02d}" for n in note['back'])
        conf = note.get('confidence', 0) * 100
        print(f"   第{i}注：{front_str} + {back_str}  (置信度：{conf:.1f}%)")
    
    # 保存推荐
    report = {
        'timestamp': datetime.now().isoformat(),
        'model': 'ensemble_voting_v2',
        'weights': weight_report,
        'history_periods': len(history),
        'notes': notes
    }
    
    report_file = Path('/root/.openclaw/workspace/lottery/reports/ensemble_prediction_v2.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已保存：reports/ensemble_prediction_v2.json")


if __name__ == "__main__":
    main()
