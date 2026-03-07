#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
策略跟踪和评估模块
- 保存每期 7 种策略的推荐结果
- 开奖后计算各策略中奖情况
- 统计中奖率和中奖金额
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List


class StrategyTracker:
    """策略跟踪器"""
    
    STRATEGY_NAMES = {
        'balanced': '均衡策略',
        'hot_tracking': '热号追踪',
        'cold_rebound': '冷号反弹',
        'odd_even': '奇偶均衡',
        'zone_distribution': '区间分布',
        'consecutive': '连号追踪',
        'warm_balance': '温号搭配',
    }
    
    def __init__(self, base_dir: str = "/root/.openclaw/workspace/lottery"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.stats_dir = self.base_dir / "stats"
        
        # 创建目录
        for dir_path in [self.data_dir, self.stats_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 文件路径
        self.ssq_recommend_file = self.data_dir / "ssq_recommend_all.json"
        self.dlt_recommend_file = self.data_dir / "dlt_recommend_all.json"
        self.ssq_stats_file = self.stats_dir / "ssq_strategy_stats.json"
        self.dlt_stats_file = self.stats_dir / "dlt_strategy_stats.json"
        
        # 初始化文件
        self._init_files()
    
    def _init_files(self):
        """初始化数据文件"""
        for file_path in [self.ssq_recommend_file, self.dlt_recommend_file]:
            if not file_path.exists():
                self._save_json(file_path, {"recommendations": []})
        
        for file_path in [self.ssq_stats_file, self.dlt_stats_file]:
            if not file_path.exists():
                self._save_json(file_path, {
                    "total_periods": 0,
                    "strategy_stats": {k: {"hits": 0, "total_prize": 0, "hit_rate": 0} 
                                       for k in self.STRATEGY_NAMES.keys()},
                    "best_strategy": None,
                    "last_update": None
                })
    
    def _load_json(self, file_path: Path) -> Dict:
        """加载 JSON 文件"""
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """保存 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def save_recommendations(self, lottery_type: str, issue: str, 
                            strategies_result: Dict[str, List[Dict]]):
        """
        保存所有策略的推荐结果
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            issue: 期号
            strategies_result: {策略名：[推荐号码列表]}
        """
        file_path = self.ssq_recommend_file if lottery_type == 'ssq' else self.dlt_recommend_file
        data = self._load_json(file_path)
        
        record = {
            "issue": issue,
            "created_at": datetime.now().isoformat(),
            "strategies": {}
        }
        
        for strategy_name, recommendations in strategies_result.items():
            record["strategies"][strategy_name] = {
                "name": self.STRATEGY_NAMES.get(strategy_name, strategy_name),
                "recommendations": recommendations
            }
        
        if "recommendations" not in data:
            data["recommendations"] = []
        
        # 插入到最前面
        data["recommendations"].insert(0, record)
        
        # 只保留最近 200 期
        data["recommendations"] = data["recommendations"][:200]
        
        self._save_json(file_path, data)
    
    def check_prize(self, lottery_type: str, issue: str, winning_numbers: Dict) -> Dict:
        """
        检查各策略中奖情况
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            issue: 期号
            winning_numbers: 开奖号码 {'red': [], 'blue': []} 或 {'front': [], 'back': []}
        
        Returns:
            各策略中奖统计
        """
        file_path = self.ssq_recommend_file if lottery_type == 'ssq' else self.dlt_recommend_file
        data = self._load_json(file_path)
        
        # 查找对应期号的推荐
        rec_record = None
        for rec in data.get("recommendations", []):
            if rec.get("issue") == issue:
                rec_record = rec
                break
        
        if not rec_record:
            return {"error": f"未找到期号 {issue} 的推荐记录"}
        
        results = {}
        
        for strategy_name, strategy_data in rec_record.get("strategies", {}).items():
            hits = {"level_1": 0, "level_2": 0, "level_3": 0, "level_4": 0, 
                    "level_5": 0, "level_6": 0, "total_prize": 0}
            
            for rec in strategy_data.get("recommendations", []):
                prize = self._calculate_prize(lottery_type, rec, winning_numbers)
                if prize["level"]:
                    hits[f"level_{prize['level']}"] += 1
                    hits["total_prize"] += prize["amount"]
            
            results[strategy_name] = hits
        
        # 更新统计
        self._update_stats(lottery_type, results)
        
        return results
    
    def _calculate_prize(self, lottery_type: str, recommendation: Dict, 
                        winning_numbers: Dict) -> Dict:
        """
        计算单注中奖金额
        
        Returns:
            {'level': 1-6 或 0, 'amount': 金额}
        """
        if lottery_type == 'ssq':
            red_match = len(set(recommendation.get('red', [])) & set(winning_numbers.get('red', [])))
            blue_match = 1 if recommendation.get('blue', [])[0] in winning_numbers.get('blue', []) else 0
            
            # 双色球奖级
            if red_match == 6 and blue_match == 1:
                return {"level": 1, "amount": 5000000}  # 一等奖
            elif red_match == 6 and blue_match == 0:
                return {"level": 2, "amount": 100000}   # 二等奖
            elif red_match == 5 and blue_match == 1:
                return {"level": 3, "amount": 3000}     # 三等奖
            elif red_match == 5 or (red_match == 4 and blue_match == 1):
                return {"level": 4, "amount": 200}      # 四等奖
            elif red_match == 4 or (red_match == 3 and blue_match == 1):
                return {"level": 5, "amount": 10}       # 五等奖
            elif blue_match == 1:
                return {"level": 6, "amount": 5}        # 六等奖
        
        elif lottery_type == 'dlt':
            front_match = len(set(recommendation.get('front', [])) & set(winning_numbers.get('front', [])))
            back_match = len(set(recommendation.get('back', [])) & set(winning_numbers.get('back', [])))
            
            # 大乐透奖级（简化）
            if front_match == 5 and back_match == 2:
                return {"level": 1, "amount": 8000000}
            elif front_match == 5 and back_match == 1:
                return {"level": 2, "amount": 100000}
            elif front_match == 5 or (front_match == 4 and back_match == 2):
                return {"level": 3, "amount": 10000}
            elif front_match == 4 and back_match == 1 or front_match == 3 and back_match == 2:
                return {"level": 4, "amount": 300}
            elif front_match == 4 or front_match == 3 and back_match == 1 or front_match == 2 and back_match == 2:
                return {"level": 5, "amount": 15}
            elif front_match == 3 or front_match == 1 and back_match == 2 or front_match == 2 and back_match == 1 or front_match == 0 and back_match == 2:
                return {"level": 6, "amount": 5}
        
        return {"level": 0, "amount": 0}
    
    def _update_stats(self, lottery_type: str, results: Dict):
        """更新策略统计"""
        stats_file = self.ssq_stats_file if lottery_type == 'ssq' else self.dlt_stats_file
        stats = self._load_json(stats_file)
        
        stats["total_periods"] = stats.get("total_periods", 0) + 1
        
        for strategy_name, hits in results.items():
            if strategy_name not in stats["strategy_stats"]:
                stats["strategy_stats"][strategy_name] = {"hits": 0, "total_prize": 0, "hit_rate": 0}
            
            total_hits = sum(hits.get(f"level_{i}", 0) for i in range(1, 7))
            stats["strategy_stats"][strategy_name]["hits"] += total_hits
            stats["strategy_stats"][strategy_name]["total_prize"] += hits.get("total_prize", 0)
            stats["strategy_stats"][strategy_name]["hit_rate"] = (
                stats["strategy_stats"][strategy_name]["hits"] / 
                (stats["total_periods"] * 5) * 100  # 每策略 5 注
            )
        
        # 找出最佳策略
        best = max(stats["strategy_stats"].items(), 
                   key=lambda x: x[1].get("total_prize", 0))
        stats["best_strategy"] = {
            "name": best[0],
            "name_cn": self.STRATEGY_NAMES.get(best[0], best[0]),
            "total_prize": best[1].get("total_prize", 0),
            "hit_rate": best[1].get("hit_rate", 0)
        }
        
        stats["last_update"] = datetime.now().isoformat()
        
        self._save_json(stats_file, stats)
    
    def get_best_strategy(self, lottery_type: str) -> Dict:
        """获取当前最佳策略"""
        stats_file = self.ssq_stats_file if lottery_type == 'ssq' else self.dlt_stats_file
        stats = self._load_json(stats_file)
        return stats.get("best_strategy", {"name": "balanced", "name_cn": "均衡策略"})
    
    def get_summary(self, lottery_type: str) -> Dict:
        """获取策略汇总"""
        stats_file = self.ssq_stats_file if lottery_type == 'ssq' else self.dlt_stats_file
        return self._load_json(stats_file)
