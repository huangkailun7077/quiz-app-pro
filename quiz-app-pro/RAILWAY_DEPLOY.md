# 🚀 Railway 部署指南

## 部署步骤

### 1️⃣ 访问 Railway

打开链接：https://railway.app

### 2️⃣ 注册/登录

- 使用 GitHub 账号登录（推荐）
- 或使用邮箱注册

### 3️⃣ 创建新项目

1. 点击 **"New Project"**
2. 选择 **"Deploy from GitHub repo"**
3. 授权 Railway 访问你的 GitHub
4. 选择 `quiz-app-pro` 仓库

### 4️⃣ 配置环境变量

在 Railway 项目设置中添加：

```
FLASK_ENV=production
FLASK_SECRET_KEY=xiaoling_quiz_system_2026_secret_key
```

### 5️⃣ 部署

- Railway 会自动检测 Python 项目
- 自动安装依赖（requirements.txt）
- 自动启动服务（Procfile）

### 6️⃣ 获取链接

部署完成后，Railway 会生成：
- `https://your-project-name.railway.app`

### 7️⃣ 自定义域名（可选）

在 Railway 设置中可以绑定自己的域名

---

## 📱 分享给学员

部署完成后，将 Railway 生成的链接发送给学员即可！

- ✅ 24 小时在线
- ✅ 任何网络都可访问
- ✅ 无需电脑开机
- ✅ 自动 HTTPS

---

## 🔄 更新代码

推送代码到 GitHub 后，Railway 会自动重新部署。

---

## 💰 费用

- Railway 免费额度：$5/月
- 本应用预计消耗：$2-5/月
- 足够 100+ 学员使用

---

**中移铁通 ✨ 智慧家庭题库**
