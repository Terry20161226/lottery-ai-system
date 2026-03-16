#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模型集成投票预测器
结合多个 ML 模型的预测结果进行投票
"""

import sys
import json
import random
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


class EnsemblePredictor:
    """多模型集成投票预测器"""
    
    def __init__(self, storage):
        self.storage = storage
        self.models = {
            'ml_weighted': 0.4,      # ML 权重模型
            'hot_tracking': 0.25,    # 热号追踪模型
            'cold_rebound': 0.2,     # 冷号反弹模型
            'balanced': 0.15         # 均衡策略模型
        }
    
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
        
        # 选择热号
        hot_front = [n for n, c in front_counts.most_common(15)]
        hot_back = [n for n, c in back_counts.most_common(4)]
        
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
        
        # 选择冷号
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
            
            # 大小比均衡
            small = [n for n in front if n <= 18]
            large = [n for n in front if n > 18]
            if len(small) < 2 or len(large) < 2:
                # 重新生成
                continue
            
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
        多模型投票集成
        
        投票机制：
        1. 每个模型生成候选号码
        2. 统计每个号码的投票数
        3. 选择得票最多的号码组合
        """
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
                front_votes[n] += self.models['ml_weighted']
            for n in note['back']:
                back_votes[n] += self.models['ml_weighted']
        
        for note in hot_notes:
            for n in note['front']:
                front_votes[n] += self.models['hot_tracking']
            for n in note['back']:
                back_votes[n] += self.models['hot_tracking']
        
        for note in cold_notes:
            for n in note['front']:
                front_votes[n] += self.models['cold_rebound']
            for n in note['back']:
                back_votes[n] += self.models['cold_rebound']
        
        for note in balanced_notes:
            for n in note['front']:
                front_votes[n] += self.models['balanced']
            for n in note['back']:
                back_votes[n] += self.models['balanced']
        
        # 生成最终推荐
        final_notes = []
        for _ in range(n_notes):
            # 选择得票最多的前区号码
            top_front = [int(n) for n, v in front_votes.most_common(10)]
            front = sorted(random.sample(top_front, min(5, len(top_front))))
            
            # 选择得票最多的后区号码
            top_back = [int(n) for n, v in back_votes.most_common(6)]
            back = sorted(random.sample(top_back, min(2, len(top_back))))
            
            # 确保号码有效
            if len(front) < 5:
                front = sorted(random.sample(range(1, 36), 5))
            if len(back) < 2:
                back = sorted(random.sample(range(1, 13), 2))
            
            final_notes.append({
                'front': front,
                'back': back,
                'confidence': sum(front_votes.get(str(n), front_votes.get(n, 0)) for n in front) / 5
            })
        
        # 按置信度排序
        final_notes.sort(key=lambda x: x['confidence'], reverse=True)
        
        return final_notes


def main():
    print("=" * 70)
    print("🤖 多模型集成投票预测")
    print("=" * 70)
    
    storage = LotteryStorage()
    history = storage.get_history('dlt', 50)
    
    if not history:
        print("❌ 无历史数据")
        return
    
    print(f"✅ 加载历史数据：{len(history)} 期")
    
    predictor = EnsemblePredictor(storage)
    notes = predictor.ensemble_vote(history, n_notes=5)
    
    print(f"\n📊 模型权重配置：")
    for model, weight in predictor.models.items():
        print(f"   {model}: {weight*100:.0f}%")
    
    print(f"\n🎯 推荐号码（按置信度排序）：")
    for i, note in enumerate(notes, 1):
        front_str = ' '.join(f"{n:02d}" for n in note['front'])
        back_str = ' '.join(f"{n:02d}" for n in note['back'])
        conf = note.get('confidence', 0) * 100
        print(f"   第{i}注：{front_str} + {back_str}  (置信度：{conf:.1f}%)")
    
    # 保存推荐
    report = {
        'timestamp': datetime.now().isoformat(),
        'model': 'ensemble_voting',
        'weights': predictor.models,
        'history_periods': len(history),
        'notes': notes
    }
    
    report_file = Path('/root/.openclaw/workspace/lottery/reports/ensemble_prediction.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已保存：reports/ensemble_prediction.json")


if __name__ == "__main__":
    main()
