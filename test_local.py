#!/usr/bin/env python3
"""
本地测试数据库适配器
"""
import os
import sys

# 不设置 DATABASE_URL，使用 SQLite 测试
if 'DATABASE_URL' in os.environ:
    del os.environ['DATABASE_URL']

from db_adapter import get_db, init_db, USE_POSTGRES

print(f"数据库类型：{'PostgreSQL' if USE_POSTGRES else 'SQLite'}")

try:
    # 初始化数据库
    init_db()
    print("✅ 数据库初始化成功")
    
    # 测试插入数据
    db = get_db()
    db.execute('''
        INSERT OR IGNORE INTO users (username, grid, role, created_at) 
        VALUES (%s, %s, %s, %s)
    ''', ('test_user', '测试网格', 'student', '2026-05-18T12:00:00'))
    db.commit()
    print("✅ 插入测试数据成功")
    
    # 测试查询
    db.execute('SELECT * FROM users WHERE username = %s', ('test_user',))
    user = db.fetchone()
    print(f"✅ 查询成功：{user}")
    
    db.close()
    print("✅ 所有测试通过！")
    
except Exception as e:
    print(f"❌ 错误：{e}")
    import traceback
    traceback.print_exc()
