#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票数据存储模块 - 文件存储方案
存储开奖历史、推荐记录、冷热号分析
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LotteryStorage:
    """彩票数据存储类"""
    
    def __init__(self, base_dir: str = "/root/.openclaw/workspace/lottery"):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "data"
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        
        # 创建目录
        for dir_path in [self.data_dir, self.config_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self.ssq_history_file = self.data_dir / "ssq_history.json"
        self.dlt_history_file = self.data_dir / "dlt_history.json"
        self.ssq_recommend_file = self.data_dir / "ssq_recommend.json"
        self.dlt_recommend_file = self.data_dir / "dlt_recommend.json"
        self.settings_file = self.config_dir / "settings.json"
        
        # 初始化文件
        self._init_files()
    
    def _init_files(self):
        """初始化数据文件"""
        # 双色球历史
        if not self.ssq_history_file.exists():
            self._save_json(self.ssq_history_file, {
                "lottery_type": "ssq",
                "lottery_name": "双色球",
                "last_update": None,
                "total_records": 0,
                "records": []
            })
        
        # 大乐透历史
        if not self.dlt_history_file.exists():
            self._save_json(self.dlt_history_file, {
                "lottery_type": "dlt",
                "lottery_name": "大乐透",
                "last_update": None,
                "total_records": 0,
                "records": []
            })
        
        # 双色球推荐
        if not self.ssq_recommend_file.exists():
            self._save_json(self.ssq_recommend_file, {
                "lottery_type": "ssq",
                "recommendations": []
            })
        
        # 大乐透推荐
        if not self.dlt_recommend_file.exists():
            self._save_json(self.dlt_recommend_file, {
                "lottery_type": "dlt",
                "recommendations": []
            })
        
        # 配置
        if not self.settings_file.exists():
            self._save_json(self.settings_file, {
                "ssq_push_time": "18:00",  # 双色球推送时间
                "dlt_push_time": "18:00",  # 大乐透推送时间
                "result_push_time": "21:30",  # 开奖结果推送时间
                "recommend_count": 5,  # 每次推荐注数
                "strategy": "balanced"  # 推荐策略
            })
        
        logger.info("数据文件初始化完成")
    
    def _load_json(self, file_path: Path, default: Optional[Dict] = None) -> Dict:
        """加载 JSON 文件"""
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析错误 {file_path}: {e}")
                return default if default else {}
        return default if default else {}
    
    def _save_json(self, file_path: Path, data: Dict):
        """保存 JSON 文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"数据已保存：{file_path}")
    
    def save_lottery_result(self, lottery_type: str, issue: str, 
                           numbers: Dict, draw_date: str,
                           pool_amount: int = 0, sales_amount: int = 0) -> bool:
        """保存单条开奖结果"""
        file_path = self.ssq_history_file if lottery_type == 'ssq' else self.dlt_history_file
        data = self._load_json(file_path)
        
        # 检查是否已存在
        if any(r.get("issue") == issue for r in data.get("records", [])):
            logger.info(f"期号 {issue} 已存在，跳过")
            return False
        
        # 添加新记录
        record = {
            "issue": issue,
            "draw_date": draw_date,
            "numbers": numbers,
            "pool_amount": pool_amount,
            "sales_amount": sales_amount,
            "created_at": datetime.now().isoformat()
        }
        
        if "records" not in data:
            data["records"] = []
        
        data["records"].insert(0, record)
        data["last_update"] = datetime.now().isoformat()
        data["total_records"] = len(data["records"])
        
        self._save_json(file_path, data)
        return True
    
    def batch_save_lottery_results(self, lottery_type: str, results: List[Dict]) -> tuple:
        """
        批量保存开奖结果（性能优化）
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            results: 结果列表 [{'issue': '', 'draw_date': '', 'numbers': {}}, ...]
            
        Returns:
            (imported_count, skipped_count)
        """
        file_path = self.ssq_history_file if lottery_type == 'ssq' else self.dlt_history_file
        data = self._load_json(file_path)
        
        existing_issues = {r.get("issue") for r in data.get("records", [])}
        
        imported = 0
        skipped = 0
        
        for result in results:
            issue = result.get('issue')
            if issue in existing_issues:
                skipped += 1
                continue
            
            # 数据校验
            is_valid, msg = self.validate_lottery_result(lottery_type, issue, result.get('numbers'))
            if not is_valid:
                logger.warning(f"数据校验失败 {issue}: {msg}")
                skipped += 1
                continue
            
            record = {
                "issue": issue,
                "draw_date": result.get('draw_date'),
                "numbers": result.get('numbers'),
                "pool_amount": result.get('pool_amount', 0),
                "sales_amount": result.get('sales_amount', 0),
                "created_at": datetime.now().isoformat()
            }
            
            if "records" not in data:
                data["records"] = []
            
            data["records"].insert(0, record)
            imported += 1
            existing_issues.add(issue)
        
        # 一次性保存所有数据
        data["last_update"] = datetime.now().isoformat()
        data["total_records"] = len(data["records"])
        self._save_json(file_path, data)
        
        logger.info(f"批量导入完成：{imported}期新增，{skipped}期跳过")
        return imported, skipped
    
    def validate_lottery_result(self, lottery_type: str, issue: str, numbers: Dict) -> tuple:
        """
        验证开奖数据有效性
        
        Returns:
            (is_valid: bool, message: str)
        """
        import re
        
        # 验证期号格式 (YYYY + 3 位数字)
        if not re.match(r'^\d{7}$', issue):
            return False, f"期号格式错误：{issue} (应为 YYYY + 3 位数字)"
        
        if lottery_type == 'ssq':
            # 双色球验证
            red = numbers.get('red', [])
            blue = numbers.get('blue', [])
            
            if len(red) != 6:
                return False, f"红球数量错误：{len(red)} (应为 6 个)"
            if len(blue) != 1:
                return False, f"蓝球数量错误：{len(blue)} (应为 1 个)"
            if not all(1 <= n <= 33 for n in red):
                return False, "红球号码超出范围 (1-33)"
            if not all(1 <= n <= 16 for n in blue):
                return False, "蓝球号码超出范围 (1-16)"
            if len(red) != len(set(red)):
                return False, "红球号码重复"
            if len(blue) != len(set(blue)):
                return False, "蓝球号码重复"
                
        elif lottery_type == 'dlt':
            # 大乐透验证
            front = numbers.get('front', [])
            back = numbers.get('back', [])
            
            if len(front) != 5:
                return False, f"前区数量错误：{len(front)} (应为 5 个)"
            if len(back) != 2:
                return False, f"后区数量错误：{len(back)} (应为 2 个)"
            if not all(1 <= n <= 35 for n in front):
                return False, "前区号码超出范围 (1-35)"
            if not all(1 <= n <= 12 for n in back):
                return False, "后区号码超出范围 (1-12)"
            if len(front) != len(set(front)):
                return False, "前区号码重复"
            if len(back) != len(set(back)):
                return False, "后区号码重复"
        
        return True, "验证通过"
    
    def save_recommendation(self, lottery_type: str, issue: str, 
                           numbers: List[Dict], strategy: str) -> str:
        """
        保存推荐号码
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            issue: 推荐期号
            numbers: 推荐号码列表
            strategy: 推荐策略
            
        Returns:
            推荐记录 ID
        """
        file_path = self.ssq_recommend_file if lottery_type == 'ssq' else self.dlt_recommend_file
        data = self._load_json(file_path)
        
        rec_id = f"rec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        record = {
            "id": rec_id,
            "issue": issue,
            "created_at": datetime.now().isoformat(),
            "strategy": strategy,
            "numbers": numbers
        }
        
        if "recommendations" not in data:
            data["recommendations"] = []
        
        data["recommendations"].insert(0, record)
        # 只保留最近 100 条推荐
        data["recommendations"] = data["recommendations"][:100]
        
        self._save_json(file_path, data)
        logger.info(f"推荐记录已保存：{rec_id}")
        return rec_id
    
    def get_history(self, lottery_type: str, limit: int = 50) -> List[Dict]:
        """获取历史开奖数据"""
        file_path = self.ssq_history_file if lottery_type == 'ssq' else self.dlt_history_file
        data = self._load_json(file_path)
        return data.get("records", [])[:limit]
    
    def get_cold_hot_numbers(self, lottery_type: str, period: int = 30) -> Dict:
        """
        计算冷热号
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            period: 统计最近 N 期
            
        Returns:
            {'hot': [], 'cold': [], 'frequency': {}}
        """
        history = self.get_history(lottery_type, period)
        
        if not history:
            return {"hot": [], "cold": [], "frequency": {}}
        
        # 统计频率
        freq = {}
        for record in history:
            numbers = record.get("numbers", {})
            # 双色球
            for num in numbers.get("red", []):
                freq[num] = freq.get(num, 0) + 1
            for num in numbers.get("blue", []):
                freq[num] = freq.get(num, 0) + 1
            # 大乐透
            for num in numbers.get("front", []):
                freq[num] = freq.get(num, 0) + 1
            for num in numbers.get("back", []):
                freq[num] = freq.get(num, 0) + 1
        
        # 排序
        sorted_nums = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        
        hot_numbers = [n[0] for n in sorted_nums[:10]]  # 热号前 10
        cold_numbers = [n[0] for n in sorted_nums[-10:]]  # 冷号后 10
        
        return {
            "hot": hot_numbers,
            "cold": cold_numbers,
            "frequency": freq
        }
    
    def get_last_issue(self, lottery_type: str) -> Optional[str]:
        """获取最新期号"""
        history = self.get_history(lottery_type, 1)
        if history:
            return history[0].get("issue")
        return None
    
    def generate_recommendation(self, lottery_type: str, issue: str, 
                               strategy: str = "balanced") -> List[Dict]:
        """
        生成推荐号码
        
        Args:
            lottery_type: 'ssq' 或 'dlt'
            issue: 推荐期号
            strategy: 'balanced' | 'hot' | 'cold' | 'random'
            
        Returns:
            推荐号码列表
        """
        cold_hot = self.get_cold_hot_numbers(lottery_type, 30)
        recommendations = []
        
        if lottery_type == 'ssq':
            # 双色球：红球 6 个 (1-33) + 蓝球 1 个 (1-16)
            red_hot = [n for n in cold_hot["hot"] if n <= 33]
            red_cold = [n for n in cold_hot["cold"] if n <= 33]
            blue_hot = [n for n in cold_hot["hot"] if n <= 16]
            blue_cold = [n for n in cold_hot["cold"] if n <= 16]
            
            for _ in range(5):  # 生成 5 注
                if strategy == "hot":
                    red = random.sample(red_hot if len(red_hot) >= 6 else list(range(1, 34)), 6)
                    blue = random.sample(blue_hot if len(blue_hot) >= 1 else list(range(1, 17)), 1)
                elif strategy == "cold":
                    red = random.sample(red_cold if len(red_cold) >= 6 else list(range(1, 34)), 6)
                    blue = random.sample(blue_cold if len(blue_cold) >= 1 else list(range(1, 17)), 1)
                else:  # balanced or random
                    # 均衡策略：4 热 2 冷
                    red = random.sample(red_hot, min(4, len(red_hot))) + \
                          random.sample(red_cold, min(2, len(red_cold)))
                    if len(red) < 6:
                        red += random.sample([n for n in range(1, 34) if n not in red], 6 - len(red))
                    blue = random.sample(blue_hot + blue_cold, 1) if (blue_hot or blue_cold) else random.sample(range(1, 17), 1)
                
                recommendations.append({
                    "red": sorted(red),
                    "blue": sorted(blue)
                })
        
        elif lottery_type == 'dlt':
            # 大乐透：前区 5 个 (1-35) + 后区 2 个 (1-12)
            front_hot = [n for n in cold_hot["hot"] if n <= 35]
            front_cold = [n for n in cold_hot["cold"] if n <= 35]
            back_hot = [n for n in cold_hot["hot"] if n <= 12]
            back_cold = [n for n in cold_hot["cold"] if n <= 12]
            
            for _ in range(5):  # 生成 5 注
                if strategy == "hot":
                    front = random.sample(front_hot if len(front_hot) >= 5 else list(range(1, 36)), 5)
                    back = random.sample(back_hot if len(back_hot) >= 2 else list(range(1, 13)), 2)
                elif strategy == "cold":
                    front = random.sample(front_cold if len(front_cold) >= 5 else list(range(1, 36)), 5)
                    back = random.sample(back_cold if len(back_cold) >= 2 else list(range(1, 13)), 2)
                else:  # balanced or random
                    # 均衡策略：3 热 2 冷
                    front = random.sample(front_hot, min(3, len(front_hot))) + \
                            random.sample(front_cold, min(2, len(front_cold)))
                    if len(front) < 5:
                        front += random.sample([n for n in range(1, 36) if n not in front], 5 - len(front))
                    back = random.sample(back_hot + back_cold, 2) if len(back_hot + back_cold) >= 2 else random.sample(range(1, 13), 2)
                
                recommendations.append({
                    "front": sorted(front),
                    "back": sorted(back)
                })
        
        return recommendations
    
    def get_settings(self) -> Dict:
        """获取配置"""
        return self._load_json(self.settings_file, {})
    
    def update_settings(self, settings: Dict):
        """更新配置"""
        current = self.get_settings()
        current.update(settings)
        self._save_json(self.settings_file, current)
    
    def get_statistics(self, lottery_type: str) -> Dict:
        """获取统计信息"""
        file_path = self.ssq_history_file if lottery_type == 'ssq' else self.dlt_history_file
        data = self._load_json(file_path)
        
        return {
            "lottery_type": lottery_type,
            "total_records": data.get("total_records", 0),
            "last_update": data.get("last_update"),
            "last_issue": self.get_last_issue(lottery_type)
        }


# 测试代码
if __name__ == "__main__":
    storage = LotteryStorage()
    
    # 测试保存开奖结果
    storage.save_lottery_result(
        lottery_type="ssq",
        issue="2026023",
        numbers={"red": [5, 12, 18, 23, 27, 31], "blue": [9]},
        draw_date="2026-03-03",
        pool_amount=700000000,
        sales_amount=200000000
    )
    
    # 测试生成推荐
    rec = storage.generate_recommendation("ssq", "2026024", "balanced")
    print(f"生成推荐：{rec}")
    
    # 测试保存推荐
    rec_id = storage.save_recommendation("ssq", "2026024", rec, "balanced")
    print(f"推荐 ID: {rec_id}")
    
    # 测试统计
    stats = storage.get_statistics("ssq")
    print(f"统计：{stats}")
