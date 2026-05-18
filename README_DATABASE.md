# 📊 数据库配置指南

## ⚠️ 重要：数据持久化

默认使用 SQLite 时，**Render 每次重启会清空数据**！  
必须配置 PostgreSQL 才能永久保存学员数据。

## 🎯 推荐：使用 Neon（免费 PostgreSQL）

### 第 1 步：创建 Neon 账户

1. 访问 https://neon.tech
2. 点击 **Sign Up**（可用 GitHub 登录）
3. 免费计划：
   - ✅ 0.5 GB 存储
   - ✅ 无限数据库
   - ✅ 无需信用卡

### 第 2 步：创建数据库

1. 点击 **New Project**
2. 填写：
   - **Project name**: `quiz-app-db`
   - **Region**: 选离中国近的（如 `AWS ap-northeast-1` 东京）
3. 点击 **Create project**

### 第 3 步：获取连接字符串

在项目页面：
1. 找到 **Connection Details**
2. 选择 **Pooled connection**
3. 复制连接字符串，格式类似：
   ```
   postgresql://username:password@xxx-xxx.ap-northeast-1.aws.neon.tech/quizdb?sslmode=require
   ```

### 第 4 步：配置到 Render

1. 登录 https://render.com
2. 进入 **quiz-app-pro** Web Service
3. 点击 **Environment** 标签
4. 点击 **Add Environment Variable**
5. 填写：
   - **Key**: `DATABASE_URL`
   - **Value**: 从 Neon 复制的连接字符串
6. 点击 **Save Changes**

Render 会自动重新部署，之后数据就会永久保存！

---

## 🧪 验证配置

部署完成后，访问你的应用：
1. 登录一个学员账号
2. 做几道题
3. 刷新页面或重新登录
4. 检查学习记录是否还在 ✅

---

## 📋 其他 PostgreSQL 提供商

| 服务商 | 免费额度 | 网址 |
|--------|----------|------|
| Neon | 0.5GB 存储 | https://neon.tech |
| Supabase | 500MB | https://supabase.com |
| Aiven | $300 额度 | https://aiven.io |
| Railway | $5 额度 | https://railway.app |

---

## 🛠️ 本地测试

如果需要本地测试 PostgreSQL：

```bash
# 安装 PostgreSQL（Mac）
brew install postgresql@15
brew services start postgresql@15

# 创建数据库
createdb quiz_app

# 设置环境变量
export DATABASE_URL=postgresql://localhost/quiz_app

# 运行应用
python3 app.py
```
