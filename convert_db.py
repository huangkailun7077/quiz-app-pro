#!/usr/bin/env python3
"""
自动转换 app.py 以支持 PostgreSQL
"""

import re

# 读取原文件
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 替换导入语句
content = content.replace(
    'import sqlite3\nimport psycopg2',
    'from db_adapter import get_db, init_db, USE_POSTGRES'
)

# 2. 替换 get_db 调用模式
# conn = get_db() -> db = get_db()
content = re.sub(r'conn = get_db\(\)', 'db = get_db()', content)

# 3. 替换 cursor 调用模式
# c = conn.cursor() -> 删除这行
content = re.sub(r'\s+c = conn\.cursor\(\)\n', '\n', content)

# 4. 替换 execute 调用
# c.execute( -> db.execute(
content = re.sub(r'c\.execute\(', 'db.execute(', content)

# 5. 替换 fetchone/fetchall 调用
# c.fetchone() -> db.fetchone()
content = re.sub(r'c\.fetchone\(\)', 'db.fetchone()', content)
# c.fetchall() -> db.fetchall()
content = re.sub(r'c\.fetchall\(\)', 'db.fetchall()', content)

# 6. 替换 commit/close
# conn.commit() -> db.commit()
content = re.sub(r'conn\.commit\(\)', 'db.commit()', content)
# conn.close() -> db.close()
content = re.sub(r'conn\.close\(\)', 'db.close()', content)

# 7. 替换 lastrowid
# c.lastrowid -> db.lastrowid()
content = re.sub(r'c\.lastrowid', 'db.lastrowid()', content)

# 8. 替换 ? 为 %s (SQL 占位符)
# 这个要小心，只替换 SQL 语句中的 ?
# 暂时跳过，让 db_adapter 处理

# 9. 删除旧的 init_db 和 get_db 函数定义
# 找到并删除这些函数
content = re.sub(
    r'\n# 数据库初始化\ndef init_db\(\):.*?(?=\n# |\n@app\.route|\ndef load_questions)',
    '\n',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'\n# 获取数据库连接\ndef get_db\(\):.*?(?=\n# |\n@app\.route)',
    '\n',
    content,
    flags=re.DOTALL
)

# 10. 删除旧的 DATABASE_URL 相关代码
content = re.sub(
    r'\n# 数据库路径\nDB_PATH = .*?\nQUESTIONS_PATH',
    '\n# 题库路径\nQUESTIONS_PATH',
    content,
    flags=re.DOTALL
)

content = re.sub(
    r'\n# 数据库配置 - 支持 PostgreSQL 和 SQLite\nDATABASE_URL = .*?\n    return conn\n',
    '\n',
    content,
    flags=re.DOTALL
)

# 11. 添加 init_db 调用
if 'init_db()' not in content:
    content = content.replace(
        "app = Flask(__name__)",
        "app = Flask(__name__)\n\n# 初始化数据库\ninit_db()"
    )

# 写入新文件
with open('app_converted.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 转换完成！生成文件：app_converted.py')
print('请检查后替换 app.py')
