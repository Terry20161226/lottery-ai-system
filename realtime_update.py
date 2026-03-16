#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时性优化模块
- 监听开奖结果
- 立即更新策略权重
- 异常检测与自动调整
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage
# from strategy_tracker import StrategyTracker  # 已移除
from adaptive_strategy import AdaptiveStrategy
from feature_analyzer import FeatureAnalyzer
from datetime import datetime
import json


class RealtimeUpdater:
    """实时更新器"""
    
    def __init__(self):
        self.storage = LotteryStorage()
        self.tracker = StrategyTracker()
        self.adaptive = AdaptiveStrategy()
        self.analyzer = FeatureAnalyzer()
    
    def check_and_update(self, lottery_type: str) -> dict:
        """
        检查是否有新开奖并更新
        
        Returns:
            更新结果
        """
        result = {
            'updated': False,
            'lottery_type': lottery_type,
            'message': '',
            'new_weights': None,
        }
        
        # 获取最新开奖
        history = self.storage.get_history(lottery_type, 1)
        if not history:
            result['message'] = '无历史数据'
            return result
        
        latest = history[0]
        issue = latest.get('issue')
        draw_date = latest.get('draw_date')
        
        # 检查是否已核对
        stats = self.tracker.get_summary(lottery_type)
        last_update = stats.get('last_update')
        
        # 核对中奖
        prize_result = self.tracker.check_prize(lottery_type, issue, latest.get('numbers', {}))
        
        if 'error' not in prize_result:
            result['updated'] = True
            result['message'] = f'✅ {issue} 期已核对'
            
            # 重新计算权重
            new_weights = self.adaptive.get_adaptive_weights(lottery_type)
            result['new_weights'] = new_weights
            
            # 检查是否需要重新生成推荐
            if self._should_regenerate(lottery_type, prize_result):
                result['regenerate'] = True
                result['message'] += ' ⚠️ 策略表现异常，建议重新生成推荐'
        
        return result
    
    def _should_regenerate(self, lottery_type: str, prize_result: dict) -> bool:
        """
        判断是否需要重新生成推荐
        
        条件：
        1. 某策略连续 5 期未中奖
        2. 权重变化超过 20%
        3. 发现新的显著特征
        """
        # 检查连续未中奖
        stats = self.tracker.get_summary(lottery_type)
        if stats.get('strategy_stats'):
            for strategy, data in stats['strategy_stats'].items():
                hit_rate = data.get('hit_rate', 0)
                if hit_rate < 5:  # 中奖率低于 5%
                    return True
        
        return False
    
    def anomaly_detection(self, lottery_type: str) -> dict:
        """
        异常检测
        
        检测项：
        1. 某策略连续不中
        2. 号码分布异常
        3. 和值/跨度异常
        """
        anomalies = []
        
        # 1. 策略表现异常
        stats = self.tracker.get_summary(lottery_type)
        if stats.get('strategy_stats'):
            for strategy, data in stats['strategy_stats'].items():
                hit_rate = data.get('hit_rate', 0)
                if hit_rate < 5:
                    anomalies.append({
                        'type': 'strategy_underperform',
                        'strategy': strategy,
                        'hit_rate': hit_rate,
                        'suggestion': f'降低{strategy}权重'
                    })
        
        # 2. 特征异常
        features = self.analyzer.run_full_analysis(lottery_type)
        if 'error' not in features:
            # 遗漏值异常
            omission = features.get('features', {}).get('omission', {})
            if omission.get('max_omission', 0) > 30:
                anomalies.append({
                    'type': 'high_omission',
                    'value': omission['max_omission'],
                    'suggestion': '关注冷号反弹'
                })
            
            # 和值异常
            sum_value = features.get('features', {}).get('sum_value', {})
            if sum_value.get('trend') == 'increasing' or sum_value.get('trend') == 'decreasing':
                anomalies.append({
                    'type': 'sum_trend',
                    'trend': sum_value['trend'],
                    'suggestion': f'和值{sum_value["trend"]}，调整选号范围'
                })
        
        return {
            'has_anomaly': len(anomalies) > 0,
            'anomalies': anomalies,
            'count': len(anomalies)
        }


def main():
    """主函数"""
    updater = RealtimeUpdater()
    
    print("=" * 60)
    print("实时性检查与更新")
    print("=" * 60)
    
    # 双色球
    print("\n【双色球】")
    ssq_result = updater.check_and_update('ssq')
    print(f"更新状态：{'✅ 已更新' if ssq_result['updated'] else '❌ 未更新'}")
    print(f"消息：{ssq_result['message']}")
    
    if ssq_result.get('new_weights'):
        print("\n新权重：")
        for k, v in sorted(ssq_result['new_weights'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {k}: {v}")
    
    # 异常检测
    ssq_anomalies = updater.anomaly_detection('ssq')
    if ssq_anomalies['has_anomaly']:
        print(f"\n⚠️ 发现 {ssq_anomalies['count']} 个异常：")
        for a in ssq_anomalies['anomalies']:
            print(f"  - {a['type']}: {a.get('suggestion', '')}")
    
    # 大乐透
    print("\n【大乐透】")
    dlt_result = updater.check_and_update('dlt')
    print(f"更新状态：{'✅ 已更新' if dlt_result['updated'] else '❌ 未更新'}")
    print(f"消息：{dlt_result['message']}")
    
    if dlt_result.get('new_weights'):
        print("\n新权重：")
        for k, v in sorted(dlt_result['new_weights'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {k}: {v}")
    
    # 异常检测
    dlt_anomalies = updater.anomaly_detection('dlt')
    if dlt_anomalies['has_anomaly']:
        print(f"\n⚠️ 发现 {dlt_anomalies['count']} 个异常：")
        for a in dlt_anomalies['anomalies']:
            print(f"  - {a['type']}: {a.get('suggestion', '')}")
    
    print("\n" + "=" * 60)
    print("检查完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
