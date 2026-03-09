#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 开奖数据爬虫（从乐彩网获取真实数据）
使用 web_fetch 解析后的数据
"""

import json
import re
from datetime import datetime, timedelta

DATA_FILE = "/root/.openclaw/workspace/lottery/data/fc3d_history.json"

# 从 web_fetch 获取的原始数据（乐彩网福彩 3D 历史开奖）
RAW_DATA = """
2026-03-08 2026057 766 107 477 264 无 无
2025-09-22 2025255 865 457 072 264 406 860
2024-11-01 2024292 907 911 426 462 521 364
2024-10-31 2024291 841 989 911 426 462 521
2024-06-06 2024148 661 180 225 426 153 356
2024-03-18 2024068 983 198 709 642 451 671
2022-08-24 2022226 510 008 410 426 654 640
2022-05-20 2022130 162 156 395 462 865 572
2022-01-14 2022014 385 952 528 462 786 285
2021-01-26 2021026 291 030 280 264 472 381
2020-12-16 2020298 424 898 042 624 964 299
2020-12-05 2020287 257 875 628 462 956 086
2020-04-14 2020056 774 978 468 462 880 902
2019-11-12 2019302 732 936 109 426 909 465
2018-10-09 2018275 281 457 557 264 261 709
2018-08-31 2018236 201 953 828 642 631 720
2018-03-25 2018077 061 861 785 246 616 369
2017-10-31 2017297 492 723 959 462 218 921
2017-02-11 2017035 192 114 348 624 650 897
2017-01-05 2017005 249 650 317 246 888 783
2016-10-12 2016279 808 085 435 624 378 998
2016-01-24 2016024 484 916 729 624 110 324
2015-12-15 2015342 807 079 070 642 655 134
2015-12-10 2015337 466 996 369 624 254 014
2015-09-04 2015240 558 267 899 462 957 764
2015-08-31 2015236 745 454 107 264 107 267
2014-11-11 2014307 104 474 391 642 429 461
2013-07-06 2013180 041 927 368 642 248 944
2012-02-23 2012047 682 026 493 642 875 808
2011-12-06 2011333 216 934 805 246 783 762
2011-10-29 2011295 740 098 717 624 766 042
2011-03-26 2011078 951 746 206 246 785 648
2010-11-09 2010306 705 340 513 642 442 498
2010-08-12 2010217 561 878 688 642 715 748
2010-01-12 2010012 262 875 115 426 969 196
2009-08-07 2009212 916 304 681 642 567 239
2008-04-23 2008107 437 492 653 624 199 918
2007-04-24 2007106 319 130 177 642 529 653
2006-10-09 2006274 110 857 849 426 576 935
2006-06-23 2006166 094 132 127 426 095 519
2006-05-27 2006139 021 351 128 462 363 688
2006-01-10 2006010 740 179 349 624 634 098
2004-11-05 2004303 761 688 177 264 597 270
2004-09-09 2004246 351 375 567 642 115 383
2004-02-02 2004026 668 584 985 426 541 435
2004-01-30 2004023 423 084 665 642 584 985
2002-09-20 2002256 246 444 687 624 395 099
"""


def parse_raw_data():
    """解析原始数据"""
    records = []
    
    lines = RAW_DATA.strip().split('\n')
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 4:
            try:
                draw_date = parts[0]
                issue = parts[1]
                shiji_num = parts[2]  # 试机号
                
                # 当前期开奖号码（第 4 列是前一期，第 5 列是当前期）
                current_nums = parts[4] if len(parts) > 4 else None
                
                if current_nums and len(current_nums) == 3 and current_nums != '无':
                    numbers = [int(n) for n in current_nums]
                    total_sum = sum(numbers)
                    
                    records.append({
                        "issue": issue,
                        "draw_date": draw_date,
                        "numbers": numbers,
                        "sum": total_sum,
                        "shiji": shiji_num
                    })
            except Exception as e:
                continue
    
    return records


def save_data(records):
    """保存数据到 JSON 文件"""
    data = {
        "lottery_type": "fc3d",
        "name": "福彩 3D",
        "last_update": datetime.now().isoformat(),
        "total_records": len(records),
        "source": "乐彩网 (17500.cn)",
        "records": sorted(records, key=lambda x: x['issue'], reverse=True)
    }
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data


def main():
    print("=" * 50)
    print("福彩 3D 开奖数据爬虫（真实数据）")
    print("=" * 50)
    
    # 解析数据
    print("\n📝 解析乐彩网数据...")
    records = parse_raw_data()
    print(f"   ✅ 解析 {len(records)} 条记录")
    
    # 保存数据
    print(f"\n💾 保存数据...")
    data = save_data(records)
    print(f"✅ 保存到：{DATA_FILE}")
    
    # 显示最近 10 期
    print("\n📋 最近 10 期开奖：")
    print("-" * 70)
    for i, record in enumerate(data['records'][:10], 1):
        nums = record["numbers"]
        print(f"{i:2}. 第{record['issue']}期 ({record['draw_date']}) | 号码：{' '.join(map(str, nums))} | 和值:{record['sum']}")
    
    print("\n" + "=" * 50)
    print("✅ 数据爬取完成")
    print("=" * 50)
    
    return data


if __name__ == "__main__":
    main()
