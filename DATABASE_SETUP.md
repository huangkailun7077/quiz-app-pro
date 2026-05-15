# 📦 数据库持久化配置指南

## 问题说明

当前系统使用 SQLite 本地文件存储数据，但 Render 免费版使用**临时文件系统**：
- ❌ 每次部署后数据清空
- ❌ 应用重启后数据丢失
- ❌ 无法长期保存学员学习记录

## 解决方案：使用 Neon PostgreSQL（免费）

### 第一步：创建 Neon 数据库（5 分钟）

1. **访问** https://neon.tech
2. **登录**：使用 GitHub 账号
3. **创建项目**：
   - 点击 "New Project"
   - 项目名称：`quiz-app-db`
   - 点击 "Create"

### 第二步：获取数据库连接字符串

1. 在 Neon Dashboard 点击 **"Connection Details"**
2. 选择 **"Pooled connection"**
3. 复制连接字符串，格式类似：
   ```
   postgresql://quiz-app_user:xxx@ep-xxx.xxx.neon.tech/quiz-app?sslmode=require
   ```

### 第三步：在 Render 设置环境变量

1. 访问 https://render.com/dashboard
2. 选择 `quiz-app-pro` 服务
3. 点击左侧 **"Environment"**
4. 点击 **"Add Environment Variable"**
5. 添加：
   - **Key**: `DATABASE_URL`
   - **Value**: `postgresql://...`（刚才复制的完整连接字符串）
6. 点击 **"Save Changes"**

### 第四步：部署代码

系统会自动检测 `DATABASE_URL` 环境变量：
- ✅ 如果存在 → 使用 PostgreSQL（持久化）
- ✅ 如果不存在 → 使用 SQLite（本地开发）

### 第五步：验证

1. 等待 Render 完成部署（2-3 分钟）
2. 访问 https://quiz-app-pro.onrender.com
3. 学员登录 → 答题 → 考试
4. 刷新页面 → 数据应该还在！
5. 老师后台 → 查看学员数据

---

## 技术说明

### 数据库表结构

系统会自动创建以下表（首次运行时）：

1. **users** - 用户信息
2. **teacher_auth** - 老师授权
3. **answer_records** - 答题记录（保留 30 天）
4. **exam_records** - 考试记录（保留 30 天）
5. **practice_records** - 刷题记录（保留 30 天）
6. **wrong_questions** - 错题本（永久保留）
7. **favorite_questions** - 收藏题目（永久保留）

### 数据保留策略

- **答题/考试/刷题记录**：自动保留 30 天
- **错题本**：永久保留，直到学员手动清除
- **收藏题目**：永久保留
- **用户账号**：永久保留

### 自动清理

系统会在每次启动时自动清理 30 天前的临时记录，保持数据库精简。

---

## 常见问题

### Q: Neon 免费版的限制？
A: 
- ✅ 0.5GB 存储（足够 10 万 + 条记录）
- ✅ 自动休眠（15 分钟无活动）
- ✅ 唤醒时间 1-2 秒
- ✅ 完全免费，无需信用卡

### Q: 数据会丢失吗？
A: 
- ✅ Neon 自动备份，数据永久保存
- ✅ 即使 Render 部署失败，数据也安全
- ✅ 可导出完整数据库备份

### Q: 如何备份数据？
A: 
在 Neon Dashboard 可下载 SQL 备份，或使用：
```bash
pg_dump "$DATABASE_URL" > backup.sql
```

### Q: 可以迁移到其他数据库吗？
A: 
可以！支持：
- PostgreSQL（任何服务商）
- SQLite（本地开发）
- 未来可添加 MySQL/MariaDB 支持

---

## 联系支持

- Neon 文档：https://neon.tech/docs
- Render 文档：https://render.com/docs
- 项目问题：GitHub Issues

---

**配置完成后，学员数据将永久保存！** ✨
