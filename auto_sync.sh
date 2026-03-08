#!/bin/bash
# Lottery AI System 自动同步脚本
# 检测变更并自动推送到 GitHub

set -e

# 配置
LOTTERY_DIR="/root/.openclaw/workspace/lottery"
GITHUB_REPO="https://github.com/Terry20161226/lottery-ai-system.git"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"
COMMIT_MSG="${1:-auto: 自动同步 $(date +%Y-%m-%d_%H-%M-%S)}"

cd "$LOTTERY_DIR"

# 配置 Git 用户
git config user.name "Lottery System"
git config user.email "user@example.com"

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "✅ 无变更，跳过推送"
    exit 0
fi

# 添加变更
git add -A

# 提交
git commit -m "$COMMIT_MSG"

# 推送（带 Token）
if [ -n "$GITHUB_TOKEN" ]; then
    AUTH_REPO="https://BoFeng:${GITHUB_TOKEN}@github.com/Terry20161226/lottery-ai-system.git"
    git push "$AUTH_REPO" main
    # 恢复远程 URL（清除 Token）
    git remote set-url origin "$GITHUB_REPO"
else
    echo "⚠️ GITHUB_TOKEN 未设置，尝试直接推送"
    git push origin main
fi

echo "✅ 推送完成：$COMMIT_MSG"
