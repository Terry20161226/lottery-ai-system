#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户反馈收集系统
- 收集中奖反馈
- 统计策略效果
- 生成反馈报告
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

FEEDBACK_FILE = '/root/.openclaw/workspace/lottery/feedback/feedback_log.json'
FEEDBACK_DIR = '/root/.openclaw/workspace/lottery/feedback'


class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self):
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict:
        """加载反馈数据"""
        if os.path.exists(FEEDBACK_FILE):
            with open(FEEDBACK_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'submissions': [],
            'statistics': {
                'total_submissions': 0,
                'wins': 0,
                'losses': 0,
                'by_strategy': {},
                'by_lottery_type': {'ssq': {'wins': 0, 'total': 0}, 'dlt': {'wins': 0, 'total': 0}}
            }
        }
    
    def _save_feedback(self):
        """保存反馈数据"""
        with open(FEEDBACK_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.feedback_data, f, ensure_ascii=False, indent=2)
    
    def submit_feedback(
        self,
        lottery_type: str,
        issue: str,
        strategy: str,
        recommended_numbers: List,
        actual_numbers: List,
        win_level: str,
        user_id: str = 'anonymous'
    ):
        """
        提交反馈
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            issue: 期号
            strategy: 使用的策略名称
            recommended_numbers: 推荐的号码
            actual_numbers: 实际开奖号码
            win_level: 中奖等级 ('未中奖', '六等奖', '五等奖', ..., '一等奖')
            user_id: 用户 ID
        """
        feedback = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'lottery_type': lottery_type,
            'issue': issue,
            'strategy': strategy,
            'recommended_numbers': recommended_numbers,
            'actual_numbers': actual_numbers,
            'win_level': win_level,
            'is_win': win_level != '未中奖'
        }
        
        self.feedback_data['submissions'].append(feedback)
        
        # 更新统计
        stats = self.feedback_data['statistics']
        stats['total_submissions'] += 1
        
        if feedback['is_win']:
            stats['wins'] += 1
        else:
            stats['losses'] += 1
        
        # 按彩种统计
        if lottery_type in stats['by_lottery_type']:
            stats['by_lottery_type'][lottery_type]['total'] += 1
            if feedback['is_win']:
                stats['by_lottery_type'][lottery_type]['wins'] += 1
        
        # 按策略统计
        if strategy not in stats['by_strategy']:
            stats['by_strategy'][strategy] = {'wins': 0, 'total': 0}
        stats['by_strategy'][strategy]['total'] += 1
        if feedback['is_win']:
            stats['by_strategy'][strategy]['wins'] += 1
        
        self._save_feedback()
        print(f"✅ 反馈已记录：{lottery_type} 第{issue}期 - {win_level}")
    
    def get_statistics(self) -> Dict:
        """获取统计数据"""
        return self.feedback_data['statistics']
    
    def get_strategy_ranking(self) -> List[Dict]:
        """获取策略胜率排名"""
        strategies = []
        for name, stats in self.feedback_data['statistics']['by_strategy'].items():
            if stats['total'] > 0:
                win_rate = stats['wins'] / stats['total']
                strategies.append({
                    'strategy': name,
                    'wins': stats['wins'],
                    'total': stats['total'],
                    'win_rate': round(win_rate, 3)
                })
        return sorted(strategies, key=lambda x: x['win_rate'], reverse=True)
    
    def generate_report(self, days: int = 7) -> str:
        """生成反馈报告"""
        stats = self.get_statistics()
        ranking = self.get_strategy_ranking()
        
        report = []
        report.append("=" * 60)
        report.append("📊 用户反馈报告")
        report.append("=" * 60)
        report.append(f"\n总反馈数：{stats['total_submissions']}")
        report.append(f"中奖次数：{stats['wins']}")
        report.append(f"未中奖次数：{stats['losses']}")
        
        overall_rate = stats['wins'] / stats['total_submissions'] if stats['total_submissions'] > 0 else 0
        report.append(f"总体中奖率：{overall_rate:.1%}")
        
        report.append("\n【彩种统计】")
        for lt, data in stats['by_lottery_type'].items():
            name = '双色球' if lt == 'ssq' else '大乐透'
            rate = data['wins'] / data['total'] if data['total'] > 0 else 0
            report.append(f"  {name}: {data['wins']}/{data['total']} ({rate:.1%})")
        
        report.append("\n【策略胜率排名】")
        for i, item in enumerate(ranking[:5], 1):
            report.append(f"  {i}. {item['strategy']}: {item['win_rate']:.1%} ({item['wins']}/{item['total']})")
        
        report.append("\n" + "=" * 60)
        return "\n".join(report)


def main():
    """主函数"""
    collector = FeedbackCollector()
    
    # 示例：提交反馈
    print("📝 反馈收集系统")
    print("=" * 60)
    
    # 显示当前统计
    stats = collector.get_statistics()
    print(f"当前总反馈数：{stats['total_submissions']}")
    print(f"当前中奖数：{stats['wins']}")
    
    # 生成报告
    if stats['total_submissions'] > 0:
        print("\n" + collector.generate_report())
    else:
        print("\n暂无反馈数据")
        print("\n使用说明：")
        print("1. 在 push_best_strategy.py 中添加反馈收集")
        print("2. 用户收到推荐后，可通过钉钉回复中奖情况")
        print("3. 系统自动记录并更新统计")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
