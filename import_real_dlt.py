#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入真实大乐透开奖数据
从 web_search 结果解析并导入
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage

# 真实大乐透数据（从 web_search 获取）
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


def main():
    storage = LotteryStorage()
    
    print("=" * 50)
    print("导入真实大乐透开奖数据")
    print("=" * 50)
    
    saved_count = 0
    skipped_count = 0
    
    for record in REAL_DLT_DATA:
        result = storage.save_lottery_result(
            lottery_type='dlt',
            issue=record['issue'],
            numbers={'front': record['front'], 'back': record['back']},
            draw_date=record['draw_date']
        )
        
        if result:
            saved_count += 1
            print(f"✅ 导入 {record['issue']} 期 ({record['draw_date']})")
        else:
            skipped_count += 1
    
    print(f"\n========== 导入完成 ==========")
    print(f"新增：{saved_count} 期")
    print(f"跳过（已存在）: {skipped_count} 期")
    
    stats = storage.get_statistics('dlt')
    print(f"\n大乐透总记录：{stats['total_records']} 期")
    print(f"最新期号：{stats['last_issue']}")
    
    return saved_count


if __name__ == "__main__":
    main()
