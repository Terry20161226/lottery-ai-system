#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入快三历史开奖数据（模拟数据）
"""

import json
import random
from datetime import datetime, timedelta

# 配置
DATA_FILE = "/root/.openclaw/workspace/lottery/data/ks3_history.json"


def generate_ks3_draw(issue, draw_date):
    """生成一期快三开奖数据"""
    numbers = [random.randint(1, 6) for _ in range(3)]
    return {
        "issue": issue,
        "draw_date": draw_date,
        "numbers": numbers,
        "sum": sum(numbers)
    }


def main():
    print("=" * 50)
    print("导入快三历史数据")
    print("=" * 50)
    
    # 生成最近 100 期模拟数据
    records = []
    start_date = datetime(2026, 1, 1)
    
    print(f"\n📝 生成最近 100 期模拟数据...")
    
    for i in range(100):
        # 期号格式：年份 + 序号
        issue = f"2026{i+1:03d}"
        # 每天约 84 期（每 10 分钟一期）
        days_offset = i // 84
        draw_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        record = generate_ks3_draw(issue, draw_date)
        records.append(record)
    
    # 保存到文件
    data = {
        "lottery_type": "ks3",
        "name": "快三",
        "last_update": datetime.now().isoformat(),
        "total_records": len(records),
        "records": records
    }
    
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 已生成 {len(records)} 期历史数据")
    print(f"💾 保存到：{DATA_FILE}")
    
    # 显示最近 5 期
    print("\n📋 最近 5 期开奖：")
    print("-" * 50)
    for i, record in enumerate(records[:5], 1):
        nums = record["numbers"]
        print(f"{i}. 第{record['issue']}期 ({record['draw_date']})")
        print(f"   开奖号码：{' '.join(map(str, nums))} (和值:{record['sum']})")
    
    print("\n" + "=" * 50)
    print("✅ 数据导入完成")
    print("=" * 50)


if __name__ == "__main__":
    main()
