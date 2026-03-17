#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多策略集成推荐生成器
- 集成 4 种策略（ML 加权、热号追踪、冷号反弹、均衡策略）
- 投票机制生成最终推荐
- 支持大乐透、双色球
- 每周日 22:15 执行（开奖前优化推荐）
"""

import sys
import json
import random
from datetime import datetime
from pathlib import Path
from collections import Counter

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


class EnsembleRecommender:
    """多策略集成推荐器"""
    
    def __init__(self, lottery_type: str = 'dlt'):
        self.lottery_type = lottery_type
        self.storage = LotteryStorage()
        self.history = self.storage.get_history(lottery_type, 50)
        
        # 策略权重
        self.weights = {
            'ml_weighted': 0.40,
            'hot_tracking': 0.25,
            'cold_rebound': 0.20,
            'balanced': 0.15
        }
    
    def ml_weighted_strategy(self) -> list:
        """ML 加权策略"""
        try:
            from ml_predictor import MLPredictor
            predictor = MLPredictor(self.storage, lottery_type=self.lottery_type)
            predictor.prepare_data()
            notes = predictor.predict(n_predictions=5)
            return notes
        except Exception as e:
            print(f"⚠️ ML 策略失败：{e}")
            return []
    
    def hot_tracking_strategy(self) -> list:
        """热号追踪策略 - 选择近期高频号码"""
        if len(self.history) < 10:
            return []
        
        recent = self.history[-10:]
        front_counts = Counter()
        back_counts = Counter()
        
        for draw in recent:
            nums = draw.get('numbers', {})
            if self.lottery_type == 'dlt':
                front_counts.update(nums.get('front', nums.get('red', [])))
                back_counts.update(nums.get('back', nums.get('blue', [])))
            else:  # ssq
                front_counts.update(nums.get('red', []))
                back_counts.update(nums.get('blue', []))
        
        # 选择热号
        hot_front = [n for n, c in front_counts.most_common(18)]
        hot_back = [n for n, c in back_counts.most_common(6)]
        
        notes = []
        for _ in range(5):
            if self.lottery_type == 'dlt':
                front = sorted(random.sample(hot_front, 5))
                back = sorted(random.sample(hot_back, 2))
                notes.append({'front': front, 'back': back})
            else:
                front = sorted(random.sample(hot_front, 6))
                back = [random.choice(hot_back)]
                notes.append({'red': front, 'blue': back})
        
        return notes
    
    def cold_rebound_strategy(self) -> list:
        """冷号反弹策略 - 选择遗漏久的号码"""
        if len(self.history) < 10:
            return []
        
        # 计算遗漏值
        max_num = 35 if self.lottery_type == 'dlt' else 33
        omission = {n: 0 for n in range(1, max_num + 1)}
        
        for draw in reversed(self.history[-30:]):
            nums = draw.get('numbers', {})
            if self.lottery_type == 'dlt':
                front_nums = [int(x) for x in nums.get('front', nums.get('red', []))]
            else:
                front_nums = [int(x) for x in nums.get('red', [])]
            
            for n in front_nums:
                omission[n] = 0
            for n in omission:
                if n not in front_nums:
                    omission[n] += 1
        
        # 选择遗漏最多的号码
        cold_front = sorted([int(x) for x in omission.keys()], key=lambda x: omission[x], reverse=True)[:18]
        
        # 后区冷号
        back_max = 12 if self.lottery_type == 'dlt' else 16
        back_omission = {n: 0 for n in range(1, back_max + 1)}
        for draw in reversed(self.history[-30:]):
            nums = draw.get('numbers', {})
            if self.lottery_type == 'dlt':
                back_nums = [int(x) for x in nums.get('back', nums.get('blue', []))]
            else:
                back_nums = [int(x) for x in nums.get('blue', [])]
            
            for n in back_nums:
                back_omission[n] = 0
            for n in back_omission:
                if n not in back_nums:
                    back_omission[n] += 1
        
        cold_back = sorted([int(x) for x in back_omission.keys()], key=lambda x: back_omission[x], reverse=True)[:8]
        
        notes = []
        for _ in range(5):
            if self.lottery_type == 'dlt':
                front = sorted(random.sample(cold_front, 5))
                back = sorted(random.sample(cold_back, 2))
                notes.append({'front': front, 'back': back})
            else:
                front = sorted(random.sample(cold_front, 6))
                back = [random.choice(cold_back)]
                notes.append({'red': front, 'blue': back})
        
        return notes
    
    def balanced_strategy(self) -> list:
        """均衡策略 - 冷热号混合"""
        hot_notes = self.hot_tracking_strategy()
        cold_notes = self.cold_rebound_strategy()
        
        if not hot_notes or not cold_notes:
            return []
        
        # 混合冷热号
        notes = []
        for i in range(5):
            hot = hot_notes[i % len(hot_notes)]
            cold = cold_notes[i % len(cold_notes)]
            
            if self.lottery_type == 'dlt':
                # 前区 3 热 +2 冷，后区 1 热 +1 冷
                hot_front = set(hot.get('front', []))
                cold_front = set(cold.get('front', []))
                front = sorted(list(hot_front)[:3] + list(cold_front)[:2])
                
                hot_back = set(hot.get('back', []))
                cold_back = set(cold.get('back', []))
                back = sorted(list(hot_back)[:1] + list(cold_back)[:1])
                
                notes.append({'front': front, 'back': back})
            else:
                hot_front = set(hot.get('red', []))
                cold_front = set(cold.get('red', []))
                front = sorted(list(hot_front)[:4] + list(cold_front)[:2])
                
                hot_back = hot.get('blue', [])
                cold_back = cold.get('blue', [])
                back = [hot_back[0] if hot_back else cold_back[0]]
                
                notes.append({'red': front, 'blue': back})
        
        return notes
    
    def voting_ensemble(self) -> list:
        """投票集成 - 统计各策略推荐，选出现频率最高的号码"""
        all_notes = {
            'ml': self.ml_weighted_strategy(),
            'hot': self.hot_tracking_strategy(),
            'cold': self.cold_rebound_strategy(),
            'balanced': self.balanced_strategy()
        }
        
        print("\n📊 各策略推荐数量:")
        for name, notes in all_notes.items():
            print(f"   {name}: {len(notes)} 注")
        
        # 统计号码频率
        if self.lottery_type == 'dlt':
            front_freq = Counter()
            back_freq = Counter()
            
            for strategy_name, notes in all_notes.items():
                weight = self.weights.get(strategy_name.replace('_strategy', '') if strategy_name != 'ml' else 'ml_weighted', 0.25)
                for note in notes:
                    for n in note.get('front', []):
                        front_freq[int(n)] += weight
                    for n in note.get('back', []):
                        back_freq[int(n)] += weight
            
            # 选择频率最高的号码
            top_front = [n for n, _ in front_freq.most_common(18)]
            top_back = [n for n, _ in back_freq.most_common(8)]
            
            # 生成最终推荐
            recommendations = []
            for _ in range(5):
                front = sorted(random.sample(top_front, 5))
                back = sorted(random.sample(top_back, 2))
                recommendations.append({'front': front, 'back': back})
        
        else:  # ssq
            red_freq = Counter()
            blue_freq = Counter()
            
            for strategy_name, notes in all_notes.items():
                weight = self.weights.get(strategy_name.replace('_strategy', '') if strategy_name != 'ml' else 'ml_weighted', 0.25)
                for note in notes:
                    for n in note.get('red', []):
                        red_freq[int(n)] += weight
                    for n in note.get('blue', []):
                        blue_freq[int(n)] += weight
            
            top_red = [n for n, _ in red_freq.most_common(20)]
            top_blue = [n for n, _ in blue_freq.most_common(8)]
            
            recommendations = []
            for _ in range(5):
                red = sorted(random.sample(top_red, 6))
                blue = [random.choice(top_blue)]
                recommendations.append({'red': red, 'blue': blue})
        
        return recommendations
    
    def save_recommendations(self, recommendations: list):
        """保存推荐到文件"""
        issue = self._get_current_issue()
        
        data = {
            'recommendations': [{
                'id': f'ensemble_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'issue': issue,
                'created_at': datetime.now().isoformat(),
                'strategy': 'ensemble_voting',
                'method': 'weighted_frequency_voting',
                'weights': self.weights,
                'numbers': recommendations
            }]
        }
        
        # 保存
        if self.lottery_type == 'dlt':
            filepath = Path('/root/.openclaw/workspace/lottery/data/dlt_recommend.json')
        else:
            filepath = Path('/root/.openclaw/workspace/lottery/data/ssq_recommend.json')
        
        # 合并现有推荐（保留其他策略的推荐）
        existing = {}
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                existing = json.load(f)
        
        # 更新 recommendations 列表
        if 'recommendations' not in existing:
            existing['recommendations'] = []
        
        # 移除同策略的旧推荐
        existing['recommendations'] = [
            r for r in existing['recommendations']
            if r.get('strategy') != 'ensemble_voting'
        ]
        
        # 添加新推荐
        existing['recommendations'].extend(data['recommendations'])
        
        # 保存
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 推荐已保存：{filepath}")
    
    def _get_current_issue(self) -> str:
        """获取当前期号"""
        if not self.history:
            return datetime.now().strftime('%Y%m%d')
        
        latest_issue = self.history[0].get('issue', '')
        # 期号 +1（简化处理）
        try:
            issue_num = int(latest_issue)
            return str(issue_num + 1)
        except:
            return datetime.now().strftime('%Y%m%d')
    
    def generate(self):
        """生成集成推荐"""
        print("=" * 60)
        print(f"🤖 多策略集成推荐 - {self.lottery_type.upper()}")
        print(f"【时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        print(f"\n📖 加载历史数据：{len(self.history)} 期")
        
        print("\n📊 策略权重配置:")
        for name, weight in self.weights.items():
            print(f"   {name}: {int(weight * 100)}%")
        
        # 生成推荐
        print("\n🎯 生成集成推荐...")
        recommendations = self.voting_ensemble()
        
        # 显示推荐
        print(f"\n✅ 生成 {len(recommendations)} 注推荐:")
        for i, rec in enumerate(recommendations, 1):
            if self.lottery_type == 'dlt':
                front = ' '.join(f'{n:02d}' for n in rec.get('front', []))
                back = ' '.join(f'{n:02d}' for n in rec.get('back', []))
                print(f"   第{i}注：前区 {front} + 后区 {back}")
            else:
                red = ' '.join(f'{n:02d}' for n in rec.get('red', []))
                blue = ' '.join(f'{n:02d}' for n in rec.get('blue', []))
                print(f"   第{i}注：红球 {red} + 蓝球 {blue}")
        
        # 保存
        self.save_recommendations(recommendations)
        
        print("\n" + "=" * 60)
        print("✅ 集成推荐完成！")
        print("=" * 60)


def main():
    """主函数 - 生成大乐透和双色球集成推荐"""
    print("\n" + "=" * 60)
    print("🎯 多策略集成推荐系统")
    print("=" * 60)
    
    # 大乐透（周一/三/六）
    print("\n【大乐透集成推荐】")
    dlt_recommender = EnsembleRecommender('dlt')
    dlt_recommender.generate()
    
    # 双色球（周二/四/日）
    print("\n【双色球集成推荐】")
    ssq_recommender = EnsembleRecommender('ssq')
    ssq_recommender.generate()
    
    print("\n" + "=" * 60)
    print("✅ 全部完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
