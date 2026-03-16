#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
彩票推荐号码生成器 - 三彩合一
支持：大乐透、双色球、福彩 3D
"""

from datetime import datetime


def main():
    """生成三彩推荐"""
    print("=" * 60)
    print("🎯 彩票推荐号码 - 三彩合一")
    print(f"【生成时间】{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 大乐透
    print("\n【大乐透推荐】")
    print("执行：python3 ensemble_voting_v2.py")
    print("-" * 60)
    
    # 双色球
    print("\n【双色球推荐】")
    print("执行：python3 ml_predictor.py")
    print("-" * 60)
    
    # 福彩 3D
    print("\n【福彩 3D 推荐】")
    print("执行：python3 fc3d_recommendation.py")
    print("-" * 60)
    
    print("\n" + "=" * 60)
    print("✅ 推荐完成（详细结果请查看各脚本输出）")


if __name__ == "__main__":
    main()
