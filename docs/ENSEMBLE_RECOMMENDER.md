# 多策略集成推荐系统

## 🎯 功能概述

集成 4 种彩票预测策略，通过加权投票机制生成最终推荐号码。

**支持的彩种：**
- 大乐透（DLT）
- 双色球（SSQ）

---

## 📊 策略组成

| 策略 | 权重 | 原理 | 特点 |
|------|------|------|------|
| **ML 加权** | 40% | 机器学习模型预测 | 捕捉复杂模式 |
| **热号追踪** | 25% | 选择近期高频号码 | 跟随趋势 |
| **冷号反弹** | 20% | 选择遗漏久的号码 | 博反弹 |
| **均衡策略** | 15% | 冷热号混合 | 平衡风险 |

---

## 🔧 工作原理

### 1. 各策略独立推荐
每个策略生成 5 注推荐号码

### 2. 加权投票统计
根据权重统计每个号码的出现频率：
```
号码频率 = Σ(策略权重 × 该策略推荐此号码的次数)
```

### 3. 生成最终推荐
从频率最高的号码池中随机组合生成 5 注最终推荐

---

## 📁 文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| 主脚本 | `lottery/ensemble_recommender.py` | 集成推荐生成器 |
| 大乐透推荐 | `lottery/data/dlt_recommend.json` | 大乐透推荐结果 |
| 双色球推荐 | `lottery/data/ssq_recommend.json` | 双色球推荐结果 |
| 日志 | `lottery/logs/ensemble_recommend.log` | 运行日志 |

---

## ⏰ 定时任务

**执行时间：** 每天 22:15（开奖前优化推荐）

**Crontab 配置：**
```bash
15 22 * * * cd /root/.openclaw/workspace/lottery && python3 ensemble_recommender.py >> /root/.openclaw/workspace/lottery/logs/ensemble_recommend.log 2>&1
```

---

## 🚀 手动运行

```bash
cd /root/.openclaw/workspace/lottery
python3 ensemble_recommender.py
```

**输出示例：**
```
============================================================
🎯 多策略集成推荐系统
============================================================

【大乐透集成推荐】
============================================================
🤖 多策略集成推荐 - DLT
【时间】2026-03-16 11:12
============================================================

📖 加载历史数据：24 期

📊 策略权重配置:
   ml_weighted: 40%
   hot_tracking: 25%
   cold_rebound: 20%
   balanced: 15%

🎯 生成集成推荐...
✅ 模型已加载：2026-03-11T11:35:25.095108

📊 各策略推荐数量:
   ml: 5 注
   hot: 5 注
   cold: 5 注
   balanced: 5 注

✅ 生成 5 注推荐:
   第1注：前区 02 05 23 26 31 + 后区 05 09
   第2注：前区 03 15 16 34 35 + 后区 01 10
   ...

💾 推荐已保存：/root/.openclaw/workspace/lottery/data/dlt_recommend.json
```

---

## 📈 推荐数据格式

```json
{
  "recommendations": [
    {
      "id": "ensemble_20260316_111252",
      "issue": "2026025",
      "created_at": "2026-03-16T11:12:52.699104",
      "strategy": "ensemble_voting",
      "method": "weighted_frequency_voting",
      "weights": {
        "ml_weighted": 0.40,
        "hot_tracking": 0.25,
        "cold_rebound": 0.20,
        "balanced": 0.15
      },
      "numbers": [
        {
          "front": [2, 5, 23, 26, 31],
          "back": [5, 9]
        },
        ...
      ]
    }
  ]
}
```

---

## 🔧 权重调整

修改 `ensemble_recommender.py` 中的权重配置：

```python
self.weights = {
    'ml_weighted': 0.40,   # ML 模型权重
    'hot_tracking': 0.25,  # 热号权重
    'cold_rebound': 0.20,  # 冷号权重
    'balanced': 0.15       # 均衡权重
}
```

**调整建议：**
- 近期 ML 表现好 → 增加 `ml_weighted`
- 热号连续中奖 → 增加 `hot_tracking`
- 冷号开始反弹 → 增加 `cold_rebound`
- 追求稳定 → 增加 `balanced`

---

## 📊 策略对比

| 指标 | 单一 ML 策略 | 集成策略 |
|------|-------------|----------|
| 稳定性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 覆盖率 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 抗风险 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 计算开销 | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## ⚠️ 注意事项

1. **ML 模型依赖**：需要预先训练好 ML 模型（`ml_model.pkl`）
2. **历史数据**：至少需要 10 期历史数据才能生成有效推荐
3. **权重总和**：确保所有策略权重之和为 1.0
4. **随机性**：最终推荐包含随机抽样，每次运行结果可能不同

---

## 📝 更新日志

**2026-03-16** - 初始版本
- ✅ 创建 `ensemble_recommender.py`
- ✅ 集成 4 种策略
- ✅ 加权投票机制
- ✅ 定时任务配置（每天 22:15）
- ✅ 修复 `ml_predictor.py` 的 `lottery_type` 参数问题

---

_最后更新：2026-03-16_
