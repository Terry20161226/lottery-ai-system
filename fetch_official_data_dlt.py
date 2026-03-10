#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从福彩官网获取大乐透历史数据
URL: https://kaijiang.zhcw.com/zhcw/html/dlt/list.html
"""

import sys
import subprocess
import re
import time
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage


def browser_navigate(url: str) -> bool:
    """浏览器导航到 URL"""
    result = subprocess.Popen(
        ['openclaw', 'browser', 'navigate', url],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = result.communicate(timeout=60)
    return result.returncode == 0


def browser_snapshot() -> str:
    """获取浏览器快照"""
    result = subprocess.Popen(
        ['openclaw', 'browser', 'snapshot', '--format', 'aria'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = result.communicate(timeout=60)
    if result.returncode == 0:
        return stdout.decode('utf-8', errors='ignore')
    return ""


def parse_snapshot(snapshot: str) -> list:
    """解析快照中的开奖数据"""
    records = []
    lines = snapshot.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 查找期号（7 位数字）
        if re.match(r'^- cell "\d{7}"$', line):
            issue_match = re.search(r'"(\d{7})"', line)
            if issue_match:
                issue = issue_match.group(1)
                
                # 查找日期
                draw_date = None
                for j in range(max(0, i-5), i):
                    date_match = re.search(r'cell "(\d{4}-\d{2}-\d{2})"', lines[j])
                    if date_match:
                        draw_date = date_match.group(1)
                        break
                
                # 查找中奖号码（大乐透：5 前区 +2 后区）
                numbers = None
                for j in range(i, min(i+20, len(lines))):
                    # 大乐透格式：XX XX XX XX XX XX XX（5+2）
                    num_match = re.search(r'cell "(\d{2}) (\d{2}) (\d{2}) (\d{2}) (\d{2}) (\d{2}) (\d{2})"', lines[j])
                    if num_match:
                        nums = [int(num_match.group(k)) for k in range(1, 8)]
                        # 前 5 个是前区（1-35），后 2 个是后区（1-12）
                        front = sorted(nums[:5])
                        back = sorted([nums[5], nums[6]])
                        if all(1 <= f <= 35 for f in front) and all(1 <= b <= 12 for b in back):
                            numbers = {'front': front, 'back': back}
                        break
                
                if issue and numbers:
                    records.append({
                        'issue': issue,
                        'draw_date': draw_date,
                        'numbers': numbers
                    })
                
                i += 1
                continue
        i += 1
    
    return records


def fetch_all_pages():
    """获取所有大乐透历史数据"""
    import shutil
    
    storage = LotteryStorage()
    
    # 备份现有数据
    backup_path = Path('/root/.openclaw/workspace/lottery/data/dlt_history.json.bak')
    if storage.dlt_history_file.exists():
        shutil.copy2(storage.dlt_history_file, backup_path)
        print(f"已备份现有数据到：{backup_path}")
    
    base_url = "https://kaijiang.zhcw.com/zhcw/html/dlt/list_{}.html"
    
    all_records = []
    
    # 大乐透约 100+ 页
    for page in range(1, 150):
        if page == 1:
            url = "https://kaijiang.zhcw.com/zhcw/html/dlt/list.html"
        else:
            url = base_url.format(page)
        
        print(f"\n【第 {page}/150 页】{url}")
        
        # 导航到页面
        if not browser_navigate(url):
            print(f"  导航失败，跳过")
            break
        
        time.sleep(2)
        
        # 获取快照
        snapshot = browser_snapshot()
        if not snapshot:
            print(f"  快照获取失败，跳过")
            break
        
        # 解析数据
        records = parse_snapshot(snapshot)
        print(f"  解析到 {len(records)} 期数据")
        
        if not records:
            print(f"  无数据，可能已到最后一页")
            break
        
        all_records.extend(records)
        print(f"  累计收集 {len(all_records)} 期")
        
        # 避免请求过快
        time.sleep(1)
    
    # 一次性保存所有数据
    print(f"\n保存 {len(all_records)} 期数据到文件...")
    data = {
        'records': [],
        'total_records': 0,
        'last_update': datetime.now().isoformat()
    }
    
    existing_issues = set()
    for record in all_records:
        if record['issue'] in existing_issues:
            continue
        existing_issues.add(record['issue'])
        
        data['records'].append({
            'issue': record['issue'],
            'draw_date': record['draw_date'],
            'numbers': record['numbers'],
            'pool_amount': 0,
            'sales_amount': 0,
            'created_at': datetime.now().isoformat()
        })
    
    data['records'].sort(key=lambda x: x['issue'], reverse=True)
    data['total_records'] = len(data['records'])
    data['last_update'] = datetime.now().isoformat()
    
    with open(storage.dlt_history_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 保存完成：{len(data['records'])}期")
    
    return len(data['records']), 0


def main():
    print("=" * 70)
    print("📊 体彩官网大乐透历史数据获取")
    print("=" * 70)
    
    storage = LotteryStorage()
    before_count = len(storage.get_history('dlt', 2000))
    print(f"导入前：{before_count}期")
    
    imported, skipped = fetch_all_pages()
    
    after_count = len(storage.get_history('dlt', 2000))
    
    print("\n" + "=" * 70)
    print("✅ 数据获取完成！")
    print(f"本次导入：{imported}期")
    print(f"跳过重复：{skipped}期")
    print(f"当前总数：{after_count}期")
    print("=" * 70)


if __name__ == "__main__":
    main()
