#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时奖池分析器
分析奖池金额、销售额、中奖注数等数据
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


class PrizePoolAnalyzer:
    """实时奖池分析器"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def analyze_current_pool(self, lottery_type='dlt'):
        """分析当前奖池状态"""
        history = self.storage.get_history(lottery_type, 30)
        
        if not history:
            return None
        
        latest = history[0]
        
        # 奖池趋势分析
        pool_trend = []
        for draw in history[:10]:
            pool_trend.append(draw.get('pool_amount', 0))
        
        # 计算趋势
        if len(pool_trend) >= 2:
            avg_pool = sum(pool_trend) / len(pool_trend)
            trend = 'rising' if pool_trend[0] > avg_pool else 'falling'
        else:
            avg_pool = pool_trend[0] if pool_trend else 0
            trend = 'stable'
        
        # 中奖难度分析
        first_prize_count = 0
        total_periods = len(history)
        
        for draw in history:
            # 假设一等奖注数存储在 prize_info 中
            prize_info = draw.get('prize_info', {})
            if prize_info.get('first_prize', 0) == 0:
                first_prize_count += 1
        
        difficulty_rate = first_prize_count / total_periods * 100 if total_periods > 0 else 0
        
        return {
            'latest_issue': latest.get('issue'),
            'latest_date': latest.get('draw_date'),
            'current_pool': latest.get('pool_amount', 0),
            'avg_pool_10d': avg_pool,
            'pool_trend': trend,
            'difficulty_rate': difficulty_rate,
            'recommendation': self._get_recommendation(latest.get('pool_amount', 0), trend, difficulty_rate)
        }
    
    def _get_recommendation(self, pool_amount, trend, difficulty_rate):
        """根据奖池情况给出投注建议"""
        recommendations = []
        
        # 奖池金额建议
        if pool_amount > 10_000_000:
            recommendations.append('💰 奖池丰厚（>1000 万），值得投注')
        elif pool_amount > 5_000_000:
            recommendations.append('📈 奖池中等（500-1000 万），可适当投注')
        else:
            recommendations.append('📉 奖池较低（<500 万），建议小额投注')
        
        # 趋势建议
        if trend == 'rising':
            recommendations.append('📊 奖池上升趋势，可继续观望')
        elif trend == 'falling':
            recommendations.append('💸 奖池下降趋势，中奖概率可能提高')
        
        # 难度建议
        if difficulty_rate > 70:
            recommendations.append('⚠️ 近期中奖难度大，建议降低期望')
        elif difficulty_rate < 30:
            recommendations.append('✅ 近期中奖频率较高，可适当增加投注')
        
        return recommendations
    
    def analyze_sales(self, lottery_type='dlt'):
        """分析销售额趋势"""
        history = self.storage.get_history(lottery_type, 30)
        
        if not history:
            return None
        
        sales_data = []
        for draw in history[:20]:
            sales = draw.get('sales_amount', 0)
            if sales > 0:
                sales_data.append({
                    'issue': draw.get('issue'),
                    'sales': sales
                })
        
        if not sales_data:
            return None
        
        # 计算平均销售额
        avg_sales = sum(d['sales'] for d in sales_data) / len(sales_data)
        
        # 判断热度
        latest_sales = sales_data[0]['sales']
        if latest_sales > avg_sales * 1.2:
            heat = 'hot'
        elif latest_sales < avg_sales * 0.8:
            heat = 'cold'
        else:
            heat = 'normal'
        
        return {
            'latest_sales': latest_sales,
            'avg_sales': avg_sales,
            'heat': heat,
            'trend': 'rising' if latest_sales > avg_sales else 'falling'
        }
    
    def generate_analysis_report(self, lottery_type='dlt'):
        """生成完整分析报告"""
        pool_analysis = self.analyze_current_pool(lottery_type)
        sales_analysis = self.analyze_sales(lottery_type)
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'lottery_type': lottery_type,
            'pool_analysis': pool_analysis,
            'sales_analysis': sales_analysis,
            'overall_recommendation': self._combine_recommendations(pool_analysis, sales_analysis)
        }
        
        return report
    
    def _combine_recommendations(self, pool_analysis, sales_analysis):
        """综合建议"""
        all_recs = []
        
        if pool_analysis:
            all_recs.extend(pool_analysis.get('recommendation', []))
        
        if sales_analysis:
            if sales_analysis['heat'] == 'hot':
                all_recs.append('🔥 销售火热，关注度高')
            elif sales_analysis['heat'] == 'cold':
                all_recs.append('❄️ 销售冷清，可逆向思考')
        
        return all_recs


def main():
    print("=" * 70)
    print("💰 实时奖池分析")
    print("=" * 70)
    
    storage = LotteryStorage()
    analyzer = PrizePoolAnalyzer(storage)
    
    # 大乐透分析
    print("\n【大乐透】")
    dlt_report = analyzer.generate_analysis_report('dlt')
    
    if dlt_report['pool_analysis']:
        pool = dlt_report['pool_analysis']
        print(f"  最新期号：{pool['latest_issue']}")
        print(f"  开奖日期：{pool['latest_date']}")
        print(f"  当前奖池：¥{pool['current_pool']:,.0f}")
        print(f"  10 期平均：¥{pool['avg_pool_10d']:,.0f}")
        print(f"  奖池趋势：{pool['pool_trend']}")
        print(f"  中奖难度：{pool['difficulty_rate']:.1f}% 未中一等奖")
    
    if dlt_report['sales_analysis']:
        sales = dlt_report['sales_analysis']
        print(f"\n  最新销售：¥{sales['latest_sales']:,.0f}")
        print(f"  平均销售：¥{sales['avg_sales']:,.0f}")
        print(f"  销售热度：{sales['heat']}")
    
    print(f"\n  综合建议：")
    for rec in dlt_report['overall_recommendation']:
        print(f"    {rec}")
    
    # 保存报告
    report_file = Path('/root/.openclaw/workspace/lottery/reports/prize_pool_analysis.json')
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(dlt_report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 报告已保存：reports/prize_pool_analysis.json")


if __name__ == "__main__":
    main()
