#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时奖池分析器 v2 - 优化版
分析奖池金额、销售额、中奖注数等数据，增加趋势预测和智能建议
"""

import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


class PrizePoolAnalyzerV2:
    """实时奖池分析器 v2 - 优化版"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def analyze_current_pool(self, lottery_type='dlt'):
        """分析当前奖池状态 - 增强版"""
        history = self.storage.get_history(lottery_type, 50)
        
        if not history:
            return None
        
        latest = history[0]
        
        # 奖池趋势分析（20 期）
        pool_trend = [draw.get('pool_amount', 0) for draw in history[:20] if draw.get('pool_amount', 0) > 0]
        
        if len(pool_trend) >= 2:
            avg_pool = sum(pool_trend) / len(pool_trend)
            # 计算移动平均
            ma_5 = sum(pool_trend[:5]) / min(5, len(pool_trend)) if pool_trend else 0
            ma_10 = sum(pool_trend[:10]) / min(10, len(pool_trend)) if pool_trend else 0
            
            # 判断趋势
            if pool_trend[0] > ma_5 * 1.1:
                trend = 'rising_fast'
            elif pool_trend[0] > ma_5:
                trend = 'rising'
            elif pool_trend[0] < ma_5 * 0.9:
                trend = 'falling_fast'
            elif pool_trend[0] < ma_5:
                trend = 'falling'
            else:
                trend = 'stable'
        else:
            avg_pool = pool_trend[0] if pool_trend else 0
            ma_5 = avg_pool
            ma_10 = avg_pool
            trend = 'stable'
        
        # 中奖难度分析
        first_prize_count = sum(1 for draw in history if draw.get('prize_info', {}).get('first_prize', 0) == 0)
        difficulty_rate = first_prize_count / len(history) * 100 if history else 0
        
        # 奖池累积速度
        if len(pool_trend) >= 5:
            accumulation_rate = (pool_trend[0] - pool_trend[4]) / max(pool_trend[4], 1) * 100
        else:
            accumulation_rate = 0
        
        return {
            'latest_issue': latest.get('issue'),
            'latest_date': latest.get('draw_date'),
            'current_pool': latest.get('pool_amount', 0),
            'avg_pool_20d': avg_pool,
            'ma_5': ma_5,
            'ma_10': ma_10,
            'pool_trend': trend,
            'accumulation_rate': accumulation_rate,
            'difficulty_rate': difficulty_rate,
            'recommendation': self._get_recommendation_v2(latest.get('pool_amount', 0), trend, difficulty_rate, accumulation_rate)
        }
    
    def _get_recommendation_v2(self, pool_amount, trend, difficulty_rate, accumulation_rate):
        """智能投注建议 v2"""
        recommendations = []
        score = 0  # 推荐指数 0-100
        
        # 奖池金额评分（0-40 分）
        if pool_amount > 15_000_000:
            recommendations.append('💰 奖池非常丰厚（>1500 万），强烈推荐')
            score += 40
        elif pool_amount > 10_000_000:
            recommendations.append('💰 奖池丰厚（>1000 万），值得投注')
            score += 30
        elif pool_amount > 5_000_000:
            recommendations.append('📈 奖池中等（500-1000 万），可适当投注')
            score += 20
        else:
            recommendations.append('📉 奖池较低（<500 万），建议小额投注')
            score += 10
        
        # 趋势评分（0-30 分）
        if trend == 'rising_fast':
            recommendations.append('📊 奖池快速上升，建议继续累积后投注')
            score += 10
        elif trend == 'rising':
            recommendations.append('📊 奖池上升趋势，可观望')
            score += 15
        elif trend == 'falling_fast':
            recommendations.append('💸 奖池快速下降，中奖概率高！')
            score += 30
        elif trend == 'falling':
            recommendations.append('💸 奖池下降趋势，中奖概率可能提高')
            score += 25
        else:
            recommendations.append('⏸️ 奖池稳定，正常投注')
            score += 20
        
        # 难度评分（0-30 分）
        if difficulty_rate > 80:
            recommendations.append('⚠️ 近期中奖难度极大，建议降低期望')
            score += 5
        elif difficulty_rate > 60:
            recommendations.append('⚠️ 中奖难度较高，谨慎投注')
            score += 15
        elif difficulty_rate < 40:
            recommendations.append('✅ 近期中奖频率较高，可适当增加投注')
            score += 30
        else:
            recommendations.append('📊 中奖难度正常')
            score += 20
        
        # 综合推荐指数
        if score >= 80:
            recommendations.append(f'\n🎯 综合推荐指数：{score}/100 - 强烈推荐')
        elif score >= 60:
            recommendations.append(f'\n📊 综合推荐指数：{score}/100 - 推荐')
        elif score >= 40:
            recommendations.append(f'\n⏸️ 综合推荐指数：{score}/100 - 观望')
        else:
            recommendations.append(f'\n⚠️ 综合推荐指数：{score}/100 - 谨慎')
        
        return {
            'recommendations': recommendations,
            'score': score
        }
    
    def analyze_sales(self, lottery_type='dlt'):
        """分析销售额趋势 - 增强版"""
        history = self.storage.get_history(lottery_type, 50)
        
        if not history:
            return None
        
        sales_data = [draw.get('sales_amount', 0) for draw in history[:20] if draw.get('sales_amount', 0) > 0]
        
        if not sales_data:
            return None
        
        # 计算统计
        avg_sales = sum(sales_data) / len(sales_data)
        max_sales = max(sales_data)
        min_sales = min(sales_data)
        latest_sales = sales_data[0]
        
        # 判断热度
        if latest_sales > avg_sales * 1.3:
            heat = 'very_hot'
        elif latest_sales > avg_sales * 1.1:
            heat = 'hot'
        elif latest_sales < avg_sales * 0.7:
            heat = 'very_cold'
        elif latest_sales < avg_sales * 0.9:
            heat = 'cold'
        else:
            heat = 'normal'
        
        # 销售趋势
        if len(sales_data) >= 5:
            recent_avg = sum(sales_data[:5]) / 5
            prev_avg = sum(sales_data[5:10]) / min(5, len(sales_data)-5)
            trend = 'rising' if recent_avg > prev_avg else 'falling'
        else:
            trend = 'stable'
        
        return {
            'latest_sales': latest_sales,
            'avg_sales': avg_sales,
            'max_sales': max_sales,
            'min_sales': min_sales,
            'heat': heat,
            'trend': trend
        }
    
    def predict_next_pool(self, lottery_type='dlt'):
        """预测下期奖池"""
        history = self.storage.get_history(lottery_type, 30)
        
        if not history:
            return None
        
        pool_data = [draw.get('pool_amount', 0) for draw in history[:20] if draw.get('pool_amount', 0) > 0]
        
        if len(pool_data) < 3:
            return None
        
        # 简单线性预测
        recent_change = [(pool_data[i] - pool_data[i+1]) for i in range(min(5, len(pool_data)-1))]
        avg_change = sum(recent_change) / len(recent_change) if recent_change else 0
        
        predicted_pool = pool_data[0] + avg_change
        
        return {
            'current_pool': pool_data[0],
            'predicted_pool': max(0, predicted_pool),
            'change_trend': 'increasing' if avg_change > 0 else 'decreasing'
        }
    
    def generate_analysis_report(self, lottery_type='dlt'):
        """生成完整分析报告 v2"""
        pool_analysis = self.analyze_current_pool(lottery_type)
        sales_analysis = self.analyze_sales(lottery_type)
        pool_prediction = self.predict_next_pool(lottery_type)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'lottery_type': lottery_type,
            'pool_analysis': pool_analysis,
            'sales_analysis': sales_analysis,
            'pool_prediction': pool_prediction,
            'overall_recommendation': self._combine_recommendations_v2(pool_analysis, sales_analysis, pool_prediction)
        }
        
        return report
    
    def _combine_recommendations_v2(self, pool_analysis, sales_analysis, pool_prediction):
        """综合建议 v2"""
        all_recs = []
        score = 0
        
        if pool_analysis:
            all_recs.extend(pool_analysis.get('recommendation', {}).get('recommendations', []))
            score = pool_analysis.get('recommendation', {}).get('score', 50)
        
        if sales_analysis:
            heat_text = {
                'very_hot': '🔥 销售非常火热，关注度高',
                'hot': '🔥 销售火热，关注度高',
                'normal': '📊 销售正常',
                'cold': '❄️ 销售冷清，可逆向思考',
                'very_cold': '❄️ 销售非常冷清'
            }
            all_recs.append(heat_text.get(sales_analysis['heat'], ''))
        
        if pool_prediction:
            change = pool_prediction['predicted_pool'] - pool_prediction['current_pool']
            pct = change / max(pool_prediction['current_pool'], 1) * 100
            all_recs.append(f"📈 预测下期奖池：¥{pool_prediction['predicted_pool']:,.0f} ({'+' if change > 0 else ''}{pct:.1f}%)")
        
        return {
            'recommendations': all_recs,
            'score': score
        }


def main():
    print("=" * 70)
    print("💰 实时奖池分析 v2 - 优化版")
    print("=" * 70)
    
    storage = LotteryStorage()
    analyzer = PrizePoolAnalyzerV2(storage)
    
    # 大乐透分析
    print("\n【大乐透】")
    dlt_report = analyzer.generate_analysis_report('dlt')
    
    if dlt_report['pool_analysis']:
        pool = dlt_report['pool_analysis']
        print(f"  最新期号：{pool['latest_issue']}")
        print(f"  开奖日期：{pool['latest_date']}")
        print(f"  当前奖池：¥{pool['current_pool']:,.0f}")
        print(f"  20 期平均：¥{pool['avg_pool_20d']:,.0f}")
        print(f"  5 期移动平均：¥{pool['ma_5']:,.0f}")
        print(f"  10 期移动平均：¥{pool['ma_10']:,.0f}")
        print(f"  奖池趋势：{pool['pool_trend']}")
        print(f"  累积速度：{pool['accumulation_rate']:+.1f}%")
        print(f"  中奖难度：{pool['difficulty_rate']:.1f}% 未中一等奖")
    
    if dlt_report['sales_analysis']:
        sales = dlt_report['sales_analysis']
        print(f"\n  销售分析：")
        print(f"    最新销售：¥{sales['latest_sales']:,.0f}")
        print(f"    平均销售：¥{sales['avg_sales']:,.0f}")
        print(f"    最高销售：¥{sales['max_sales']:,.0f}")
        print(f"    最低销售：¥{sales['min_sales']:,.0f}")
        print(f"    销售热度：{sales['heat']}")
        print(f"    销售趋势：{sales['trend']}")
    
    if dlt_report['pool_prediction']:
        pred = dlt_report['pool_prediction']
        print(f"\n  奖池预测：")
        print(f"    当前奖池：¥{pred['current_pool']:,.0f}")
        print(f"    预测下期：¥{pred['predicted_pool']:,.0f}")
        print(f"    变化趋势：{pred['change_trend']}")
    
    print(f"\n  综合建议：")
    for rec in dlt_report['overall_recommendation']['recommendations']:
        print(f"    {rec}")
    
    # 保存报告
    report_file = Path('/root/.openclaw/workspace/lottery/reports/prize_pool_analysis_v2.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(dlt_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已保存：reports/prize_pool_analysis_v2.json")


if __name__ == "__main__":
    main()
