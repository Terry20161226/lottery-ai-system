#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票中奖自动计算脚本
根据开奖号码和推荐号码，计算中奖金额并通知
"""

import os
import json
from datetime import datetime
from pathlib import Path
from collections import Counter

# 配置
LOTTERY_DIR = "/root/.openclaw/workspace/lottery"
DATA_DIR = os.path.join(LOTTERY_DIR, "data")
FEEDBACK_DIR = os.path.join(LOTTERY_DIR, "feedback")

# 奖级规则
SSQ_PRIZES = {
    "一等奖": {"match": 6, "blue": True, "amount": 5000000},
    "二等奖": {"match": 6, "blue": False, "amount": 100000},
    "三等奖": {"match": 5, "blue": True, "amount": 3000},
    "四等奖": {"match": 5, "blue": False, "amount": 200},
    "四等奖_2": {"match": 4, "blue": True, "amount": 200},
    "五等奖": {"match": 4, "blue": False, "amount": 10},
    "五等奖_2": {"match": 3, "blue": True, "amount": 10},
    "六等奖": {"match": 2, "blue": True, "amount": 5},
    "六等奖_2": {"match": 1, "blue": True, "amount": 5},
    "六等奖_3": {"match": 0, "blue": True, "amount": 5},
}

DLT_PRIZES = {
    "一等奖": {"match": 5, "blue": 2, "amount": 5000000},
    "二等奖": {"match": 5, "blue": 1, "amount": 100000},
    "三等奖": {"match": 5, "blue": 0, "amount": 10000},
    "四等奖": {"match": 4, "blue": 2, "amount": 3000},
    "五等奖": {"match": 4, "blue": 1, "amount": 300},
    "六等奖": {"match": 3, "blue": 2, "amount": 200},
    "七等奖": {"match": 4, "blue": 0, "amount": 100},
    "八等奖": {"match": 3, "blue": 1, "amount": 15},
    "八等奖_2": {"match": 2, "blue": 2, "amount": 15},
    "九等奖": {"match": 3, "blue": 0, "amount": 5},
    "九等奖_2": {"match": 1, "blue": 2, "amount": 5},
    "九等奖_3": {"match": 2, "blue": 1, "amount": 5},
    "九等奖_4": {"match": 0, "blue": 2, "amount": 5},
}

# 福彩 3D 奖级规则
FC3D_PRIZES = {
    "直选": {"amount": 1040},
    "组三": {"amount": 346},
    "组六": {"amount": 173},
}

def load_json_file(filepath):
    """加载 JSON 文件"""
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_json_file(filepath, data):
    """保存 JSON 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_latest_draw(lottery_type):
    """获取最新开奖号码"""
    if lottery_type == "ssq":
        filepath = os.path.join(DATA_DIR, "ssq_history.json")
        data = load_json_file(filepath)
        if data and "records" in data and len(data["records"]) > 0:
            record = data["records"][0]
            return {
                "issue": record.get("issue"),
                "draw_date": record.get("draw_date"),
                "red_balls": record.get("numbers", {}).get("red", []),
                "blue_ball": record.get("numbers", {}).get("blue", [])[0] if record.get("numbers", {}).get("blue") else None
            }
    elif lottery_type == "dlt":
        filepath = os.path.join(DATA_DIR, "dlt_history.json")
        data = load_json_file(filepath)
        if data and "records" in data and len(data["records"]) > 0:
            record = data["records"][0]
            nums = record.get("numbers", {})
            front_balls = nums.get("front", nums.get("red", []))
            back_balls = nums.get("back", nums.get("blue", []))
            return {
                "issue": record.get("issue"),
                "draw_date": record.get("draw_date"),
                "front_balls": front_balls,
                "back_balls": back_balls
            }
    elif lottery_type == "fc3d":
        filepath = os.path.join(DATA_DIR, "fc3d_history.json")
        data = load_json_file(filepath)
        if data and "records" in data and len(data["records"]) > 0:
            record = data["records"][0]
            numbers = record.get("numbers", [])
            return {
                "issue": record.get("issue"),
                "draw_date": record.get("draw_date"),
                "numbers": numbers,
                "sum": sum(numbers)
            }
    return None

def get_latest_recommendations(lottery_type):
    """获取最新推荐号码"""
    filepath = os.path.join(DATA_DIR, f"{lottery_type}_recommend.json")
    
    data = load_json_file(filepath)
    if data and "recommendations" in data:
        recs = []
        for rec in data["recommendations"]:
            if lottery_type == "ssq":
                numbers = rec.get("numbers", [])
                for num in numbers:
                    recs.append({
                        "red_balls": num.get("red", []),
                        "blue_ball": num.get("blue", [])[0] if num.get("blue") else None
                    })
            elif lottery_type == "dlt":
                numbers = rec.get("numbers", [])
                for num in numbers:
                    # 大乐透数据格式：front/back 或 red/blue 都支持
                    front_balls = num.get("front", num.get("red", []))
                    back_balls = num.get("back", num.get("blue", []))
                    recs.append({
                        "front_balls": front_balls,
                        "back_balls": back_balls
                    })
            elif lottery_type == "fc3d":
                recs.append({
                    "numbers": rec.get("numbers", []),
                    "sum": rec.get("sum"),
                    "type": "直选",
                    "pattern": rec.get("pattern")
                })
        return recs[:5]
    return []

def calculate_ssq_prize(red_balls, blue_ball, recommendation):
    """计算双色球中奖"""
    rec_reds = set(recommendation.get("red_balls", []))
    rec_blue = recommendation.get("blue_ball")
    
    if not rec_reds or not rec_blue:
        return None, 0
    
    # 计算匹配的红球数量
    match_red = len(set(red_balls) & rec_reds)
    match_blue = (blue_ball == rec_blue)
    
    prize_name = None
    prize_amount = 0
    
    for name, rule in SSQ_PRIZES.items():
        if match_red == rule["match"] and match_blue == rule["blue"]:
            prize_name = name
            prize_amount = rule["amount"]
            break
    
    return prize_name, prize_amount

def calculate_dlt_prize(front_balls, back_balls, recommendation):
    """计算大乐透中奖"""
    rec_fronts = set(recommendation.get("front_balls", []))
    rec_backs = set(recommendation.get("back_balls", []))
    
    if not rec_fronts or not rec_backs:
        return None, 0
    
    match_front = len(set(front_balls) & rec_fronts)
    match_back = len(set(back_balls) & rec_backs)
    
    prize_name = None
    prize_amount = 0
    
    for name, rule in DLT_PRIZES.items():
        if match_front == rule["match"] and match_back == rule["blue"]:
            prize_name = name
            prize_amount = rule["amount"]
            break
    
    return prize_name, prize_amount


def analyze_fc3d_pattern(numbers):
    """分析福彩 3D 号码形态"""
    counter = Counter(numbers)
    values = list(counter.values())
    
    if len(counter) == 1:
        return "豹子"
    elif len(counter) == 2:
        return "组三"
    elif len(counter) == 3:
        return "组六"
    return "未知"


def calculate_fc3d_prize(draw_data, recommendation):
    """计算福彩 3D 中奖"""
    draw_numbers = draw_data.get("numbers", [])
    draw_sum = sum(draw_numbers)
    draw_pattern = analyze_fc3d_pattern(draw_numbers)
    
    bet_type = recommendation.get("type", "直选")
    bet_numbers = recommendation.get("numbers", [])
    bet_sum = recommendation.get("sum")
    
    prize_name = None
    prize_amount = 0
    
    # 直选：号码和顺序完全匹配
    if bet_type == "直选":
        if bet_numbers == draw_numbers:
            prize_name = "直选"
            prize_amount = 1040
    
    # 组选：号码匹配但顺序不限
    elif bet_type == "组选":
        if Counter(bet_numbers) == Counter(draw_numbers):
            if draw_pattern == "组三":
                prize_name = "组三"
                prize_amount = 346
            elif draw_pattern == "组六":
                prize_name = "组六"
                prize_amount = 173
    
    # 和值投注
    elif bet_type == "和值":
        if bet_sum == draw_sum:
            prize_name = f"和值 {bet_sum}"
            prize_amount = 0  # 和值奖金根据具体和值而定
    
    return prize_name, prize_amount

def check_lottery_prize(lottery_type, draw_data, recommendations):
    """检查某彩票类型的中奖情况"""
    results = []
    total_amount = 0
    
    if lottery_type == "ssq":
        red_balls = draw_data.get("red_balls", [])
        blue_ball = draw_data.get("blue_ball")
        
        for i, rec in enumerate(recommendations, 1):
            prize_name, prize_amount = calculate_ssq_prize(red_balls, blue_ball, rec)
            if prize_name:
                results.append({
                    "note": i,
                    "prize_name": prize_name,
                    "prize_amount": prize_amount,
                    "recommendation": rec
                })
                total_amount += prize_amount
    
    elif lottery_type == "dlt":
        front_balls = draw_data.get("front_balls", [])
        back_balls = draw_data.get("back_balls", [])
        
        for i, rec in enumerate(recommendations, 1):
            prize_name, prize_amount = calculate_dlt_prize(front_balls, back_balls, rec)
            if prize_name:
                results.append({
                    "note": i,
                    "prize_name": prize_name,
                    "prize_amount": prize_amount,
                    "recommendation": rec
                })
                total_amount += prize_amount
    
    elif lottery_type == "fc3d":
        for i, rec in enumerate(recommendations, 1):
            prize_name, prize_amount = calculate_fc3d_prize(draw_data, rec)
            if prize_name:
                results.append({
                    "note": i,
                    "prize_name": prize_name,
                    "prize_amount": prize_amount,
                    "recommendation": rec
                })
                total_amount += prize_amount
    
    return results, total_amount

def format_report(ssq_results, dlt_results, fc3d_results, ssq_draw, dlt_draw, fc3d_draw):
    """格式化中奖报告"""
    report = []
    report.append("🎉 彩票中奖核对报告")
    report.append("=" * 50)
    report.append("")
    
    # 双色球部分
    report.append("🔴 双色球")
    if ssq_draw:
        report.append(f"期号：{ssq_draw.get('issue', '未知')}")
        reds = ssq_draw.get("red_balls", [])
        blue = ssq_draw.get("blue_ball")
        report.append(f"开奖号码：红球 {' '.join(map(str, reds))} + 蓝球 {blue}")
        report.append("")
        
        if ssq_results:
            report.append("✅ 中奖详情：")
            for r in ssq_results:
                report.append(f"  第{r['note']}注：{r['prize_name']} - ¥{r['prize_amount']:,}")
            report.append("")
            report.append(f"💰 双色球总奖金：¥{sum(r['prize_amount'] for r in ssq_results):,}")
        else:
            report.append("❌ 未中奖")
    else:
        report.append("⏳ 暂无开奖数据")
    
    report.append("")
    report.append("-" * 50)
    report.append("")
    
    # 大乐透部分
    report.append("🔵 大乐透")
    if dlt_draw:
        report.append(f"期号：{dlt_draw.get('issue', '未知')}")
        fronts = dlt_draw.get("front_balls", [])
        backs = dlt_draw.get("back_balls", [])
        report.append(f"开奖号码：前区 {' '.join(map(str, fronts))} + 后区 {' '.join(map(str, backs))}")
        report.append("")
        
        if dlt_results:
            report.append("✅ 中奖详情：")
            for r in dlt_results:
                report.append(f"  第{r['note']}注：{r['prize_name']} - ¥{r['prize_amount']:,}")
            report.append("")
            report.append(f"💰 大乐透总奖金：¥{sum(r['prize_amount'] for r in dlt_results):,}")
        else:
            report.append("❌ 未中奖")
    else:
        report.append("⏳ 暂无开奖数据")
    
    report.append("")
    report.append("-" * 50)
    report.append("")
    
    # 福彩 3D 部分
    report.append("🎲 福彩 3D")
    if fc3d_draw:
        report.append(f"期号：{fc3d_draw.get('issue', '未知')}")
        nums = fc3d_draw.get("numbers", [])
        report.append(f"开奖号码：{' '.join(map(str, nums))} (和值:{fc3d_draw.get('sum')})")
        report.append("")
        
        if fc3d_results:
            report.append("✅ 中奖详情：")
            for r in fc3d_results:
                report.append(f"  第{r['note']}注：{r['prize_name']} - ¥{r['prize_amount']:,}")
            report.append("")
            report.append(f"💰 福彩 3D 总奖金：¥{sum(r['prize_amount'] for r in fc3d_results):,}")
        else:
            report.append("❌ 未中奖")
    else:
        report.append("⏳ 暂无开奖数据")
    
    report.append("")
    report.append("=" * 50)
    
    # 总计
    total = (sum(r['prize_amount'] for r in ssq_results) + 
             sum(r['prize_amount'] for r in dlt_results) + 
             sum(r['prize_amount'] for r in fc3d_results))
    if total > 0:
        report.append(f"🎊 本期总奖金：¥{total:,}")
        report.append("")
        report.append("🎉 恭喜中奖！请记得兑奖哦～")
    else:
        report.append("😅 本期未中奖，继续加油！")
    
    report.append("")
    report.append("⚠️ 彩票有风险，购买需谨慎")
    
    return "\n".join(report)

def main():
    print("🎉 彩票中奖自动核对")
    print("=" * 50)
    
    # 获取开奖数据
    print("📖 读取开奖数据...")
    ssq_draw = get_latest_draw("ssq")
    dlt_draw = get_latest_draw("dlt")
    fc3d_draw = get_latest_draw("fc3d")
    
    if ssq_draw:
        print(f"   双色球最新期：{ssq_draw.get('issue', '未知')}")
    if dlt_draw:
        print(f"   大乐透最新期：{dlt_draw.get('issue', '未知')}")
    if fc3d_draw:
        print(f"   福彩 3D 最新期：{fc3d_draw.get('issue', '未知')}")
    
    # 获取推荐数据
    print("📖 读取推荐数据...")
    ssq_recs = get_latest_recommendations("ssq")
    dlt_recs = get_latest_recommendations("dlt")
    fc3d_recs = get_latest_recommendations("fc3d")
    
    print(f"   双色球推荐：{len(ssq_recs)} 注")
    print(f"   大乐透推荐：{len(dlt_recs)} 注")
    print(f"   福彩 3D 推荐：{len(fc3d_recs)} 注")
    
    # 计算中奖
    print("🔍 计算中奖情况...")
    ssq_results, ssq_total = check_lottery_prize("ssq", ssq_draw, ssq_recs) if ssq_draw and ssq_recs else ([], 0)
    dlt_results, dlt_total = check_lottery_prize("dlt", dlt_draw, dlt_recs) if dlt_draw and dlt_recs else ([], 0)
    fc3d_results, fc3d_total = check_lottery_prize("fc3d", fc3d_draw, fc3d_recs) if fc3d_draw and fc3d_recs else ([], 0)
    
    print(f"   双色球中奖：{len(ssq_results)} 注，¥{ssq_total:,}")
    print(f"   大乐透中奖：{len(dlt_results)} 注，¥{dlt_total:,}")
    print(f"   福彩 3D 中奖：{len(fc3d_results)} 注，¥{fc3d_total:,}")
    
    # 生成报告
    report = format_report(ssq_results, dlt_results, fc3d_results, ssq_draw, dlt_draw, fc3d_draw)
    
    # 保存结果
    result_data = {
        "timestamp": datetime.now().isoformat(),
        "ssq": {
            "draw": ssq_draw,
            "results": ssq_results,
            "total": ssq_total
        },
        "dlt": {
            "draw": dlt_draw,
            "results": dlt_results,
            "total": dlt_total
        },
        "fc3d": {
            "draw": fc3d_draw,
            "results": fc3d_results,
            "total": fc3d_total
        },
        "grand_total": ssq_total + dlt_total + fc3d_total
    }
    
    result_file = os.path.join(FEEDBACK_DIR, "prize_check_result.json")
    save_json_file(result_file, result_data)
    print(f"\n💾 结果已保存到：{result_file}")
    
    # 输出报告
    print("\n" + report)
    
    # 调用策略追踪
    print("\n" + "=" * 50)
    print("📊 更新策略统计...")
    try:
        import subprocess
        result = subprocess.run(
            ["python3", os.path.join(LOTTERY_DIR, "strategy_tracker.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30
        )
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ 警告：{result.stderr}")
    except Exception as e:
        print(f"⚠️ 策略追踪失败：{e}")
    
    return report

if __name__ == "__main__":
    main()
