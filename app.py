#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智慧家庭题库刷题系统 - 专业版
Alan伦 ✨ 出品

功能：
- 学员登录、刷题、考试
- 老师后台、数据查看、Excel 导出
"""

from flask import Flask, render_template, request, jsonify, session, send_file, redirect, url_for
from db_adapter import get_db, init_db, USE_POSTGRES
import json
import os
import hashlib
from datetime import datetime
import pandas as pd
import io
from urllib.parse import urlparse

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'xiaoling_quiz_system_2026_secret_key')

# Session 配置 - 支持 HTTPS 环境（Render）
# 自动检测是否为 HTTPS 环境
if os.environ.get('RENDER_EXTERNAL_URL'):
    # Render 环境：启用安全 session
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
else:
    # 本地开发：不限制
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 1 天

# 禁止缓存静态资源和页面
@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# 题库路径
QUESTIONS_PATH = os.path.join(os.path.dirname(__file__), 'questions.json')

# 初始化数据库（延迟到应用启动时）
try:
    init_db()
except Exception as e:
    print(f'⚠️  数据库初始化失败：{e}')
    print('应用将继续运行，但数据库功能可能不可用')

# 允许访问 uploads 目录
@app.route('/uploads/<filename>')
def serve_uploads(filename):
    uploads_dir = os.path.join(os.path.dirname(__file__), 'uploads')
    return send_file(os.path.join(uploads_dir, filename))

# 访问指南页面
@app.route('/access')
def access_guide():
    return render_template('access.html')

# 调试端点 - 检查数据库状态
@app.route('/debug/db')
def debug_db():
    try:
        from db_adapter import USE_POSTGRES
        db = get_db()
        db.execute('SELECT COUNT(*) FROM users')
        count = db.fetchone()
        db.close()
        return jsonify({
            'success': True,
            'database': 'PostgreSQL' if USE_POSTGRES else 'SQLite',
            'user_count': count[0] if count else 0,
            'status': 'connected'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'database': 'unknown'
        }), 500


# 加载题库
def load_questions():
    with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


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
    try:
        data = request.json
        username = data.get('username', '').strip()
        role = data.get('role', 'student')
        grid = data.get('grid', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': '请输入用户名'})
        
        # 老师账号检查：必须是 hkl7077 或在授权列表中
        if role == 'teacher':
            if username != 'hkl7077':
                db = get_db()
                db.execute('SELECT * FROM teacher_auth WHERE username = ?', (username,))
                auth = db.fetchone()
                db.close()
                
                if not auth:
                    return jsonify({'success': False, 'message': '您没有老师权限，请联系管理员授权'})
        
        db = get_db()
        
        # 查找或创建用户
        db.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = db.fetchone()
        
        if not user:
            # 创建新用户
            created_at = datetime.now().isoformat()
            db.execute('INSERT INTO users (username, grid, role, created_at) VALUES (?, ?, ?, ?)',
                     (username, grid, role, created_at))
            db.commit()
            user_id = db.lastrowid()
        else:
            user_id = user['id']
            # 更新角色和网格（如果是老师登录或网格为空）
            if role == 'teacher' and user['role'] != 'teacher':
                db.execute('UPDATE users SET role = ?, grid = ? WHERE id = ?', ('teacher', grid, user_id))
                db.commit()
            elif not user.get('grid') and grid:
                db.execute('UPDATE users SET grid = ? WHERE id = ?', (grid, user_id))
                db.commit()
        
        db.close()
        
        session['user_id'] = user_id
        session['username'] = username
        session['role'] = role
        session['grid'] = grid
        
        return jsonify({'success': True, 'message': '登录成功'})
    
    except Exception as e:
        print(f'❌ 登录错误：{e}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'登录失败：{str(e)}'}), 500

# 登出
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# 学员首页
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

# 获取题库数据
@app.route('/api/questions')
def api_get_questions():
    questions = load_questions()
    return jsonify(questions)

# 保存答题记录
@app.route('/api/save_answer', methods=['POST'])
def api_save_answer():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.json
    user_id = session['user_id']
    
    db = get_db()
    
    # 保存答题记录
    db.execute('''
        INSERT INTO answer_records (user_id, question_id, question_type, user_answer, correct_answer, is_correct, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data['questionId'], data['questionType'], data['userAnswer'], 
          data['correctAnswer'], 1 if data['isCorrect'] else 0, datetime.now().isoformat()))
    
    # 如果是错题，加入错题本
    if not data['isCorrect']:
        db.execute('''
            INSERT OR IGNORE INTO wrong_questions (user_id, question_id, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, data['questionId'], datetime.now().isoformat()))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True})

# 保存考试记录
@app.route('/api/save_exam', methods=['POST'])
def api_save_exam():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.json
    user_id = session['user_id']
    
    db = get_db()
    
    # 保存考试记录
    db.execute('''
        INSERT INTO exam_records (user_id, score, correct_count, total_count, time_used, stats, wrong_ids, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, data['score'], data['correctCount'], data['totalCount'], 
          data['timeUsed'], json.dumps(data['stats']), json.dumps(data['wrongIds']), 
          datetime.now().isoformat()))
    
    # 错题加入错题本
    for qid in data['wrongIds']:
        db.execute('''
            INSERT OR IGNORE INTO wrong_questions (user_id, question_id, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, qid, datetime.now().isoformat()))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True})

# 保存刷题记录
@app.route('/api/save_practice', methods=['POST'])
def api_save_practice():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.json
    user_id = session['user_id']
    
    db = get_db()
    
    db.execute('''
        INSERT INTO practice_records (user_id, mode, question_type, question_count, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, data['mode'], data['questionType'], data['questionCount'], 
          datetime.now().isoformat()))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True})

# 收藏/取消收藏
@app.route('/api/toggle_favorite', methods=['POST'])
def api_toggle_favorite():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    data = request.json
    user_id = session['user_id']
    question_id = data['questionId']
    
    db = get_db()
    
    # 检查是否已收藏
    db.execute('SELECT id FROM favorite_questions WHERE user_id = ? AND question_id = ?', 
              (user_id, question_id))
    existing = db.fetchone()
    
    if existing:
        # 取消收藏
        db.execute('DELETE FROM favorite_questions WHERE id = ?', (existing['id'],))
        action = 'removed'
    else:
        # 加入收藏
        db.execute('''
            INSERT INTO favorite_questions (user_id, question_id, created_at)
            VALUES (?, ?, ?)
        ''', (user_id, question_id, datetime.now().isoformat()))
        action = 'added'
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'action': action})

# 获取学员统计数据
@app.route('/api/student/stats')
def api_student_stats():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_id = session['user_id']
    db = get_db()
    
    # 答题总数和正确率
    db.execute('''
        SELECT COUNT(*) as total, SUM(is_correct) as correct
        FROM answer_records WHERE user_id = ?
    ''', (user_id,))
    answer_stats = db.fetchone()
    
    # 考试次数
    db.execute('SELECT COUNT(*) FROM exam_records WHERE user_id = ?', (user_id,))
    exam_count = db.fetchone()[0]
    
    # 刷题次数
    db.execute('SELECT COUNT(*) FROM practice_records WHERE user_id = ?', (user_id,))
    practice_count = db.fetchone()[0]
    
    # 错题数
    db.execute('SELECT COUNT(DISTINCT question_id) FROM wrong_questions WHERE user_id = ?', (user_id,))
    wrong_count = db.fetchone()[0]
    
    # 收藏数
    db.execute('SELECT COUNT(DISTINCT question_id) FROM favorite_questions WHERE user_id = ?', (user_id,))
    favorite_count = db.fetchone()[0]
    
    db.close()
    
    total = answer_stats['total'] or 0
    correct = answer_stats['correct'] or 0
    correct_rate = round((correct / total * 100), 1) if total > 0 else 0
    
    return jsonify({
        'success': True,
        'data': {
            'totalAnswers': total,
            'correctAnswers': correct,
            'correctRate': correct_rate,
            'examCount': exam_count,
            'practiceCount': practice_count,
            'wrongCount': wrong_count,
            'favoriteCount': favorite_count
        }
    })

# 获取学员考试记录
@app.route('/api/student/exams')
def api_student_exams():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_id = session['user_id']
    db = get_db()
    
    db.execute('''
        SELECT * FROM exam_records 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 50
    ''', (user_id,))
    
    exams = []
    for row in db.fetchall():
        exams.append({
            'id': row['id'],
            'score': row['score'],
            'correctCount': row['correct_count'],
            'totalCount': row['total_count'],
            'timeUsed': row['time_used'],
            'stats': json.loads(row['stats']),
            'createdAt': row['created_at']
        })
    
    db.close()
    return jsonify({'success': True, 'exams': exams})

# 学员：获取错题集
@app.route('/api/student/wrong')
def api_student_wrong():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_id = session['user_id']
    db = get_db()
    
    # 获取错题（去重）
    db.execute('''
        SELECT DISTINCT w.question_id, w.created_at
        FROM wrong_questions w
        WHERE w.user_id = ?
        ORDER BY w.created_at DESC
    ''', (user_id,))
    
    wrong_ids = [row['question_id'] for row in db.fetchall()]
    
    # 从题库中获取题目详情
    try:
        with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
    except:
        db.close()
        return jsonify({'success': False, 'message': '加载题库失败'})
    
    wrong_questions = []
    for q in all_questions:
        if q['id'] in wrong_ids:
            wrong_questions.append({
                'id': q['id'],
                'content': q['content'],
                'type': q['type'],
                'options': q.get('options', {}),
                'answer': q['answer']
            })
    
    db.close()
    
    return jsonify({
        'success': True,
        'total': len(wrong_questions),
        'questions': wrong_questions
    })

# 学员：清空错题集
@app.route('/api/student/wrong/clear', methods=['POST'])
def api_student_wrong_clear():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    user_id = session['user_id']
    db = get_db()
    
    db.execute('DELETE FROM wrong_questions WHERE user_id = ?', (user_id,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': '错题集已清空'})

# 老师：获取所有学员列表
@app.route('/api/teacher/students')
def api_teacher_students():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    
    db.execute('''
        SELECT u.id, u.username, u.created_at,
               COUNT(DISTINCT a.id) as answer_count,
               COUNT(DISTINCT e.id) as exam_count,
               COUNT(DISTINCT p.id) as practice_count,
               COUNT(DISTINCT w.question_id) as wrong_count
        FROM users u
        LEFT JOIN answer_records a ON u.id = a.user_id
        LEFT JOIN exam_records e ON u.id = e.user_id
        LEFT JOIN practice_records p ON u.id = p.user_id
        LEFT JOIN wrong_questions w ON u.id = w.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY u.created_at DESC
    ''')
    
    students = []
    for row in db.fetchall():
        students.append({
            'id': row['id'],
            'username': row['username'],
            'createdAt': row['created_at'],
            'answerCount': row['answer_count'],
            'examCount': row['exam_count'],
            'practiceCount': row['practice_count'],
            'wrongCount': row['wrong_count']
        })
    
    db.close()
    return jsonify({'success': True, 'students': students})

# 老师：删除学员
@app.route('/api/teacher/student/<int:student_id>', methods=['DELETE'])
def api_delete_student(student_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    
    # 删除答题记录
    db.execute('DELETE FROM answer_records WHERE user_id = ?', (student_id,))
    # 删除考试记录
    db.execute('DELETE FROM exam_records WHERE user_id = ?', (student_id,))
    # 删除用户
    db.execute('DELETE FROM users WHERE id = ? AND role = ?', (student_id, 'student'))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': '学员已删除'})

# 老师：获取指定学员的详细信息
@app.route('/api/teacher/student/<int:student_id>')
def api_teacher_student_detail(student_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    
    # 学员基本信息
    db.execute('SELECT * FROM users WHERE id = ? AND role = "student"', (student_id,))
    student = db.fetchone()
    
    if not student:
        db.close()
        return jsonify({'success': False, 'message': '学员不存在'})
    
    # 答题统计
    db.execute('''
        SELECT COUNT(*) as total, SUM(is_correct) as correct
        FROM answer_records WHERE user_id = ?
    ''', (student_id,))
    answer_stats = db.fetchone()
    
    # 考试成绩统计
    db.execute('''
        SELECT 
            COUNT(*) as exam_count,
            AVG(score) as avg_score,
            MAX(score) as max_score,
            MIN(score) as min_score
        FROM exam_records 
        WHERE user_id = ?
    ''', (student_id,))
    exam_stats = db.fetchone()
    
    # 最近 20 次考试记录
    db.execute('''
        SELECT * FROM exam_records 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 20
    ''', (student_id,))
    
    exams = []
    for row in db.fetchall():
        exams.append({
            'id': row['id'],
            'score': row['score'],
            'correctCount': row['correct_count'],
            'totalCount': row['total_count'],
            'timeUsed': row['time_used'],
            'createdAt': row['created_at']
        })
    
    # 同网格平均成绩对比
    grid = student['grid']
    db.execute('''
        SELECT AVG(e.score) as grid_avg
        FROM exam_records e
        JOIN users u ON e.user_id = u.id
        WHERE u.grid = ? AND u.role = "student"
    ''', (grid,))
    grid_avg_result = db.fetchone()
    grid_avg = round(grid_avg_result['grid_avg'], 1) if grid_avg_result and grid_avg_result['grid_avg'] else 0
    
    db.close()
    
    total = answer_stats['total'] or 0
    correct = answer_stats['correct'] or 0
    correct_rate = round((correct / total * 100), 1) if total > 0 else 0
    
    avg_score = round(exam_stats['avg_score'], 1) if exam_stats['avg_score'] else 0
    
    return jsonify({
        'success': True,
        'student': {
            'id': student['id'],
            'username': student['username'],
            'grid': grid,
            'createdAt': student['created_at'],
            'totalAnswers': total,
            'correctAnswers': correct,
            'correctRate': correct_rate,
            'examCount': exam_stats['exam_count'] or 0,
            'avgScore': avg_score,
            'maxScore': exam_stats['max_score'] or 0,
            'minScore': exam_stats['min_score'] or 0,
            'gridAvgScore': grid_avg,
            'scoreDiff': round(avg_score - grid_avg, 1),
            'exams': exams
        }
    })

# 老师：获取指定学员的详细学习记录
@app.route('/api/teacher/student/<int:student_id>/details')
def api_teacher_student_details(student_id):
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    
    # 刷题记录
    db.execute('''
        SELECT mode, question_type, question_count, created_at
        FROM practice_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (student_id,))
    
    practice = []
    for row in db.fetchall():
        practice.append({
            'mode': row['mode'],
            'question_type': row['question_type'],
            'question_count': row['question_count'],
            'created_at': row['created_at']
        })
    
    # 考试记录
    db.execute('''
        SELECT score, correct_count, total_count, time_used, created_at
        FROM exam_records
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    ''', (student_id,))
    
    exams = []
    for row in db.fetchall():
        exams.append({
            'score': row['score'],
            'correct_count': row['correct_count'],
            'total_count': row['total_count'],
            'time_used': row['time_used'],
            'created_at': row['created_at']
        })
    
    # 答题记录（按题型统计）
    db.execute('''
        SELECT question_type, COUNT(*) as count, SUM(is_correct) as correct
        FROM answer_records
        WHERE user_id = ?
        GROUP BY question_type
    ''', (student_id,))
    
    by_type = {}
    for row in db.fetchall():
        by_type[row['question_type']] = {
            'count': row['count'],
            'correct': row['correct'] or 0,
            'rate': round(((row['correct'] or 0) / row['count'] * 100), 1) if row['count'] > 0 else 0
        }
    
    db.close()
    
    return jsonify({
        'success': True,
        'practice': practice,
        'exams': exams,
        'by_type': by_type
    })

# 老师：导出详细 Excel
@app.route('/api/teacher/export')
def api_teacher_export():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    
    # 获取所有学员数据
    db.execute('''
        SELECT u.id, u.username, u.created_at,
               COUNT(DISTINCT a.id) as answer_count,
               SUM(a.is_correct) as correct_count,
               COUNT(DISTINCT e.id) as exam_count,
               COUNT(DISTINCT w.question_id) as wrong_count
        FROM users u
        LEFT JOIN answer_records a ON u.id = a.user_id
        LEFT JOIN exam_records e ON u.id = e.user_id
        LEFT JOIN wrong_questions w ON u.id = w.user_id
        WHERE u.role = 'student'
        GROUP BY u.id
        ORDER BY u.username
    ''')
    
    students_data = []
    for row in db.fetchall():
        total = row['answer_count'] or 0
        correct = row['correct_count'] or 0
        correct_rate = round((correct / total * 100), 1) if total > 0 else 0
        
        students_data.append({
            '学员名': row['username'],
            '注册时间': row['created_at'][:10],
            '答题总数': total,
            '正确数': correct or 0,
            '正确率': f'{correct_rate}%',
            '考试次数': row['exam_count'] or 0,
            '错题数': row['wrong_count'] or 0
        })
    
    # 获取详细学习记录
    db.execute('''
        SELECT u.username, p.mode, p.question_type, p.question_count, p.created_at
        FROM practice_records p
        JOIN users u ON p.user_id = u.id
        WHERE u.role = 'student'
        ORDER BY p.created_at DESC
    ''')
    
    practice_records = []
    for row in db.fetchall():
        practice_records.append({
            '学员名': row['username'],
            '学习模式': row['mode'],
            '题型': row['question_type'],
            '题数': row['question_count'],
            '学习时间': row['created_at'][:19].replace('T', ' ')
        })
    
    # 获取详细考试记录
    db.execute('''
        SELECT u.username, e.score, e.correct_count, e.total_count, e.time_used, e.created_at
        FROM exam_records e
        JOIN users u ON e.user_id = u.id
        WHERE u.role = 'student'
        ORDER BY e.created_at DESC
    ''')
    
    exam_records = []
    for row in db.fetchall():
        exam_records.append({
            '学员名': row['username'],
            '分数': row['score'],
            '正确数': row['correct_count'],
            '总题数': row['total_count'],
            '用时 (秒)': row['time_used'],
            '考试时间': row['created_at'][:19].replace('T', ' ')
        })
    
    db.close()
    
    # 创建 Excel（多个 sheet）
    df_summary = pd.DataFrame(students_data)
    df_practice = pd.DataFrame(practice_records)
    df_exam = pd.DataFrame(exam_records)
    
    # 添加统计行
    total_students = len(students_data)
    total_answers = sum(s['答题总数'] for s in students_data)
    total_correct = sum(s['正确数'] for s in students_data)
    avg_correct_rate = round((total_correct / total_answers * 100), 1) if total_answers > 0 else 0
    
    summary = {
        '学员名': f'总计 ({total_students}人)',
        '注册时间': '-',
        '答题总数': total_answers,
        '正确数': total_correct,
        '正确率': f'{avg_correct_rate}%',
        '考试次数': sum(s['考试次数'] for s in students_data),
        '错题数': sum(s['错题数'] for s in students_data)
    }
    
    df_summary = pd.concat([df_summary, pd.DataFrame([summary])], ignore_index=True)
    
    # 输出到内存
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, index=False, sheet_name='学员统计')
        df_practice.to_excel(writer, index=False, sheet_name='刷题记录')
        df_exam.to_excel(writer, index=False, sheet_name='考试记录')
        
        # 自动调整列宽
        for sheet_name in ['学员统计', '刷题记录', '考试记录']:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    output.seek(0)
    
    # 生成文件名
    filename = f'学员学习统计_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

# ============== 老师管理功能 ==============

# 获取所有授权老师列表
@app.route('/api/teacher/teachers')
def api_teacher_list():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    db.execute('SELECT * FROM teacher_auth ORDER BY granted_at DESC')
    teachers = db.fetchall()
    db.close()
    
    return jsonify({
        'success': True,
        'teachers': [dict(t) for t in teachers]
    })

# 添加老师
@app.route('/api/teacher/add_teacher', methods=['POST'])
def api_add_teacher():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': '请输入用户名'})
    
    # 检查是否已存在
    db = get_db()
    db.execute('SELECT * FROM teacher_auth WHERE username = ?', (username,))
    if db.fetchone():
        db.close()
        return jsonify({'success': False, 'message': '该用户已是老师'})
    
    # 添加授权
    db.execute('INSERT INTO teacher_auth (username, granted_by, granted_at) VALUES (?, ?, ?)',
             (username, session['username'], datetime.now().isoformat()))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': f'已授权 {username} 为老师'})

# 删除老师
@app.route('/api/teacher/remove_teacher', methods=['POST'])
def api_remove_teacher():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    data = request.json
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'success': False, 'message': '请输入用户名'})
    
    # 不能删除自己
    if username == session['username']:
        return jsonify({'success': False, 'message': '不能取消自己的老师权限'})
    
    db = get_db()
    db.execute('DELETE FROM teacher_auth WHERE username = ?', (username,))
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': f'已取消 {username} 的老师权限'})

# ============== 题库浏览功能 ==============

# 网格数据分析
@app.route('/api/teacher/grid_analysis')
def api_grid_analysis():
    if 'user_id' not in session or session['role'] != 'teacher':
        return jsonify({'success': False, 'message': '权限不足'})
    
    db = get_db()
    
    # 获取所有网格
    grids = ['白洋湾', '金阊', '虎丘', '平江', '苏锦', '沧浪', '双塔', '吴门桥', '后台']
    
    analysis = []
    for grid in grids:
        # 学员数
        db.execute('SELECT COUNT(*) as count FROM users WHERE grid = ? AND role = ?', (grid, 'student'))
        student_count = db.fetchone()['count']
        
        # 答题总数
        db.execute('''
            SELECT COUNT(*) as count FROM answer_records ar
            JOIN users u ON ar.user_id = u.id
            WHERE u.grid = ?
        ''', (grid,))
        answer_count = db.fetchone()['count'] or 0
        
        # 正确数
        db.execute('''
            SELECT COUNT(*) as count FROM answer_records ar
            JOIN users u ON ar.user_id = u.id
            WHERE u.grid = ? AND ar.is_correct = 1
        ''', (grid,))
        correct_count = db.fetchone()['count'] or 0
        
        # 考试次数
        db.execute('''
            SELECT COUNT(*) as count FROM exam_records e
            JOIN users u ON e.user_id = u.id
            WHERE u.grid = ?
        ''', (grid,))
        exam_count = db.fetchone()['count'] or 0
        
        # 计算正确率
        correct_rate = round((correct_count / answer_count * 100), 1) if answer_count > 0 else 0
        
        analysis.append({
            'grid': grid,
            'studentCount': student_count,
            'answerCount': answer_count,
            'correctCount': correct_count,
            'correctRate': correct_rate,
            'examCount': exam_count
        })
    
    db.close()
    
    return jsonify({
        'success': True,
        'data': analysis
    })

# 获取题库列表（支持搜索和筛选）
@app.route('/api/questions/browse')
def api_questions_browse():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': '请先登录'})
    
    # 加载题库
    try:
        with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
            all_questions = json.load(f)
    except:
        return jsonify({'success': False, 'message': '加载题库失败'})
    
    # 获取筛选参数
    question_type = request.args.get('type', 'all')
    keyword = request.args.get('keyword', '').strip()
    question_id = request.args.get('id', '').strip()
    page = request.args.get('page', '1', type=int)  # 页码（每组 100 题）
    
    filtered = all_questions
    
    # 按题型筛选
    if question_type != 'all':
        filtered = [q for q in filtered if q['type'] == question_type]
    
    # 按关键字搜索
    if keyword:
        filtered = [q for q in filtered if keyword.lower() in q['content'].lower()]
    
    # 按序号搜索
    if question_id:
        filtered = [q for q in filtered if q['id'] == question_id]
    
    # 计算总数
    total = len(filtered)
    
    # 分页（每组 100 条）
    page_size = 100
    total_pages = (total + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    filtered = filtered[start_idx:end_idx]
    
    # 返回题目
    questions = []
    for q in filtered:
        questions.append({
            'id': q['id'],
            'content': q['content'],
            'type': q['type'],
            'options': q.get('options', {}),
            'answer': q['answer']
        })
    
    return jsonify({
        'success': True,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'questions': questions
    })

if __name__ == '__main__':
    print("✨ 智慧家庭题库系统 - 专业版启动中...")
    port = int(os.environ.get('PORT', 5002))
    print(f"🌐 服务运行在端口 {port}")
    print("🚀 服务运行中...")
    app.run(debug=False, host='0.0.0.0', port=port, threaded=True)
