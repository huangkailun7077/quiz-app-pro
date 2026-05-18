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

# 获取数据库连接（兼容旧代码）
def get_db():
    """获取数据库连接（返回兼容对象）"""
    conn = get_db_connection()
    if not USE_POSTGRES:
        conn.row_factory = sqlite3.Row
    return conn

# 首页
@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'teacher':
            return redirect(url_for('teacher_dashboard'))
        else:
            return redirect(url_for('student_home'))
    return render_template('login.html')

# 登录
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    role = data.get('role', 'student')
    grid = data.get('grid', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': '请输入用户名'})
    
    # 老师账号检查：必须是 hkl7077 或在授权列表中
    if role == 'teacher':
        if username != 'hkl7077':
            conn = get_db()
            c = conn.cursor()
            if USE_POSTGRES:
                c.execute('SELECT * FROM teacher_auth WHERE username = %s', (username,))
            else:
                c.execute('SELECT * FROM teacher_auth WHERE username = ?', (username,))
            auth = c.fetchone()
            conn.close()
            
            if not auth:
                return jsonify({'success': False, 'message': '您没有老师权限，请联系管理员授权'})
    
    conn = get_db()
    c = conn.cursor()
    
    # 查找或创建用户
    if USE_POSTGRES:
        c.execute('SELECT * FROM users WHERE username = %s', (username,))
    else:
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    
    if not user:
        # 创建新用户
        created_at = datetime.now().isoformat()
        if USE_POSTGRES:
            c.execute('INSERT INTO users (username, grid, role, created_at) VALUES (%s, %s, %s, %s)',
                     (username, grid, role, created_at))
        else:
            c.execute('INSERT INTO users (username, grid, role, created_at) VALUES (?, ?, ?, ?)',
                     (username, grid, role, created_at))
        conn.commit()
        # 获取新用户的 ID
        if USE_POSTGRES:
            c.execute('SELECT id FROM users WHERE username = %s', (username,))
            user_id = c.fetchone()[0]
        else:
            user_id = c.lastrowid
    else:
        user_id = user['id']
        # 更新角色和网格（如果是老师登录或网格为空）
        if role == 'teacher' and user['role'] != 'teacher':
            if USE_POSTGRES:
                c.execute('UPDATE users SET role = %s, grid = %s WHERE id = %s', ('teacher', grid, user_id))
            else:
                c.execute('UPDATE users SET role = ?, grid = ? WHERE id = ?', ('teacher', grid, user_id))
            conn.commit()
        elif not user['grid'] and grid:
            if USE_POSTGRES:
                c.execute('UPDATE users SET grid = %s WHERE id = %s', (grid, user_id))
            else:
                c.execute('UPDATE users SET grid = ? WHERE id = ?', (grid, user_id))
            conn.commit()
    
    conn.close()
    
    # 设置 session
    session['user_id'] = user_id
    session['username'] = username
    session['role'] = role
    session['grid'] = grid
    
    return jsonify({'success': True})

# 获取当前用户
@app.route('/api/me')
def get_me():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '未登录'})
    
    return jsonify({
        'success': True,
        'user_id': session['user_id'],
        'username': session['username'],
        'role': session['role'],
        'grid': session.get('grid', '')
    })

# 登出
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 学员主页
@app.route('/student')
def student_home():
    if 'user_id' not in session or session['role'] != 'student':
        return redirect(url_for('index'))
    return render_template('student.html')

# 老师后台
@app.route('/teacher')
def teacher_dashboard():
    if 'user_id' not in session or session['role'] != 'teacher':
        return redirect(url_for('index'))
    return render_template('teacher.html')

# 初始化数据库
@app.before_request
def before_request():
    """确保数据库已初始化"""
    # 这里可以添加初始化检查
    pass

# 启动应用
if __name__ == '__main__':
    # 初始化数据库
    init_db()
    db_type = "PostgreSQL" if USE_POSTGRES else "SQLite"
    print(f'✅ 数据库已初始化（使用 {db_type}）')
    if USE_POSTGRES:
        print('🎉 数据将永久保存！')
    else:
        print('⚠️  警告：SQLite 数据在重启后可能丢失，请配置 DATABASE_URL 使用 PostgreSQL')
    
    # 运行 Flask
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
