#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手动修复双色球数据 - 从搜索结果导入
"""

import json
import os
from datetime import datetime

DATA_DIR = "/root/.openclaw/workspace/lottery/data"
SSQ_FILE = os.path.join(DATA_DIR, "ssq_history.json")

# 从百度搜索结果提取的双色球数据（2025 年部分）
SSQ_2025_DATA = [
    {"issue": "2025037", "draw_date": "2025-04-06", "red": [3, 6, 11, 20, 21, 31], "blue": [2]},
    {"issue": "2025036", "draw_date": "2025-04-03", "red": [5, 11, 13, 16, 19, 32], "blue": [7]},
    {"issue": "2025035", "draw_date": "2025-04-01", "red": [1, 8, 16, 18, 25, 31], "blue": [1]},
    {"issue": "2025034", "draw_date": "2025-03-30", "red": [5, 8, 13, 14, 24, 26], "blue": [12]},
    {"issue": "2025033", "draw_date": "2025-03-27", "red": [3, 5, 18, 25, 26, 33], "blue": [8]},
    {"issue": "2025032", "draw_date": "2025-03-25", "red": [3, 8, 10, 14, 16, 21], "blue": [3]},
    {"issue": "2025031", "draw_date": "2025-03-23", "red": [1, 5, 6, 8, 23, 28], "blue": [1]},
    {"issue": "2025030", "draw_date": "2025-03-20", "red": [4, 6, 7, 30, 31, 33], "blue": [6]},
    {"issue": "2025029", "draw_date": "2025-03-18", "red": [5, 15, 16, 25, 30, 33], "blue": [16]},
    {"issue": "2025028", "draw_date": "2025-03-16", "red": [4, 9, 14, 15, 18, 25], "blue": [15]},
    {"issue": "2025027", "draw_date": "2025-03-13", "red": [5, 7, 8, 15, 16, 23], "blue": [6]},
    {"issue": "2025026", "draw_date": "2025-03-11", "red": [9, 10, 12, 14, 19, 32], "blue": [7]},
    {"issue": "2025025", "draw_date": "2025-03-09", "red": [12, 15, 21, 23, 25, 30], "blue": [2]},
    {"issue": "2025024", "draw_date": "2025-03-06", "red": [10, 11, 22, 27, 30, 32], "blue": [15]},
    {"issue": "2025023", "draw_date": "2025-03-04", "red": [9, 12, 13, 24, 25, 33], "blue": [7]},
    {"issue": "2025022", "draw_date": "2025-03-02", "red": [11, 17, 18, 20, 28, 30], "blue": [10]},
    {"issue": "2025021", "draw_date": "2025-02-27", "red": [7, 8, 16, 18, 25, 32], "blue": [14]},
    {"issue": "2025020", "draw_date": "2025-02-25", "red": [4, 11, 13, 16, 26, 30], "blue": [15]},
    {"issue": "2025019", "draw_date": "2025-02-23", "red": [5, 13, 17, 18, 22, 23], "blue": [11]},
    {"issue": "2025018", "draw_date": "2025-02-20", "red": [3, 9, 18, 21, 28, 29], "blue": [11]},
]

def fix_ssq_data():
    """修复双色球数据"""
    
    # 加载现有数据
    if os.path.exists(SSQ_FILE):
        with open(SSQ_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"records": []}
    
    if "records" not in data:
        data = {"records": []}
    
    # 添加新数据（去重）
    existing_issues = {r.get("issue") for r in data["records"]}
    added_count = 0
    
    for item in SSQ_2025_DATA:
        if item["issue"] not in existing_issues:
            record = {
                "issue": item["issue"],
                "draw_date": item["draw_date"],
                "numbers": {
                    "red": sorted(item["red"]),
                    "blue": item["blue"]
                },
                "pool_amount": 0,
                "sales_amount": 0,
                "created_at": datetime.now().isoformat()
            }
            data["records"].append(record)
            added_count += 1
    
    # 按期号排序
    data["records"].sort(key=lambda x: x["issue"], reverse=True)
    
    # 保存
    with open(SSQ_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 双色球数据修复完成")
    print(f"   新增期数：{added_count}")
    print(f"   总期数：{len(data['records'])}")
    print(f"   最新期号：{data['records'][0]['issue']} ({data['records'][0]['draw_date']})")
    
    return added_count

if __name__ == "__main__":
    fix_ssq_data()
