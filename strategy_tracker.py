#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票策略效果追踪与分析
记录每次开奖后各策略的表现，生成统计报告
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# 配置
LOTTERY_DIR = "/root/.openclaw/workspace/lottery"
DATA_DIR = os.path.join(LOTTERY_DIR, "data")
STATS_DIR = os.path.join(LOTTERY_DIR, "stats")
FEEDBACK_DIR = os.path.join(LOTTERY_DIR, "feedback")

# 策略名称映射
STRATEGY_NAMES = {
    "hot": "热号追踪",
    "balanced": "均衡策略",
    "warm": "温号搭配",
    "consecutive": "连号追踪",
    "odd_even": "奇偶均衡",
    "zone": "区间分布",
    "cold": "冷号反弹"
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

def get_strategy_stats_file(lottery_type):
    """获取策略统计文件路径"""
    return os.path.join(STATS_DIR, f"{lottery_type}_strategy_stats.json")

def init_strategy_stats(lottery_type):
    """初始化策略统计数据结构"""
    return {
        "lottery_type": lottery_type,
        "last_update": datetime.now().isoformat(),
        "total_draws": 0,
        "strategies": {}
    }

def record_strategy_result(lottery_type, issue, draw_date, recommendations, prize_results):
    """记录某期开奖的策略结果"""
    stats_file = get_strategy_stats_file(lottery_type)
    
    # 加载或初始化统计
    if os.path.exists(stats_file):
        stats = load_json_file(stats_file)
        # 确保有 strategies 键
        if "strategies" not in stats:
            stats["strategies"] = {}
    else:
        stats = init_strategy_stats(lottery_type)
    
    # 更新统计时间
    stats["last_update"] = datetime.now().isoformat()
    stats["total_draws"] = stats.get("total_draws", 0) + 1
    
    # 记录本期各策略表现
    for i, rec in enumerate(recommendations):
        strategy = rec.get("strategy", "unknown")
        prize_result = prize_results[i] if i < len(prize_results) else {"prize_name": None, "prize_amount": 0}
        
        if strategy not in stats["strategies"]:
            stats["strategies"][strategy] = {
                "name": STRATEGY_NAMES.get(strategy, strategy),
                "total_notes": 0,
                "win_notes": 0,
                "total_amount": 0,
                "win_rate": 0,
                "roi": 0,
                "history": []  # 历史记录
            }
        
        strat = stats["strategies"][strategy]
        strat["total_notes"] += 1
        
        # 如果中奖
        if prize_result.get("prize_name"):
            strat["win_notes"] += 1
            strat["total_amount"] += prize_result.get("prize_amount", 0)
            
            # 记录中奖历史
            strat["history"].append({
                "issue": issue,
                "draw_date": draw_date,
                "prize_name": prize_result["prize_name"],
                "prize_amount": prize_result["prize_amount"]
            })
        
        # 更新胜率
        strat["win_rate"] = round(strat["win_notes"] / strat["total_notes"] * 100, 2) if strat["total_notes"] > 0 else 0
        
        # 计算 ROI（假设每注 2 元）
        cost = strat["total_notes"] * 2
        strat["roi"] = round((strat["total_amount"] - cost) / cost * 100, 2) if cost > 0 else 0
    
    # 保存统计
    save_json_file(stats_file, stats)
    return stats

def generate_strategy_report(lottery_type, limit_draws=50):
    """生成策略分析报告"""
    stats_file = get_strategy_stats_file(lottery_type)
    
    if not os.path.exists(stats_file):
        return f"⏳ 暂无 {lottery_type} 策略统计数据"
    
    stats = load_json_file(stats_file)
    
    report = []
    lottery_name = "双色球" if lottery_type == "ssq" else "大乐透"
    
    report.append(f"📊 {lottery_name} 策略效果分析")
    report.append("=" * 50)
    report.append(f"统计期数：{stats.get('total_draws', 0)} 期")
    report.append(f"更新时间：{stats.get('last_update', '未知')[:10]}")
    report.append("")
    
    # 按 ROI 排序策略
    strategies = stats.get("strategies", {})
    if not strategies:
        return "📭 暂无策略数据"
    
    sorted_strategies = sorted(
        strategies.items(),
        key=lambda x: x[1].get("roi", 0),
        reverse=True
    )
    
    report.append("🏆 策略排行榜（按 ROI）")
    report.append("-" * 50)
    
    for rank, (strategy_id, data) in enumerate(sorted_strategies, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
        
        report.append(f"\n{medal} {data.get('name', strategy_id)}")
        report.append(f"   投注注数：{data.get('total_notes', 0)}")
        report.append(f"   中奖注数：{data.get('win_notes', 0)}")
        report.append(f"   胜率：{data.get('win_rate', 0)}%")
        report.append(f"   总奖金：¥{data.get('total_amount', 0):,}")
        report.append(f"   ROI：{data.get('roi', 0)}%")
        
        # 显示最近中奖记录
        history = data.get("history", [])[-3:]
        if history:
            report.append(f"   最近中奖:")
            for h in history:
                report.append(f"     - {h.get('issue', '?')}期 {h.get('prize_name', '?')} ¥{h.get('prize_amount', 0):,}")
    
    report.append("")
    report.append("=" * 50)
    
    # 推荐最佳策略
    if sorted_strategies:
        best = sorted_strategies[0]
        report.append(f"\n💡 推荐策略：{best[1].get('name', '未知')}")
        report.append(f"   理由：ROI {best[1].get('roi', 0)}%，胜率 {best[1].get('win_rate', 0)}%")
    
    report.append("")
    report.append("⚠️ 历史表现不代表未来，请理性参考")
    
    return "\n".join(report)

def get_recent_recommendations(lottery_type):
    """获取最近推荐数据（包含策略信息）"""
    filepath = os.path.join(DATA_DIR, f"{lottery_type}_recommend.json")
    data = load_json_file(filepath)
    if data and "recommendations" in data:
        return data["recommendations"]
    return []

def main():
    print("📊 彩票策略效果追踪")
    print("=" * 50)
    
    # 获取最近推荐
    print("📖 读取推荐数据...")
    ssq_recs = get_recent_recommendations("ssq")
    dlt_recs = get_recent_recommendations("dlt")
    
    print(f"   双色球推荐：{len(ssq_recs)} 注")
    print(f"   大乐透推荐：{len(dlt_recs)} 注")
    
    # 获取开奖结果（从之前的核对结果）
    result_file = os.path.join(FEEDBACK_DIR, "prize_check_result.json")
    result_data = load_json_file(result_file)
    
    if not result_data:
        print("⏳ 暂无核对结果，无法记录策略表现")
        return
    
    # 记录双色球策略结果
    if result_data.get("ssq", {}).get("draw"):
        ssq_draw = result_data["ssq"]["draw"]
        ssq_results = result_data["ssq"]["results"]
        
        # 构建 prize_results 格式
        prize_results = []
        for i in range(len(ssq_recs)):
            matched = [r for r in ssq_results if r["note"] == i + 1]
            if matched:
                prize_results.append({
                    "prize_name": matched[0]["prize_name"],
                    "prize_amount": matched[0]["prize_amount"]
                })
            else:
                prize_results.append({"prize_name": None, "prize_amount": 0})
        
        print("📝 记录双色球策略结果...")
        record_strategy_result(
            "ssq",
            ssq_draw.get("issue", "未知"),
            ssq_draw.get("draw_date", ""),
            ssq_recs,
            prize_results
        )
        print("   ✅ 已记录")
    
    # 记录大乐透策略结果
    if result_data.get("dlt", {}).get("draw"):
        dlt_draw = result_data["dlt"]["draw"]
        dlt_results = result_data["dlt"]["results"]
        
        prize_results = []
        for i in range(len(dlt_recs)):
            matched = [r for r in dlt_results if r["note"] == i + 1]
            if matched:
                prize_results.append({
                    "prize_name": matched[0]["prize_name"],
                    "prize_amount": matched[0]["prize_amount"]
                })
            else:
                prize_results.append({"prize_name": None, "prize_amount": 0})
        
        print("📝 记录大乐透策略结果...")
        record_strategy_result(
            "dlt",
            dlt_draw.get("issue", "未知"),
            dlt_draw.get("draw_date", ""),
            dlt_recs,
            prize_results
        )
        print("   ✅ 已记录")
    
    # 生成报告
    print("\n" + "=" * 50)
    print("📈 双色球策略分析")
    print("-" * 50)
    ssq_report = generate_strategy_report("ssq")
    print(ssq_report)
    
    print("\n" + "=" * 50)
    print("📈 大乐透策略分析")
    print("-" * 50)
    dlt_report = generate_strategy_report("dlt")
    print(dlt_report)
    
    # 保存完整报告
    report_file = os.path.join(STATS_DIR, "strategy_analysis_report.txt")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"生成时间：{datetime.now().isoformat()}\n\n")
        f.write(ssq_report + "\n\n")
        f.write(dlt_report)
    
    print(f"\n💾 报告已保存到：{report_file}")

if __name__ == "__main__":
    main()


class StrategyTracker:
    """策略追踪器类 - 兼容旧代码的包装类"""
    
    def __init__(self):
        pass
    
    def get_summary(self, lottery_type: str):
        """获取策略统计摘要"""
        stats_file = get_strategy_stats_file(lottery_type)
        data = load_json_file(stats_file)
        if not data:
            data = init_strategy_stats(lottery_type)
        return data
    
    def get_best_strategy(self, lottery_type: str):
        """获取最佳策略信息（返回 dict）"""
        stats = self.get_summary(lottery_type)
        if stats and 'strategy_stats' in stats:
            best_name, best_data = max(stats['strategy_stats'].items(), 
                      key=lambda x: x[1].get('hit_rate', 0),
                      default=('balanced', {}))
            return {
                'name_cn': STRATEGY_NAMES.get(best_name, best_name),
                'total_prize': best_data.get('total_prize', 0)
            }
        return {'name_cn': '均衡策略', 'total_prize': 0}
    
    def save_recommendations(self, lottery_type: str, issue: str, recommendations: dict):
        """保存推荐结果"""
        filepath = os.path.join(DATA_DIR, f"{lottery_type}_recommend.json")
        data = {
            "issue": issue,
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations
        }
        save_json_file(filepath, data)
