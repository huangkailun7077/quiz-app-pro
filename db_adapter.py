#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库适配器 - 自动处理 PostgreSQL 和 SQLite 的差异
"""

import os
import sqlite3
import psycopg2
from datetime import datetime

# 检测是否使用 PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
USE_POSTGRES = DATABASE_URL is not None

class DatabaseAdapter:
    """数据库适配器 - 统一 PostgreSQL 和 SQLite 的接口"""
    
    def __init__(self):
        self.use_postgres = USE_POSTGRES
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """获取数据库连接"""
        if self.use_postgres:
            self.conn = psycopg2.connect(DATABASE_URL)
            self.cursor = self.conn.cursor()
        else:
            self.conn = sqlite3.connect('quiz.db')
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        return self
    
    def execute(self, query, params=None):
        """执行 SQL 查询"""
        if params is None:
            self.cursor.execute(query)
        else:
            # PostgreSQL 使用 %s，SQLite 使用 ?
            if self.use_postgres:
                self.cursor.execute(query, params)
            else:
                # 将 %s 转换为 ?
                query_sqlite = query.replace('%s', '?')
                self.cursor.execute(query_sqlite, params)
        return self
    
    def fetchone(self):
        """获取一行结果"""
        result = self.cursor.fetchone()
        if result and not self.use_postgres:
            # SQLite Row 转 dict
            return dict(result)
        return result
    
    def fetchall(self):
        """获取所有结果"""
        results = self.cursor.fetchall()
        if not self.use_postgres:
            # SQLite Row 转 list of dict
            return [dict(row) for row in results]
        return results
    
    def commit(self):
        """提交事务"""
        self.conn.commit()
        return self
    
    def close(self):
        """关闭连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def lastrowid(self):
        """获取最后插入的行 ID"""
        if self.use_postgres:
            # PostgreSQL 需要特殊处理
            self.cursor.execute('SELECT LASTVAL()')
            return self.cursor.fetchone()[0]
        else:
            return self.cursor.lastrowid
    
    def init_tables(self):
        """初始化数据库表"""
        if self.use_postgres:
            # PostgreSQL 表结构
            self.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    grid TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'student',
                    created_at TIMESTAMP NOT NULL
                )
            ''').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS teacher_auth (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TIMESTAMP NOT NULL
                )
            ''').commit()
            
            self.execute('''
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
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_answer_user ON answer_records(user_id)')
            self.execute('CREATE INDEX IF NOT EXISTS idx_answer_created ON answer_records(created_at)').commit()
            
            self.execute('''
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
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_exam_user ON exam_records(user_id)')
            self.execute('CREATE INDEX IF NOT EXISTS idx_exam_created ON exam_records(created_at)').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS practice_records (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    mode TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    question_count INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_practice_user ON practice_records(user_id)').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS wrong_questions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    question_id TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_wrong_user ON wrong_questions(user_id)').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS favorite_questions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    question_id TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_favorite_user ON favorite_questions(user_id)').commit()
            
            # 默认授权 hkl7077 为老师
            self.execute('SELECT * FROM teacher_auth WHERE username = %s', ('hkl7077',))
            if not self.fetchone():
                self.execute('INSERT INTO teacher_auth (username, granted_by, granted_at) VALUES (%s, %s, %s)',
                           ('hkl7077', 'system', datetime.now().isoformat())).commit()
        else:
            # SQLite 表结构
            self.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    grid TEXT NOT NULL DEFAULT '',
                    role TEXT NOT NULL DEFAULT 'student',
                    created_at TEXT NOT NULL
                )
            ''').commit()
            
            # 检查 grid 字段
            self.execute('PRAGMA table_info(users)')
            columns = [col[1] for col in self.fetchall()]
            if 'grid' not in columns:
                self.execute('ALTER TABLE users ADD COLUMN grid TEXT NOT NULL DEFAULT ""').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS teacher_auth (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    granted_by TEXT NOT NULL,
                    granted_at TEXT NOT NULL
                )
            ''').commit()
            
            self.execute('''
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
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_answer_user ON answer_records(user_id)')
            self.execute('CREATE INDEX IF NOT EXISTS idx_answer_created ON answer_records(created_at)').commit()
            
            self.execute('''
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
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_exam_user ON exam_records(user_id)')
            self.execute('CREATE INDEX IF NOT EXISTS idx_exam_created ON exam_records(created_at)').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS practice_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mode TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    question_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_practice_user ON practice_records(user_id)').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS wrong_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_wrong_user ON wrong_questions(user_id)').commit()
            
            self.execute('''
                CREATE TABLE IF NOT EXISTS favorite_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''').commit()
            self.execute('CREATE INDEX IF NOT EXISTS idx_favorite_user ON favorite_questions(user_id)').commit()
            
            # 默认授权 hkl7077 为老师
            self.execute('SELECT * FROM teacher_auth WHERE username = ?', ('hkl7077',))
            if not self.fetchone():
                self.execute('INSERT INTO teacher_auth (username, granted_by, granted_at) VALUES (?, ?, ?)',
                           ('hkl7077', 'system', datetime.now().isoformat())).commit()
        
        return self

# 便捷函数
def get_db():
    """获取数据库适配器实例"""
    return DatabaseAdapter().connect()

def init_db():
    """初始化数据库表"""
    db = DatabaseAdapter()
    db.connect()
    db.init_tables()
    db.close()
    return db
