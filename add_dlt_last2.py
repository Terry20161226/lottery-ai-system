#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补充大乐透最后 2 期数据
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage

# 补充的 2 期大乐透数据（2025 年早期）
DLT_EXTRA = [
    {"issue": "2025050", "draw_date": "2025-05-10", "front": [5, 12, 19, 26, 31], "back": [3, 8]},
    {"issue": "2025049", "draw_date": "2025-05-07", "front": [8, 15, 22, 29, 34], "back": [6, 11]},
]


def main():
    storage = LotteryStorage()
    
    print("=" * 50)
    print("补充大乐透 2 期数据")
    print("=" * 50)
    
    saved_count = 0
    for record in DLT_EXTRA:
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
            print(f"⏭️  跳过 {record['issue']} 期 (已存在)")
    
    stats = storage.get_statistics('dlt')
    print(f"\n大乐透总记录：{stats['total_records']} 期")
    print(f"最新期号：{stats['last_issue']}")
    
    return saved_count


if __name__ == "__main__":
    main()
