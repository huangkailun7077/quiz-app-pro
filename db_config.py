#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库配置 - 支持 PostgreSQL 和 SQLite
"""

import os
import sqlite3
import psycopg2
from datetime import datetime
from urllib.parse import urlparse

# 检测是否使用 PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

def get_db_connection():
    """获取数据库连接 - 自动选择 PostgreSQL 或 SQLite"""
    if USE_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect('quiz.db')
        return conn

def init_db():
    """初始化数据库表结构"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if USE_POSTGRES:
        # PostgreSQL 表结构
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                grid TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'student',
                created_at TIMESTAMP NOT NULL
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS teacher_auth (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                granted_by TEXT NOT NULL,
                granted_at TIMESTAMP NOT NULL
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS answer_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                question_id TEXT NOT NULL,
                question_type TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_answer_user ON answer_records(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_answer_created ON answer_records(created_at)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                score REAL NOT NULL,
                correct_count INTEGER NOT NULL,
                total_count INTEGER NOT NULL,
                time_used INTEGER NOT NULL,
                stats TEXT NOT NULL,
                wrong_ids TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exam_user ON exam_records(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exam_created ON exam_records(created_at)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS practice_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                mode TEXT NOT NULL,
                question_type TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_practice_user ON practice_records(user_id)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS wrong_questions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                question_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_wrong_user ON wrong_questions(user_id)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS favorite_questions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                question_id TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_favorite_user ON favorite_questions(user_id)')
        
        # 默认授权 hkl7077 为老师
        c.execute('SELECT * FROM teacher_auth WHERE username = %s', ('hkl7077',))
        if not c.fetchone():
            c.execute('INSERT INTO teacher_auth (username, granted_by, granted_at) VALUES (%s, %s, %s)',
                     ('hkl7077', 'system', datetime.now().isoformat()))
        
    else:
        # SQLite 表结构
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                grid TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL DEFAULT 'student',
                created_at TEXT NOT NULL
            )
        ''')
        
        c.execute('PRAGMA table_info(users)')
        columns = [col[1] for col in c.fetchall()]
        if 'grid' not in columns:
            c.execute('ALTER TABLE users ADD COLUMN grid TEXT NOT NULL DEFAULT ""')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS teacher_auth (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                granted_by TEXT NOT NULL,
                granted_at TEXT NOT NULL
            )
        ''')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS answer_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                question_type TEXT NOT NULL,
                user_answer TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_answer_user ON answer_records(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_answer_created ON answer_records(created_at)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS exam_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                score REAL NOT NULL,
                correct_count INTEGER NOT NULL,
                total_count INTEGER NOT NULL,
                time_used INTEGER NOT NULL,
                stats TEXT NOT NULL,
                wrong_ids TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exam_user ON exam_records(user_id)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_exam_created ON exam_records(created_at)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS practice_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                question_type TEXT NOT NULL,
                question_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_practice_user ON practice_records(user_id)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS wrong_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_wrong_user ON wrong_questions(user_id)')
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS favorite_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_favorite_user ON favorite_questions(user_id)')
        
        # 默认授权 hkl7077 为老师
        c.execute('SELECT * FROM teacher_auth WHERE username = ?', ('hkl7077',))
        if not c.fetchone():
            c.execute('INSERT INTO teacher_auth (username, granted_by, granted_at) VALUES (?, ?, ?)',
                     ('hkl7077', 'system', datetime.now().isoformat()))
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print(f'✅ 数据库初始化完成 (使用 {"PostgreSQL" if USE_POSTGRES else "SQLite"})')
