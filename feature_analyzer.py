#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
特征分析模块 - 分析历史数据中的有效特征
"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter


class FeatureAnalyzer:
    """特征分析器"""
    
    def __init__(self, base_dir: str = "/root/.openclaw/workspace/lottery"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.analysis_dir = self.base_dir / "analysis"
        
        # 创建目录
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        
        # 分析结果文件
        self.ssq_features_file = self.analysis_dir / "ssq_features.json"
        self.dlt_features_file = self.analysis_dir / "dlt_features.json"
    
    def load_history(self, lottery_type: str, limit: int = 100) -> List[Dict]:
        """加载历史开奖数据"""
        file_path = self.data_dir / f"{lottery_type}_history.json"
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('records', [])[:limit]
        return []
    
    def analyze_cold_hot_effectiveness(self, lottery_type: str, history: List[Dict]) -> Dict:
        """分析冷热号有效性"""
        if len(history) < 30:
            return {"hot_hit_rate": 0, "cold_hit_rate": 0, "recommendation": "数据不足"}
        
        # 计算前 30 期的冷热号
        base_history = history[:30]
        all_numbers = []
        
        if lottery_type == 'ssq':
            for record in base_history:
                numbers = record.get('numbers', {})
                all_numbers.extend(numbers.get('red', []))
        else:
            for record in base_history:
                numbers = record.get('numbers', {})
                all_numbers.extend(numbers.get('front', []))
        
        # 统计频率
        freq = Counter(all_numbers)
        sorted_nums = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        
        hot_numbers = set([n[0] for n in sorted_nums[:10]])  # 热号前 10
        cold_numbers = set([n[0] for n in sorted_nums[-10:]])  # 冷号后 10
        
        # 检查后续期数中热号冷号的出现情况
        test_history = history[30:60] if len(history) >= 60 else history[30:]
        hot_hits = 0
        cold_hits = 0
        total_numbers = 0
        
        for record in test_history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            for num in numbers:
                if num in hot_numbers:
                    hot_hits += 1
                elif num in cold_numbers:
                    cold_hits += 1
                total_numbers += 1
        
        hot_hit_rate = (hot_hits / total_numbers * 100) if total_numbers > 0 else 0
        cold_hit_rate = (cold_hits / total_numbers * 100) if total_numbers > 0 else 0
        
        return {
            "hot_hit_rate": round(hot_hit_rate, 2),
            "cold_hit_rate": round(cold_hit_rate, 2),
            "hot_weight": round(hot_hit_rate / (hot_hit_rate + cold_hit_rate), 2) if (hot_hit_rate + cold_hit_rate) > 0 else 0.5,
            "recommendation": "热号更有效" if hot_hit_rate > cold_hit_rate else "冷号更有效"
        }
    
    def analyze_odd_even(self, lottery_type: str, history: List[Dict]) -> Dict:
        """分析奇偶比例有效性"""
        odd_even_dist = Counter()
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            odd_count = sum(1 for n in numbers if n % 2 == 1)
            even_count = len(numbers) - odd_count
            ratio = f"{odd_count}:{even_count}"
            odd_even_dist[ratio] += 1
        
        total = sum(odd_even_dist.values())
        distribution = {k: round(v/total*100, 2) for k, v in odd_even_dist.most_common()}
        
        best_ratio = odd_even_dist.most_common(1)[0][0] if odd_even_dist else "3:3"
        
        return {
            "distribution": distribution,
            "best_ratio": best_ratio,
            "recommendation": f"推荐奇偶比 {best_ratio}"
        }
    
    def analyze_zone_distribution(self, lottery_type: str, history: List[Dict]) -> Dict:
        """分析区间分布有效性"""
        zone_hits = Counter()
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
                zones = [0, 0, 0]  # 01-11, 12-22, 23-33
                for n in numbers:
                    if n <= 11:
                        zones[0] += 1
                    elif n <= 22:
                        zones[1] += 1
                    else:
                        zones[2] += 1
            else:
                numbers = record.get('numbers', {}).get('front', [])
                zones = [0, 0, 0]  # 01-12, 13-23, 24-35
                for n in numbers:
                    if n <= 12:
                        zones[0] += 1
                    elif n <= 23:
                        zones[1] += 1
                    else:
                        zones[2] += 1
            
            zone_hits[f"{zones[0]}-{zones[1]}-{zones[2]}"] += 1
        
        total = sum(zone_hits.values())
        distribution = {k: round(v/total*100, 2) for k, v in zone_hits.most_common()}
        best_zone = zone_hits.most_common(1)[0][0] if zone_hits else "2-2-2"
        
        return {
            "distribution": distribution,
            "best_zone": best_zone,
            "recommendation": f"推荐区间比 {best_zone}"
        }
    
    def analyze_consecutive(self, lottery_type: str, history: List[Dict]) -> Dict:
        """分析连号有效性"""
        consecutive_count = 0
        total_periods = len(history)
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = sorted(record.get('numbers', {}).get('red', []))
            else:
                numbers = sorted(record.get('numbers', {}).get('front', []))
            
            has_consecutive = False
            for i in range(len(numbers) - 1):
                if numbers[i+1] - numbers[i] == 1:
                    has_consecutive = True
                    break
            
            if has_consecutive:
                consecutive_count += 1
        
        consecutive_rate = (consecutive_count / total_periods * 100) if total_periods > 0 else 0
        
        return {
            "consecutive_rate": round(consecutive_rate, 2),
            "recommendation": "关注连号" if consecutive_rate > 50 else "连号可选可不选"
        }
    
    def analyze_omission(self, lottery_type: str, history: List[Dict]) -> Dict:
        """
        分析遗漏值（连续未出现的期数）⭐ NEW
        """
        if not history:
            return {"max_omission": 0, "avg_omission": 0, "hot_numbers": [], "cold_numbers": []}
        
        # 获取所有号码范围
        if lottery_type == 'ssq':
            all_numbers = list(range(1, 34))  # 红球 1-33
        else:
            all_numbers = list(range(1, 36))  # 前区 1-35
        
        # 统计每个号码的遗漏值
        omission = {n: 0 for n in all_numbers}
        
        # 从最新到最旧遍历
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            # 出现的号码遗漏值归 0
            for n in numbers:
                if n in omission:
                    omission[n] = 0
            
            # 未出现的号码遗漏值 +1
            for n in all_numbers:
                if n not in numbers:
                    omission[n] += 1
        
        # 找出最大遗漏和平均遗漏
        max_omission = max(omission.values())
        avg_omission = sum(omission.values()) / len(omission) if omission else 0
        
        # 热号（遗漏值<5）和冷号（遗漏值>20）
        hot_numbers = [n for n, v in omission.items() if v < 5]
        cold_numbers = [n for n, v in omission.items() if v > 20]
        
        return {
            "max_omission": max_omission,
            "avg_omission": round(avg_omission, 1),
            "hot_numbers": hot_numbers[:10],  # 前 10 个热号
            "cold_numbers": cold_numbers[:10],  # 前 10 个冷号
            "recommendation": f"最大遗漏{max_omission}期，关注冷号反弹" if max_omission > 20 else "遗漏值正常"
        }
    
    def analyze_sum_value(self, lottery_type: str, history: List[Dict]) -> Dict:
        """
        分析和值走势 ⭐ NEW
        """
        if not history:
            return {"avg_sum": 0, "trend": "stable", "recommended_sum": 0}
        
        sum_values = []
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            sum_values.append(sum(numbers))
        
        avg_sum = sum(sum_values) / len(sum_values)
        
        # 计算趋势（最近 10 期 vs 历史平均）
        recent_10 = sum_values[:10] if len(sum_values) >= 10 else sum_values
        recent_avg = sum(recent_10) / len(recent_10)
        
        if abs(recent_avg - avg_sum) < 5:
            trend = "stable"
            recommended_sum = round(avg_sum)
        elif recent_avg > avg_sum:
            trend = "increasing"
            recommended_sum = round(recent_avg)
        else:
            trend = "decreasing"
            recommended_sum = round(recent_avg)
        
        return {
            "avg_sum": round(avg_sum, 1),
            "recent_avg": round(recent_avg, 1),
            "trend": trend,
            "recommended_sum": recommended_sum,
            "recommendation": f"推荐和值范围 {recommended_sum-10}~{recommended_sum+10}"
        }
    
    def analyze_span(self, lottery_type: str, history: List[Dict]) -> Dict:
        """
        分析跨度（最大号 - 最小号）⭐ NEW
        """
        if not history:
            return {"avg_span": 0, "max_span": 0, "recommended_span": 0}
        
        spans = []
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = sorted(record.get('numbers', {}).get('red', []))
            else:
                numbers = sorted(record.get('numbers', {}).get('front', []))
            
            if numbers:
                span = max(numbers) - min(numbers)
                spans.append(span)
        
        avg_span = sum(spans) / len(spans) if spans else 0
        max_span = max(spans) if spans else 0
        
        return {
            "avg_span": round(avg_span, 1),
            "max_span": max_span,
            "recommended_span": round(avg_span),
            "recommendation": f"推荐跨度范围 {round(avg_span)-5}~{round(avg_span)+5}"
        }
    
    def analyze_same_tail(self, lottery_type: str, history: List[Dict]) -> Dict:
        """
        分析同尾号（如 03/13/23）⭐ NEW
        """
        if not history:
            return {"same_tail_rate": 0, "hot_tails": []}
        
        tail_count = Counter()
        periods_with_same_tail = 0
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            # 统计尾号
            tails = [n % 10 for n in numbers]
            tail_freq = Counter(tails)
            
            # 是否有同尾号
            if max(tail_freq.values()) > 1:
                periods_with_same_tail += 1
            
            # 统计每个尾号出现次数
            for tail in tails:
                tail_count[tail] += 1
        
        same_tail_rate = (periods_with_same_tail / len(history) * 100) if history else 0
        hot_tails = [tail for tail, count in tail_count.most_common(3)]
        
        return {
            "same_tail_rate": round(same_tail_rate, 2),
            "hot_tails": hot_tails,
            "recommendation": f"同尾号出现率{same_tail_rate:.1f}%，关注尾号{hot_tails}"
        }
    
    def analyze_sum_range(self, lottery_type: str, history: List[Dict]) -> Dict:
        """分析和值范围"""
        sums = []
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            sums.append(sum(numbers))
        
        if not sums:
            return {"avg_sum": 0, "recommended_range": "0-0"}
        
        avg_sum = sum(sums) / len(sums)
        min_sum = min(sums)
        max_sum = max(sums)
        
        # 推荐范围（平均值 ±10%）
        low_bound = int(avg_sum * 0.9)
        high_bound = int(avg_sum * 1.1)
        
        return {
            "avg_sum": round(avg_sum, 1),
            "min_sum": min_sum,
            "max_sum": max_sum,
            "recommended_range": f"{low_bound}-{high_bound}"
        }
    
    def analyze_tail_numbers(self, lottery_type: str, history: List[Dict]) -> Dict:
        """分析尾数分布"""
        tail_counts = Counter()
        
        for record in history:
            if lottery_type == 'ssq':
                numbers = record.get('numbers', {}).get('red', [])
            else:
                numbers = record.get('numbers', {}).get('front', [])
            
            for n in numbers:
                tail = n % 10
                tail_counts[tail] += 1
        
        total = sum(tail_counts.values())
        distribution = {str(k): round(v/total*100, 2) for k, v in tail_counts.most_common()}
        hot_tails = [str(k) for k, v in tail_counts.most_common(3)]
        
        return {
            "distribution": distribution,
            "hot_tails": hot_tails,
            "recommendation": f"关注尾数 {', '.join(hot_tails)}"
        }
    
    def run_full_analysis(self, lottery_type: str) -> Dict:
        """运行完整特征分析 - 增强版"""
        history = self.load_history(lottery_type, 100)
        
        if not history:
            return {"error": "无历史数据"}
        
        analysis = {
            "lottery_type": lottery_type,
            "analysis_date": str(__import__('datetime').datetime.now()),
            "periods_analyzed": len(history),
            "features": {
                "cold_hot": self.analyze_cold_hot_effectiveness(lottery_type, history),
                "odd_even": self.analyze_odd_even(lottery_type, history),
                "zone_distribution": self.analyze_zone_distribution(lottery_type, history),
                "consecutive": self.analyze_consecutive(lottery_type, history),
                # 新增特征 ⭐
                "omission": self.analyze_omission(lottery_type, history),
                "sum_value": self.analyze_sum_value(lottery_type, history),
                "span": self.analyze_span(lottery_type, history),
                "same_tail": self.analyze_same_tail(lottery_type, history),
                # 原有特征
                "sum_range": self.analyze_sum_range(lottery_type, history),
                "tail_numbers": self.analyze_tail_numbers(lottery_type, history),
            }
        }
        
        # 保存分析结果
        file_path = self.ssq_features_file if lottery_type == 'ssq' else self.dlt_features_file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        return analysis
    
    def get_strategy_weights(self, lottery_type: str) -> Dict[str, float]:
        """根据特征分析结果计算策略权重"""
        analysis = self.run_full_analysis(lottery_type)
        
        if "error" in analysis:
            # 默认权重
            return {
                'balanced': 0.3,
                'hot_tracking': 0.15,
                'cold_rebound': 0.1,
                'odd_even': 0.15,
                'zone_distribution': 0.15,
                'consecutive': 0.1,
                'warm_balance': 0.05,
            }
        
        features = analysis.get('features', {})
        weights = {}
        
        # 冷热号分析 → 热号追踪/冷号反弹权重
        cold_hot = features.get('cold_hot', {})
        hot_weight = cold_hot.get('hot_weight', 0.5)
        weights['hot_tracking'] = round(hot_weight * 0.20, 2)
        weights['cold_rebound'] = round((1 - hot_weight) * 0.10, 2)  # 降低冷号权重（回测表现差）
        
        # 奇偶分析 → 奇偶均衡权重
        odd_even = features.get('odd_even', {})
        weights['odd_even'] = 0.12 if odd_even.get('best_ratio') in ['3:3', '4:2', '2:3'] else 0.08
        
        # 区间分析 → 区间分布权重（回测表现好）
        zone = features.get('zone_distribution', {})
        weights['zone_distribution'] = 0.18 if zone.get('best_zone') else 0.12
        
        # 连号分析 → 连号追踪权重（回测表现好）
        consecutive = features.get('consecutive', {})
        weights['consecutive'] = 0.15 if consecutive.get('consecutive_rate', 0) > 50 else 0.10
        
        # 新增：遗漏值分析 → 冷号反弹修正
        omission = features.get('omission', {})
        if omission.get('max_omission', 0) > 20:  # 有大遗漏号
            weights['cold_rebound'] = min(0.15, weights.get('cold_rebound', 0) + 0.05)
        
        # 新增：和值走势 → 均衡策略修正
        sum_value = features.get('sum_value', {})
        if sum_value.get('trend') == 'stable':  # 和值稳定
            weights['balanced'] = 0.25
        else:
            weights['balanced'] = 0.20
        
        # 新增：跨度分析 → 温号搭配
        span = features.get('span', {})
        weights['warm_balance'] = 0.10 if span.get('avg_span', 25) > 20 else 0.08
        
        # 确保所有策略都有权重
        all_strategies = ['balanced', 'hot_tracking', 'cold_rebound', 'odd_even', 
                         'zone_distribution', 'consecutive', 'warm_balance']
        for s in all_strategies:
            if s not in weights:
                weights[s] = 0.10
        
        # 均衡策略作为基础
        remaining = 1.0 - sum(weights.values())
        if remaining > 0:
            weights['balanced'] = weights.get('balanced', 0.20) + remaining
        
        # 确保总和为 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: round(v/total, 2) for k, v in weights.items()}
        
        return weights
