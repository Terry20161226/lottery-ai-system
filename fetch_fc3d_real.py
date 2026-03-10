#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
福彩 3D 开奖数据爬虫（从乐彩网获取真实数据）
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
import re

DATA_FILE = "/root/.openclaw/workspace/lottery/data/ks3_history.json"


def fetch_from_17500():
    """
    从乐彩网 (17500.cn) 爬取福彩 3D 历史开奖数据
    该网站提供完整的福彩 3D 开奖历史记录
    """
    records = []
    
    # 乐彩网福彩 3D 开奖列表页
    base_url = "https://www.17500.cn/widget/3d/qhgx.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.17500.cn/"
    }
    
    print("🕷️ 爬取乐彩网福彩 3D 数据...")
    
    try:
        response = requests.get(base_url, headers=headers, timeout=15)
        response.encoding = "utf-8"
        
        if response.status_code != 200:
            print(f"   ⚠️ 请求失败：{response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找表格数据
        table = soup.find('table')
        if not table:
            print("   ⚠️ 未找到数据表格")
            return []
        
        rows = table.find_all('tr')[1:]  # 跳过表头
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 4:
                try:
                    # 期号
                    issue = cells[0].get_text(strip=True)
                    
                    # 开奖号码（百位、十位、个位）
                    baiwei = int(cells[1].get_text(strip=True))
                    shiwei = int(cells[2].get_text(strip=True))
                    gewei = int(cells[3].get_text(strip=True))
                    
                    numbers = [baiwei, shiwei, gewei]
                    
                    # 计算和值
                    total_sum = sum(numbers)
                    
                    # 日期（从期号推断，2026057 = 2026 年第 057 期）
                    if len(issue) >= 6:
                        year = "20" + issue[:2]
                        day_of_year = int(issue[2:5])
                        from datetime import timedelta
                        base_date = datetime(int(year), 1, 1)
                        draw_date = (base_date + timedelta(days=day_of_year - 1)).strftime("%Y-%m-%d")
                    else:
                        draw_date = datetime.now().strftime("%Y-%m-%d")
                    
                    records.append({
                        "issue": issue,
                        "draw_date": draw_date,
                        "numbers": numbers,
                        "sum": total_sum
                    })
                except Exception as e:
                    continue
        
        print(f"   ✅ 获取 {len(records)} 条记录")
        
    except Exception as e:
        print(f"   ❌ 爬取失败：{e}")
    
    return records


def fetch_from_eastmoney():
    """
    从东方财富网爬取福彩 3D 数据
    """
    records = []
    
    url = "https://caipiao.eastmoney.com/pub/Result/History/fc3d?page=1"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    
    print("🕷️ 尝试东方财富网...")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 解析 HTML 表格
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.select('table tbody tr')
            
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    issue = cells[0].get_text(strip=True)
                    date = cells[1].get_text(strip=True)[:10]
                    nums_text = cells[2].get_text(strip=True)
                    numbers = [int(n) for n in re.findall(r'\d+', nums_text)[:3]]
                    
                    if len(numbers) == 3:
                        records.append({
                            "issue": issue,
                            "draw_date": date,
                            "numbers": numbers,
                            "sum": sum(numbers)
                        })
            
            print(f"   ✅ 获取 {len(records)} 条记录")
    except Exception as e:
        print(f"   ❌ 失败：{e}")
    
    return records


def save_data(records):
    """保存数据到 JSON 文件"""
    data = {
        "lottery_type": "ks3",
        "name": "福彩 3D",
        "last_update": datetime.now().isoformat(),
        "total_records": len(records),
        "source": "乐彩网/东方财富网",
        "records": sorted(records, key=lambda x: x['issue'], reverse=True)
    }
    
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return data


def main():
    print("=" * 50)
    print("福彩 3D 开奖数据爬虫（真实数据）")
    print("=" * 50)
    
    # 1. 尝试从乐彩网爬取
    records = fetch_from_17500()
    
    # 2. 如果失败，尝试东方财富网
    if not records:
        records = fetch_from_eastmoney()
    
    # 3. 保存数据
    if records:
        print(f"\n💾 保存 {len(records)} 条记录...")
        data = save_data(records)
        print(f"✅ 保存到：{DATA_FILE}")
        
        # 显示最近 10 期
        print("\n📋 最近 10 期开奖：")
        print("-" * 60)
        for i, record in enumerate(data['records'][:10], 1):
            nums = record["numbers"]
            print(f"{i:2}. 第{record['issue']}期 ({record['draw_date']}) | 号码：{' '.join(map(str, nums))} | 和值:{record['sum']}")
        
        print("\n" + "=" * 50)
        print("✅ 数据爬取完成")
        print("=" * 50)
    else:
        print("\n❌ 所有数据源都失败")
        print("💡 建议：手动导入数据或使用模拟数据")
    
    return records


if __name__ == "__main__":
    main()
