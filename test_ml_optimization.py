#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试机器学习优化效果
对比：简单线性回归 vs 岭回归 vs 集成模型
"""

import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')

from ml_predictor import MLPredictor


def main():
    print("=" * 70)
    print("🧪 机器学习优化效果测试")
    print("=" * 70)
    
    predictor = MLPredictor()
    
    # 双色球
    print("\n【双色球】")
    X, y, features = predictor.prepare_features('ssq', 150)
    
    if X:
        print(f"训练数据：{len(X)} 样本，{len(features)} 特征")
        
        # 1. 简单线性回归
        print("\n1️⃣ 简单线性回归：")
        predictor.train_simple_regression(X, y)
        
        # 2. 岭回归（不同 alpha 值）
        print("\n2️⃣ 岭回归：")
        for alpha in [0.1, 0.5, 1.0, 2.0]:
            predictor.train_ridge_regression(X, y, alpha)
        
        # 3. 交叉验证
        print("\n3️⃣ 交叉验证：")
        predictor.cross_validate(X, y, k=5, alpha=1.0)
        
        # 4. 集成模型
        print("\n4️⃣ 集成模型：")
        predictor.train_ensemble(X, y)
        
        # 测试预测
        print("\n【预测测试】")
        history = predictor.storage.get_history('ssq', 10)
        result = predictor.predict(history, 'ssq')
        if 'error' not in result:
            print(f"预测下期和值：{result['predicted_sum']} ± {result['confidence']*20}")
            print(f"置信度：{result['confidence']:.2f}")
    
    # 大乐透
    print("\n" + "=" * 70)
    print("\n【大乐透】")
    X, y, features = predictor.prepare_features('dlt', 150)
    
    if X:
        print(f"训练数据：{len(X)} 样本，{len(features)} 特征")
        
        # 1. 简单线性回归
        print("\n1️⃣ 简单线性回归：")
        predictor.train_simple_regression(X, y)
        
        # 2. 岭回归
        print("\n2️⃣ 岭回归：")
        for alpha in [0.1, 0.5, 1.0, 2.0]:
            predictor.train_ridge_regression(X, y, alpha)
        
        # 3. 交叉验证
        print("\n3️⃣ 交叉验证：")
        predictor.cross_validate(X, y, k=5, alpha=1.0)
        
        # 4. 集成模型
        print("\n4️⃣ 集成模型：")
        predictor.train_ensemble(X, y)
        
        # 测试预测
        print("\n【预测测试】")
        history = predictor.storage.get_history('dlt', 10)
        result = predictor.predict(history, 'dlt')
        if 'error' not in result:
            print(f"预测下期和值：{result['predicted_sum']} ± {result['confidence']*15}")
            print(f"置信度：{result['confidence']:.2f}")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！")
    print("=" * 70)


if __name__ == "__main__":
    main()
