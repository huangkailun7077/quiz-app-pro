# 📚 智慧家庭题库系统 - 专业版

小灵 ✨ 出品

## ✨ 功能特点

### 学员端
- 👤 用户名登录（无需密码）
- 📖 顺序刷题、随机刷题、错题集
- ⏱️ 模拟考试
- 📊 实时查看学习统计
- 💾 数据自动保存到云端

### 老师端
- 👩‍🏫 老师后台管理
- 📊 查看所有学员学习情况
- 📥 **一键导出 Excel**（含答题数、正确率、考试记录等）
- 📈 学员详细数据分析

## 🚀 本地运行

### 1. 安装依赖

```bash
cd quiz-app-pro
pip3 install -r requirements.txt
```

### 2. 启动服务

```bash
python3 app.py
```

### 3. 访问系统

- **首页/登录**：http://localhost:5000
- **学员登录**：输入任意用户名（如：张三）
- **老师登录**：选择"老师"角色，输入用户名（如：老师）

## 🌐 部署到 Railway（免费）

### 步骤 1：创建 GitHub 仓库

1. 把 `quiz-app-pro` 文件夹上传到 GitHub
2. 确保包含：`app.py`、`requirements.txt`、`templates/`、`static/`、`questions.json`

### 步骤 2：部署到 Railway

1. 访问 https://railway.app
2. 点击 **New Project**
3. 选择 **Deploy from GitHub repo**
4. 选择你的仓库
5. Railway 会自动识别 Python 并部署

### 步骤 3：获取链接

部署完成后，Railway 会给你一个链接：
```
https://your-app-production.up.railway.app
```

分享给学员们即可使用！

## 📊 Excel 导出说明

老师登录后，点击"📥 导出 Excel"，会下载一个包含以下信息的表格：

| 学员名 | 注册时间 | 答题总数 | 正确数 | 正确率 | 考试次数 | 错题数 |
|--------|---------|---------|-------|-------|---------|-------|
| 张三   | 2026-05-13 | 150 | 120 | 80.0% | 5 | 30 |
| 李四   | 2026-05-13 | 200 | 170 | 85.0% | 8 | 25 |
| **总计** | - | 350 | 290 | 82.9% | 13 | 55 |

## 📁 文件结构

```
quiz-app-pro/
├── app.py              # Flask 后端
├── requirements.txt    # Python 依赖
├── questions.json      # 题库数据
├── quiz.db            # SQLite 数据库（自动创建）
├── templates/         # HTML 模板
│   ├── login.html     # 登录页
│   ├── student.html   # 学员端
│   └── teacher.html   # 老师后台
└── static/            # 静态文件
    ├── student.js     # 学员端 JS
    └── questions.js   # 题库数据（JS 格式）
```

## 🔐 账号说明

- **学员账号**：首次登录自动创建，输入任意用户名即可
- **老师账号**：首次选择"老师"角色登录时自动创建

## 📝 注意事项

1. 数据库文件 `quiz.db` 会自动创建，无需手动操作
2. 所有数据保存在数据库，学员换设备也能看到自己的记录
3. Excel 导出功能需要老师登录才能使用

---

Created with ✨ by 小灵
