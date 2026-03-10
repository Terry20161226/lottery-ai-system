#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入真实双色球开奖数据
从 web_search 结果解析并导入
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage

# 真实双色球数据（从 web_search 获取）
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


def main():
    storage = LotteryStorage()
    
    print("=" * 50)
    print("导入真实双色球开奖数据")
    print("=" * 50)
    
    saved_count = 0
    skipped_count = 0
    
    for record in REAL_SSQ_DATA:
        result = storage.save_lottery_result(
            lottery_type='ssq',
            issue=record['issue'],
            numbers={'red': record['red'], 'blue': record['blue']},
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
    
    stats = storage.get_statistics('ssq')
    print(f"\n双色球总记录：{stats['total_records']} 期")
    print(f"最新期号：{stats['last_issue']}")
    
    return saved_count


if __name__ == "__main__":
    main()
