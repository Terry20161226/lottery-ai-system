#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导入 2024 年双色球历史数据
从网页解析结果中提取并导入
"""

import re
import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from lottery_storage import LotteryStorage


def parse_ssq_from_lottost(html_content: str) -> list:
    """
    从黑龙江福彩网 HTML 解析双色球数据
    
    格式：2026-03-05| 2026024| 121321232914
    """
    results = []
    
    # 匹配表格行
    # 2026-03-05| 2026024| 121321232914| 370,443,834| 2| 79| 798
    pattern = r'(\d{4}-\d{2}-\d{2})\|?\s*(\d{7})\|?\s*(\d{12,13})'
    
    matches = re.findall(pattern, html_content)
    
    for match in matches:
        try:
            draw_date = match[0]
            issue = match[1]
            numbers_str = match[2]
            
            # 解析号码：前 12 位是红球 (6 个×2 位)，最后 1-2 位是蓝球
            if len(numbers_str) == 12:
                # 6 红 +1 蓝 (1 位)
                red_balls = sorted([int(numbers_str[i:i+2]) for i in range(0, 12, 2)])
                blue_ball = []
            elif len(numbers_str) == 13:
                # 6 红 +1 蓝 (2 位)
                red_balls = sorted([int(numbers_str[i:i+2]) for i in range(0, 12, 2)])
                blue_ball = [int(numbers_str[12:])]
            else:
                # 尝试其他格式
                red_balls = sorted([int(numbers_str[i:i+2]) for i in range(0, 12, 2)])
                blue_ball = []
            
            # 验证数据
            if len(red_balls) == 6 and all(1 <= n <= 33 for n in red_balls):
                results.append({
                    'issue': issue,
                    'draw_date': draw_date,
                    'numbers': {
                        'red': red_balls,
                        'blue': blue_ball if blue_ball else [int(numbers_str[-2:])]
                    }
                })
        except (ValueError, IndexError) as e:
            print(f"解析失败 {match}: {e}")
            continue
    
    return results


def main():
    """主函数"""
    print("=" * 70)
    print("📊 导入 2024 年双色球历史数据")
    print("=" * 70)
    
    # 从网页解析结果中提取（模拟从文件读取）
    html_content = """
    2026-03-05| 2026024| 121321232914
    2026-03-03| 2026023| 1381023296
    2026-03-01| 2026022| 15182325283211
    2026-02-26| 2026021| 313252630314
    2026-02-24| 2026020| 113142124302
    2026-02-12| 2026019| 78161718301
    2026-02-10| 2026018| 1115172225307
    2026-02-08| 2026017| 1351829324
    2026-02-05| 2026016| 45910273013
    2026-02-03| 2026015| 7101322273112
    2026-02-01| 2026014| 713192226321
    2026-01-29| 2026013| 49121316201
    2026-01-27| 2026012| 3571620248
    2026-01-25| 2026011| 2342031324
    2026-01-22| 2026010| 491015192612
    2026-01-20| 2026009| 361319232510
    2026-01-18| 2026008| 691627313310
    2026-01-15| 2026007| 913192729301
    2026-01-13| 2026006| 262223242815
    2026-01-11| 2026005| 1202227303310
    2026-01-08| 2026004| 3789183210
    2026-01-06| 2026003| 56921283016
    2026-01-04| 2026002| 1571830322
    2026-01-01| 2026001| 261112133315
    2025-12-30| 2025151| 89142228304
    2025-12-28| 2025150| 613171924318
    2025-12-25| 2025149| 1246223010
    2025-12-23| 2025148| 34910152216
    2025-12-21| 2025147| 135822338
    2025-12-18| 2025146| 57122426282
    """
    
    storage = LotteryStorage()
    
    # 解析数据
    results = parse_ssq_from_lottost(html_content)
    
    print(f"\n解析到 {len(results)} 期数据")
    
    # 批量导入
    if results:
        imported, skipped = storage.batch_save_lottery_results('ssq', results)
        print(f"  导入成功：{imported}期")
        print(f"  跳过重复：{skipped}期")
    
    # 最终统计
    ssq_count = len(storage.get_history('ssq', 2000))
    
    print("\n" + "=" * 70)
    print(f"✅ 当前双色球总数：{ssq_count}期")
    print("=" * 70)


if __name__ == "__main__":
    main()
