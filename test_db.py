#!/usr/bin/env python3
"""
测试数据库连接
"""
import os
import sys

# 设置环境变量（模拟 Render 环境）
os.environ['DATABASE_URL'] = sys.argv[1] if len(sys.argv) > 1 else ''

from db_adapter import get_db, init_db, USE_POSTGRES

print(f"📊 数据库类型：{'PostgreSQL ✅' if USE_POSTGRES else 'SQLite ⚠️'}")

if USE_POSTGRES:
    print("🎉 数据将永久保存！")
    try:
        db = get_db()
        db.execute('SELECT COUNT(*) FROM users')
        count = db.fetchone()
        print(f"📈 当前用户数：{count[0] if count else 0}")
        db.close()
        print("✅ 数据库连接成功！")
    except Exception as e:
        print(f"❌ 数据库连接失败：{e}")
else:
    print("⚠️  未配置 DATABASE_URL，使用 SQLite（重启会丢数据）")
    print("请在 Render 上配置 DATABASE_URL 环境变量")
