#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理旧数据并导入真实开奖数据
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage

# 真实双色球数据
REAL_SSQ_DATA = [
    {"issue": "2026023", "draw_date": "2026-03-03", "red": [1, 3, 8, 10, 23, 29], "blue": [6]},
    {"issue": "2026022", "draw_date": "2026-03-01", "red": [15, 18, 23, 25, 28, 32], "blue": [11]},
    {"issue": "2026021", "draw_date": "2026-02-26", "red": [3, 13, 25, 26, 30, 31], "blue": [4]},
    {"issue": "2026020", "draw_date": "2026-02-24", "red": [1, 13, 14, 21, 24, 30], "blue": [2]},
    {"issue": "2026019", "draw_date": "2026-02-12", "red": [7, 8, 16, 17, 18, 30], "blue": [1]},
    {"issue": "2026018", "draw_date": "2026-02-10", "red": [11, 15, 17, 22, 25, 30], "blue": [7]},
    {"issue": "2026017", "draw_date": "2026-02-08", "red": [1, 3, 5, 18, 29, 32], "blue": [4]},
    {"issue": "2026016", "draw_date": "2026-02-05", "red": [4, 5, 9, 10, 27, 30], "blue": [13]},
    {"issue": "2026015", "draw_date": "2026-02-03", "red": [7, 10, 13, 22, 27, 31], "blue": [12]},
    {"issue": "2026014", "draw_date": "2026-02-01", "red": [7, 13, 19, 22, 26, 32], "blue": [1]},
    {"issue": "2026013", "draw_date": "2026-01-29", "red": [4, 9, 12, 13, 16, 20], "blue": [1]},
    {"issue": "2026012", "draw_date": "2026-01-27", "red": [3, 5, 7, 16, 20, 24], "blue": [8]},
    {"issue": "2026011", "draw_date": "2026-01-25", "red": [2, 3, 4, 20, 31, 32], "blue": [4]},
    {"issue": "2026010", "draw_date": "2026-01-22", "red": [4, 9, 10, 15, 19, 26], "blue": [12]},
    {"issue": "2026009", "draw_date": "2026-01-20", "red": [3, 6, 13, 19, 23, 25], "blue": [10]},
    {"issue": "2026008", "draw_date": "2026-01-18", "red": [6, 9, 16, 27, 31, 33], "blue": [10]},
    {"issue": "2026007", "draw_date": "2026-01-15", "red": [1, 3, 5, 18, 29, 32], "blue": [4]},
    {"issue": "2026006", "draw_date": "2026-01-13", "red": [2, 6, 22, 23, 24, 28], "blue": [15]},
    {"issue": "2026005", "draw_date": "2026-01-11", "red": [1, 20, 22, 27, 30, 33], "blue": [10]},
    {"issue": "2026004", "draw_date": "2026-01-08", "red": [3, 7, 8, 9, 18, 32], "blue": [10]},
    {"issue": "2026003", "draw_date": "2026-01-06", "red": [5, 6, 9, 21, 28, 30], "blue": [16]},
    {"issue": "2026002", "draw_date": "2026-01-04", "red": [1, 5, 7, 18, 30, 32], "blue": [2]},
    {"issue": "2026001", "draw_date": "2026-01-01", "red": [2, 6, 11, 12, 13, 33], "blue": [15]},
]

# 真实大乐透数据
REAL_DLT_DATA = [
    {"issue": "2026021", "draw_date": "2026-03-02", "front": [5, 8, 12, 14, 17], "back": [4, 5]},
    {"issue": "2026020", "draw_date": "2026-02-28", "front": [1, 10, 21, 23, 29], "back": [10, 12]},
    {"issue": "2026019", "draw_date": "2026-02-25", "front": [12, 13, 14, 16, 31], "back": [4, 12]},
    {"issue": "2026018", "draw_date": "2026-02-11", "front": [9, 11, 19, 30, 35], "back": [1, 12]},
    {"issue": "2026017", "draw_date": "2026-02-09", "front": [4, 5, 10, 23, 31], "back": [7, 12]},
    {"issue": "2026016", "draw_date": "2026-02-07", "front": [8, 9, 12, 19, 24], "back": [1, 6]},
    {"issue": "2026015", "draw_date": "2026-02-04", "front": [1, 4, 10, 13, 17], "back": [3, 11]},
    {"issue": "2026014", "draw_date": "2026-02-02", "front": [16, 18, 23, 34, 35], "back": [1, 6]},
    {"issue": "2026013", "draw_date": "2026-01-31", "front": [3, 5, 6, 23, 26], "back": [1, 4]},
    {"issue": "2026012", "draw_date": "2026-01-28", "front": [1, 2, 9, 22, 25], "back": [1, 6]},
    {"issue": "2026011", "draw_date": "2026-01-26", "front": [14, 21, 23, 29, 33], "back": [2, 10]},
    {"issue": "2026010", "draw_date": "2026-01-24", "front": [2, 3, 13, 18, 26], "back": [2, 9]},
    {"issue": "2026009", "draw_date": "2026-01-21", "front": [5, 12, 13, 14, 33], "back": [5, 8]},
    {"issue": "2026008", "draw_date": "2026-01-19", "front": [3, 6, 17, 21, 33], "back": [5, 11]},
    {"issue": "2026007", "draw_date": "2026-01-17", "front": [1, 3, 13, 20, 26], "back": [3, 10]},
    {"issue": "2026006", "draw_date": "2026-01-14", "front": [5, 12, 18, 23, 35], "back": [6, 12]},
    {"issue": "2026005", "draw_date": "2026-01-12", "front": [2, 4, 16, 23, 35], "back": [6, 11]},
    {"issue": "2026004", "draw_date": "2026-01-10", "front": [5, 18, 23, 25, 32], "back": [5, 9]},
    {"issue": "2026003", "draw_date": "2026-01-07", "front": [2, 9, 11, 15, 16], "back": [2, 4]},
    {"issue": "2026002", "draw_date": "2026-01-05", "front": [4, 8, 15, 20, 31], "back": [7, 8]},
    {"issue": "2026001", "draw_date": "2026-01-03", "front": [7, 9, 23, 27, 32], "back": [2, 8]},
]


def cleanup_data(storage: LotteryStorage):
    """清理旧的模拟数据，只保留真实数据"""
    print("清理旧数据...")
    
    # 清空双色球数据
    ssq_file = storage.ssq_history_file
    ssq_data = {
        "lottery_type": "ssq",
        "lottery_name": "双色球",
        "last_update": None,
        "total_records": 0,
        "records": []
    }
    storage._save_json(ssq_file, ssq_data)
    print("✅ 双色球数据已清空")
    
    # 清空大乐透数据
    dlt_file = storage.dlt_history_file
    dlt_data = {
        "lottery_type": "dlt",
        "lottery_name": "大乐透",
        "last_update": None,
        "total_records": 0,
        "records": []
    }
    storage._save_json(dlt_file, dlt_data)
    print("✅ 大乐透数据已清空")


def import_real_data():
    """导入真实数据"""
    storage = LotteryStorage()
    
    # 清理旧数据
    cleanup_data(storage)
    
    print("\n" + "=" * 50)
    print("导入真实双色球数据")
    print("=" * 50)
    
    # 倒序导入（从旧到新），这样最新期号会在最前面
    for record in reversed(REAL_SSQ_DATA):
        storage.save_lottery_result(
            lottery_type='ssq',
            issue=record['issue'],
            numbers={'red': record['red'], 'blue': record['blue']},
            draw_date=record['draw_date']
        )
    
    ssq_stats = storage.get_statistics('ssq')
    print(f"双色球总记录：{ssq_stats['total_records']} 期")
    print(f"最新期号：{ssq_stats['last_issue']}")
    
    print("\n" + "=" * 50)
    print("导入真实大乐透数据")
    print("=" * 50)
    
    # 倒序导入（从旧到新），这样最新期号会在最前面
    for record in reversed(REAL_DLT_DATA):
        storage.save_lottery_result(
            lottery_type='dlt',
            issue=record['issue'],
            numbers={'front': record['front'], 'back': record['back']},
            draw_date=record['draw_date']
        )
    
    dlt_stats = storage.get_statistics('dlt')
    print(f"大乐透总记录：{dlt_stats['total_records']} 期")
    print(f"最新期号：{dlt_stats['last_issue']}")
    
    print("\n" + "=" * 50)
    print("✅ 真实数据导入完成")
    print("=" * 50)


if __name__ == "__main__":
    import_real_data()
