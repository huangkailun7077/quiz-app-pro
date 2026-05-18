#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧家庭题库刷题系统 - 专业版（支持 PostgreSQL 持久化）
Alan 伦 ✨ 出品

功能：
- 学员登录、刷题、考试
- 老师后台、数据查看、Excel 导出
- ✅ 支持 PostgreSQL 数据库（数据永久保存）
"""

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
import json
import os
import hashlib
from datetime import datetime
import pandas as pd
import io
from db_config import get_db_connection, init_db, USE_POSTGRES

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'xiaoling_quiz_system_2026_secret_key')

# 禁止缓存静态资源和页面
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# 题库路径
QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), 'questions.json')

# 允许访问 uploads 目录
@app.route('/uploads/<filename>')
def serve_uploads(filename):
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_file(os.path.join(uploads_dir, filename))

# 访问指南页面
@app.route('/access')
def access_guide():
    return render_template('access.html')

# 加载题库
def load_questions():
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

# 数据库查询辅助函数
def execute_query(query, params=None, fetch=False, fetchall=False):
    """执行数据库查询"""
    conn = get_db_connection()
    c = conn.cursor()
    if params:
        c.execute(query, params)
    else:
        c.execute(query)
    
    result = None
    if fetch:
        result = c.fetchone()
    elif fetchall:
        result = c.fetchall()
    
    conn.commit()
    conn.close()
    return result
