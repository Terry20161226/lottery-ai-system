#!/bin/bash
# 彩票推荐推送执行脚本
# 由 cron job 调用，执行 Python 脚本并推送结果到钉钉

cd /root/.openclaw/workspace/lottery

# 执行 Python 脚本获取推荐内容
MESSAGE=$(python3 push_to_dingtalk.py 2>&1 | tail -20)

# 输出消息（供 cron job 捕获并发送）
echo "$MESSAGE"
