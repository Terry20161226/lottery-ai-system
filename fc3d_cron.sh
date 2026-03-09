#!/bin/bash
# 福彩 3D 定时任务脚本
# 每日执行一次（福彩 3D 每日 21:30 开奖）

set -e

LOTTERY_DIR="/root/.openclaw/workspace/lottery"
LOG_FILE="$LOTTERY_DIR/logs/fc3d_$(date +%Y%m%d).log"

cd "$LOTTERY_DIR"

echo "======================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 执行福彩 3D 任务" >> "$LOG_FILE"

# 1. 生成推荐号码
echo "📝 生成推荐号码..." >> "$LOG_FILE"
python3 fc3d_strategy.py >> "$LOG_FILE" 2>&1

# 2. 核对中奖（如果有新开奖）
echo "🔍 核对中奖..." >> "$LOG_FILE"
python3 check_prize.py >> "$LOG_FILE" 2>&1 || echo "⚠️ 核对失败" >> "$LOG_FILE"

echo "✅ 福彩 3D 任务完成" >> "$LOG_FILE"
