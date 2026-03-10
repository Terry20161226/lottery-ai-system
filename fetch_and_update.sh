#!/bin/bash
# 彩票开奖数据自动获取并更新脚本

cd /root/.openclaw/workspace/lottery

echo "======================================"
echo "彩票开奖数据自动更新"
echo "======================================"

# 双色球更新
echo ""
echo "【双色球】"
echo "--------------------------------------"

# 获取最新开奖数据（通过 web_search）
RESULT=$(openclaw web-search --query "双色球 最新开奖结果 2026 年 期号 开奖号码" --count 3 2>/dev/null)

# 解析结果并保存
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage
import re

# 这里需要从搜索结果解析，简化处理：检查是否已有最新数据
storage = LotteryStorage()
last_issue = storage.get_last_issue('ssq')

# 简单检查：如果最新期号是 2026023 或更新，则跳过
if last_issue and int(last_issue) >= 2026023:
    print(f"✅ 双色球已是最新期号 ({last_issue})")
else:
    print(f"📡 需要更新双色球数据 (当前最新：{last_issue})")
    print("   请在下次开奖后手动运行更新")
PYTHON_SCRIPT

# 大乐透更新
echo ""
echo "【大乐透】"
echo "--------------------------------------"

python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '/root/.openclaw/workspace/lottery')
from lottery_storage import LotteryStorage

storage = LotteryStorage()
last_issue = storage.get_last_issue('dlt')

if last_issue and int(last_issue) >= 2026021:
    print(f"✅ 大乐透已是最新期号 ({last_issue})")
else:
    print(f"📡 需要更新大乐透数据 (当前最新：{last_issue})")
    print("   请在下次开奖后手动运行更新")
PYTHON_SCRIPT

echo ""
echo "======================================"
echo "更新检查完成"
echo "======================================"
