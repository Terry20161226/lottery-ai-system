#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动开奖核对模块
- 监听开奖结果
- 自动核对中奖情况
- 生成中奖统计报告
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage

# 推荐文件路径
DATA_DIR = Path('/root/.openclaw/workspace/lottery/data')
SSQ_RECOMMEND_FILE = DATA_DIR / 'ssq_recommend.json'
DLT_RECOMMEND_FILE = DATA_DIR / 'dlt_recommend.json'


class AutoPrizeChecker:
    """自动开奖核对器"""
    
    def __init__(self):
        self.storage = LotteryStorage()
    
    def _load_json(self, file_path: Path) -> dict:
        """加载 JSON 文件"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _get_recommendations_by_issue(self, lottery_type: str, issue: str) -> dict:
        """按期号获取推荐"""
        file_path = SSQ_RECOMMEND_FILE if lottery_type == 'ssq' else DLT_RECOMMEND_FILE
        data = self._load_json(file_path)
        
        for rec in data.get('recommendations', []):
            if rec.get('issue') == issue:
                return rec.get('strategies', {})
        
        return {}
    
    def check_ssq_prize(self, issue: str, winning_numbers: dict) -> dict:
        """
        核对双色球中奖情况
        
        Args:
            issue: 期号
            winning_numbers: 开奖号码 {'red': [...], 'blue': [...]}
        
        Returns:
            中奖统计
        """
        # 获取该期推荐（从推荐文件中查找）
        recommendations = self._get_recommendations_by_issue('ssq', issue)
        
        if not recommendations:
            return {'issue': issue, 'status': 'no_recommendation'}
        
        stats = {
            'issue': issue,
            'lottery_type': 'ssq',
            'winning_numbers': winning_numbers,
            'total_notes': 0,
            'hit_stats': {
                '6+1': 0,  # 一等奖
                '6+0': 0,  # 二等奖
                '5+1': 0,  # 三等奖
                '5+0': 0,  # 四等奖
                '4+1': 0,  # 五等奖
                '4+0': 0,  # 六等奖
                '3+1': 0,  # 六等奖
                '2+1': 0,  # 六等奖
                '1+1': 0,  # 六等奖
                '0+1': 0,  # 六等奖
            },
            'details': []
        }
        
        red_winning = set(winning_numbers.get('red', []))
        blue_winning = set(winning_numbers.get('blue', []))
        
        for strategy_name, notes in recommendations.items():
            if not isinstance(notes, list):
                continue
            for note in notes:
                if not isinstance(note, dict):
                    continue
                stats['total_notes'] += 1
                
                red_note = set(note.get('red', []))
                blue_note = set(note.get('blue', []))
                
                red_hit = len(red_winning & red_note)
                blue_hit = len(blue_winning & blue_note)
                
                hit_key = f"{red_hit}+{blue_hit}"
                if hit_key in stats['hit_stats']:
                    stats['hit_stats'][hit_key] += 1
                
                stats['details'].append({
                    'strategy': strategy_name,
                    'numbers': note,
                    'red_hit': red_hit,
                    'blue_hit': blue_hit,
                    'hit_level': hit_key
                })
        
        return stats
    
    def check_dlt_prize(self, issue: str, winning_numbers: dict) -> dict:
        """
        核对大乐透中奖情况
        
        Args:
            issue: 期号
            winning_numbers: 开奖号码 {'front': [...], 'back': [...]}
        
        Returns:
            中奖统计
        """
        # 获取该期推荐
        recommendations = self._get_recommendations_by_issue('dlt', issue)
        
        if not recommendations:
            return {'issue': issue, 'status': 'no_recommendation'}
        
        stats = {
            'issue': issue,
            'lottery_type': 'dlt',
            'winning_numbers': winning_numbers,
            'total_notes': 0,
            'hit_stats': {
                '5+2': 0,  # 一等奖
                '5+1': 0,  # 二等奖
                '5+0': 0,  # 三等奖
                '4+2': 0,  # 四等奖
                '4+1': 0,  # 五等奖
                '3+2': 0,  # 六等奖
                '4+0': 0,  # 六等奖
                '3+1': 0,  # 七等奖
                '2+2': 0,  # 七等奖
                '3+0': 0,  # 八等奖
                '1+2': 0,  # 八等奖
                '2+1': 0,  # 九等奖
                '2+0': 0,  # 九等奖
                '0+2': 0,  # 九等奖
            },
            'details': []
        }
        
        front_winning = set(winning_numbers.get('front', []))
        back_winning = set(winning_numbers.get('back', []))
        
        for strategy_name, notes in recommendations.items():
            if not isinstance(notes, list):
                continue
            for note in notes:
                if not isinstance(note, dict):
                    continue
                stats['total_notes'] += 1
                
                front_note = set(note.get('front', []))
                back_note = set(note.get('back', []))
                
                front_hit = len(front_winning & front_note)
                back_hit = len(back_winning & back_note)
                
                hit_key = f"{front_hit}+{back_hit}"
                if hit_key in stats['hit_stats']:
                    stats['hit_stats'][hit_key] += 1
                
                stats['details'].append({
                    'strategy': strategy_name,
                    'numbers': note,
                    'front_hit': front_hit,
                    'back_hit': back_hit,
                    'hit_level': hit_key
                })
        
        return stats
    
    def generate_report(self, prize_stats: list) -> str:
        """生成中奖报告"""
        lines = [
            "=" * 70,
            "🎉 开奖核对报告",
            "=" * 70,
            ""
        ]
        
        total_notes = 0
        total_hits = 0
        
        for stats in prize_stats:
            if stats.get('status') == 'no_recommendation':
                continue
            
            lines.append(f"【{stats['lottery_type'].upper()}】第 {stats['issue']} 期")
            lines.append(f"  推荐注数：{stats['total_notes']}")
            
            # 统计中奖情况
            hits = sum(v for k, v in stats['hit_stats'].items() if v > 0)
            if hits > 0:
                lines.append(f"  中奖注数：{hits}")
                for level, count in stats['hit_stats'].items():
                    if count > 0:
                        lines.append(f"    {level}球：{count}注")
                total_hits += hits
            
            total_notes += stats['total_notes']
            lines.append("")
        
        lines.append("=" * 70)
        lines.append(f"总计：推荐 {total_notes} 注，中奖 {total_hits} 注")
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def save_report(self, report: str, filename: str = None):
        """保存报告到文件"""
        if not filename:
            filename = f"prize_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        report_dir = Path('/root/.openclaw/workspace/lottery/reports')
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = report_dir / filename
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ 报告已保存：{report_path}")
        return report_path


def main():
    """主函数"""
    print("=" * 70)
    print("🎯 自动开奖核对")
    print("=" * 70)
    
    checker = AutoPrizeChecker()
    
    # 获取最近开奖期号
    storage = LotteryStorage()
    ssq_history = storage.get_history('ssq', 10)
    dlt_history = storage.get_history('dlt', 10)
    
    all_stats = []
    
    # 核对双色球
    print("\n【双色球核对】")
    for record in ssq_history:
        issue = record.get('issue')
        numbers = record.get('numbers', {})
        stats = checker.check_ssq_prize(issue, numbers)
        all_stats.append(stats)
        print(f"  第 {issue} 期：推荐 {stats.get('total_notes', 0)} 注")
    
    # 核对大乐透
    print("\n【大乐透核对】")
    for record in dlt_history:
        issue = record.get('issue')
        numbers = record.get('numbers', {})
        stats = checker.check_dlt_prize(issue, numbers)
        all_stats.append(stats)
        print(f"  第 {issue} 期：推荐 {stats.get('total_notes', 0)} 注")
    
    # 生成报告
    print("\n【生成报告】")
    report = checker.generate_report(all_stats)
    print(report)
    
    # 保存报告
    checker.save_report(report)
    
    print("\n" + "=" * 70)
    print("✅ 开奖核对完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
