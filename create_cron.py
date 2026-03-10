#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建彩票推荐定时任务
每天 22:00 推送双色球和大乐透推荐号码
"""

import subprocess
import sys

def create_cron_job():
    """创建定时任务"""
    
    # 定时任务配置
    cron_expr = "0 22 * * *"  # 每天 22:00
    task_name = "彩票推荐号码推送"
    command = "bash /root/.openclaw/workspace/lottery/run_push.sh"
    
    # 使用 openclaw CLI 创建 cron job（如果支持）
    # 或者通过 Python 直接添加到 crontab
    
    print(f"任务名称：{task_name}")
    print(f"Cron 表达式：{cron_expr}")
    print(f"执行命令：{command}")
    print("")
    print("请手动添加以下 cron 任务：")
    print(f"{cron_expr} {command}")
    
    # 尝试添加到 crontab
    try:
        # 获取当前 crontab
        result = subprocess.run(["crontab", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        current_cron = result.stdout if result.returncode == 0 else ""
        
        # 检查是否已存在
        if command in current_cron:
            print("\n✅ 任务已存在")
            return
        
        # 添加新任务
        new_cron = current_cron.strip() + "\n" if current_cron.strip() else ""
        new_cron += f"{cron_expr} {command}\n"
        
        # 写入 crontab
        proc = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, text=True)
        proc.communicate(new_cron)
        
        print("\n✅ 定时任务创建成功")
        print("每天晚上 22:00 自动推送彩票推荐号码")
        
    except Exception as e:
        print(f"\n❌ 创建失败：{e}")
        print("请手动执行：crontab -e 并添加上述任务")


if __name__ == "__main__":
    create_cron_job()
