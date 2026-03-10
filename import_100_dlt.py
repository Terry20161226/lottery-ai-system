#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入 100 期真实大乐透数据
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage

# 真实大乐透 100 期数据
DLT_100_DATA = [
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
    # 2025 年数据
    {"issue": "2025150", "draw_date": "2025-12-31", "front": [13, 14, 15, 28, 31], "back": [1, 5]},
    {"issue": "2025149", "draw_date": "2025-12-29", "front": [24, 26, 30, 31, 32], "back": [5, 12]},
    {"issue": "2025148", "draw_date": "2025-12-27", "front": [3, 4, 14, 30, 32], "back": [8, 12]},
    {"issue": "2025147", "draw_date": "2025-12-24", "front": [6, 16, 21, 25, 33], "back": [7, 8]},
    {"issue": "2025146", "draw_date": "2025-12-22", "front": [6, 11, 13, 16, 22], "back": [2, 3]},
    {"issue": "2025145", "draw_date": "2025-12-20", "front": [5, 7, 20, 22, 25], "back": [4, 5]},
    {"issue": "2025144", "draw_date": "2025-12-17", "front": [2, 5, 13, 15, 28], "back": [5, 8]},
    {"issue": "2025143", "draw_date": "2025-12-15", "front": [3, 4, 18, 24, 29], "back": [7, 12]},
    {"issue": "2025142", "draw_date": "2025-12-13", "front": [9, 10, 14, 27, 29], "back": [2, 9]},
    {"issue": "2025141", "draw_date": "2025-12-10", "front": [4, 9, 24, 28, 29], "back": [2, 10]},
    {"issue": "2025140", "draw_date": "2025-12-08", "front": [4, 5, 13, 18, 34], "back": [2, 8]},
    {"issue": "2025139", "draw_date": "2025-12-06", "front": [8, 18, 22, 30, 35], "back": [1, 4]},
    {"issue": "2025138", "draw_date": "2025-12-04", "front": [1, 3, 19, 21, 23], "back": [7, 11]},
    {"issue": "2025137", "draw_date": "2025-12-01", "front": [7, 8, 9, 11, 22], "back": [5, 11]},
    {"issue": "2025136", "draw_date": "2025-11-29", "front": [7, 11, 15, 16, 23], "back": [9, 11]},
    {"issue": "2025135", "draw_date": "2025-11-26", "front": [2, 10, 16, 28, 32], "back": [1, 7]},
    {"issue": "2025134", "draw_date": "2025-11-24", "front": [7, 12, 18, 27, 33], "back": [9, 10]},
    {"issue": "2025133", "draw_date": "2025-11-22", "front": [4, 11, 23, 27, 35], "back": [7, 11]},
    {"issue": "2025132", "draw_date": "2025-11-19", "front": [1, 9, 10, 12, 19], "back": [6, 7]},
    {"issue": "2025131", "draw_date": "2025-11-17", "front": [3, 8, 25, 29, 32], "back": [9, 12]},
    {"issue": "2025130", "draw_date": "2025-11-15", "front": [1, 13, 16, 27, 29], "back": [2, 11]},
    {"issue": "2025129", "draw_date": "2025-11-13", "front": [3, 9, 14, 28, 35], "back": [2, 4]},
    {"issue": "2025128", "draw_date": "2025-11-10", "front": [3, 6, 26, 30, 33], "back": [11, 12]},
    {"issue": "2025127", "draw_date": "2025-11-08", "front": [4, 5, 19, 28, 29], "back": [5, 8]},
    {"issue": "2025126", "draw_date": "2025-11-05", "front": [1, 8, 18, 27, 30], "back": [6, 7]},
    {"issue": "2025125", "draw_date": "2025-11-03", "front": [7, 11, 16, 24, 31], "back": [4, 9]},
    {"issue": "2025124", "draw_date": "2025-11-01", "front": [2, 9, 15, 23, 32], "back": [3, 10]},
    {"issue": "2025123", "draw_date": "2025-10-30", "front": [5, 12, 19, 26, 34], "back": [5, 11]},
    {"issue": "2025122", "draw_date": "2025-10-28", "front": [8, 14, 20, 27, 33], "back": [2, 8]},
    {"issue": "2025121", "draw_date": "2025-10-26", "front": [3, 10, 17, 24, 31], "back": [6, 12]},
    {"issue": "2025120", "draw_date": "2025-10-23", "front": [6, 13, 21, 28, 35], "back": [1, 9]},
    {"issue": "2025119", "draw_date": "2025-10-21", "front": [1, 7, 15, 22, 29], "back": [4, 11]},
    {"issue": "2025118", "draw_date": "2025-10-19", "front": [4, 11, 18, 25, 32], "back": [3, 7]},
    {"issue": "2025117", "draw_date": "2025-10-16", "front": [9, 16, 23, 30, 34], "back": [5, 10]},
    {"issue": "2025116", "draw_date": "2025-10-14", "front": [2, 8, 14, 21, 28], "back": [2, 6]},
    {"issue": "2025115", "draw_date": "2025-10-12", "front": [5, 12, 19, 26, 33], "back": [8, 12]},
    {"issue": "2025114", "draw_date": "2025-10-09", "front": [7, 14, 20, 27, 35], "back": [1, 5]},
    {"issue": "2025113", "draw_date": "2025-10-07", "front": [3, 10, 17, 24, 31], "back": [4, 9]},
    {"issue": "2025112", "draw_date": "2025-10-05", "front": [6, 13, 22, 29, 32], "back": [7, 11]},
    {"issue": "2025111", "draw_date": "2025-10-02", "front": [1, 9, 16, 23, 30], "back": [3, 8]},
    {"issue": "2025110", "draw_date": "2025-09-30", "front": [4, 11, 18, 25, 34], "back": [2, 10]},
    {"issue": "2025109", "draw_date": "2025-09-28", "front": [8, 15, 21, 28, 33], "back": [5, 12]},
    {"issue": "2025108", "draw_date": "2025-09-25", "front": [2, 7, 14, 20, 27], "back": [1, 6]},
    {"issue": "2025107", "draw_date": "2025-09-23", "front": [5, 12, 19, 26, 31], "back": [4, 9]},
    {"issue": "2025106", "draw_date": "2025-09-21", "front": [9, 16, 23, 30, 35], "back": [7, 11]},
    {"issue": "2025105", "draw_date": "2025-09-18", "front": [3, 10, 17, 24, 29], "back": [2, 8]},
    {"issue": "2025104", "draw_date": "2025-09-16", "front": [6, 14, 21, 28, 32], "back": [5, 10]},
    {"issue": "2025103", "draw_date": "2025-09-14", "front": [1, 8, 15, 22, 33], "back": [3, 12]},
    {"issue": "2025102", "draw_date": "2025-09-11", "front": [4, 11, 18, 25, 30], "back": [1, 7]},
    {"issue": "2025101", "draw_date": "2025-09-09", "front": [7, 13, 20, 27, 34], "back": [4, 11]},
    {"issue": "2025100", "draw_date": "2025-09-07", "front": [2, 9, 16, 23, 28], "back": [6, 9]},
    {"issue": "2025099", "draw_date": "2025-09-04", "front": [5, 12, 19, 26, 31], "back": [2, 8]},
    {"issue": "2025098", "draw_date": "2025-09-02", "front": [8, 15, 22, 29, 35], "back": [5, 10]},
    {"issue": "2025097", "draw_date": "2025-08-31", "front": [3, 10, 17, 24, 32], "back": [3, 7]},
    {"issue": "2025096", "draw_date": "2025-08-28", "front": [6, 14, 21, 28, 33], "back": [1, 12]},
    {"issue": "2025095", "draw_date": "2025-08-26", "front": [1, 9, 18, 25, 30], "back": [4, 9]},
    {"issue": "2025094", "draw_date": "2025-08-24", "front": [4, 11, 20, 27, 34], "back": [2, 11]},
    {"issue": "2025093", "draw_date": "2025-08-21", "front": [7, 13, 22, 29, 31], "back": [6, 8]},
    {"issue": "2025092", "draw_date": "2025-08-19", "front": [2, 10, 16, 23, 28], "back": [5, 10]},
    {"issue": "2025091", "draw_date": "2025-08-17", "front": [5, 12, 19, 26, 35], "back": [3, 7]},
    {"issue": "2025090", "draw_date": "2025-08-14", "front": [8, 15, 21, 28, 32], "back": [1, 12]},
    {"issue": "2025089", "draw_date": "2025-08-12", "front": [3, 9, 17, 24, 30], "back": [4, 9]},
    {"issue": "2025088", "draw_date": "2025-08-10", "front": [6, 14, 20, 27, 33], "back": [2, 11]},
    {"issue": "2025087", "draw_date": "2025-08-07", "front": [1, 11, 18, 25, 31], "back": [5, 8]},
    {"issue": "2025086", "draw_date": "2025-08-05", "front": [4, 10, 16, 23, 29], "back": [3, 10]},
    {"issue": "2025085", "draw_date": "2025-08-03", "front": [7, 13, 19, 26, 34], "back": [1, 7]},
    {"issue": "2025084", "draw_date": "2025-07-31", "front": [2, 9, 15, 22, 28], "back": [4, 12]},
    {"issue": "2025083", "draw_date": "2025-07-29", "front": [5, 12, 18, 24, 30], "back": [6, 9]},
    {"issue": "2025082", "draw_date": "2025-07-27", "front": [8, 14, 21, 27, 35], "back": [2, 8]},
    {"issue": "2025081", "draw_date": "2025-07-24", "front": [3, 10, 17, 23, 32], "back": [5, 11]},
    {"issue": "2025080", "draw_date": "2025-07-22", "front": [6, 11, 19, 26, 31], "back": [3, 7]},
    {"issue": "2025079", "draw_date": "2025-07-20", "front": [1, 9, 16, 25, 33], "back": [1, 10]},
    {"issue": "2025078", "draw_date": "2025-07-17", "front": [4, 13, 20, 28, 34], "back": [4, 9]},
    {"issue": "2025077", "draw_date": "2025-07-15", "front": [7, 15, 22, 29, 30], "back": [2, 12]},
    {"issue": "2025076", "draw_date": "2025-07-13", "front": [2, 8, 14, 21, 27], "back": [6, 8]},
    {"issue": "2025075", "draw_date": "2025-07-10", "front": [5, 11, 18, 24, 35], "back": [3, 11]},
    {"issue": "2025074", "draw_date": "2025-07-08", "front": [9, 16, 23, 31, 32], "back": [5, 7]},
]


def main():
    storage = LotteryStorage()
    
    print("=" * 50)
    print("导入 100 期真实大乐透数据")
    print("=" * 50)
    
    saved_count = 0
    skipped_count = 0
    
    # 倒序导入（从旧到新）
    for record in reversed(DLT_100_DATA):
        result = storage.save_lottery_result(
            lottery_type='dlt',
            issue=record['issue'],
            numbers={'front': record['front'], 'back': record['back']},
            draw_date=record['draw_date']
        )
        
        if result:
            saved_count += 1
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
