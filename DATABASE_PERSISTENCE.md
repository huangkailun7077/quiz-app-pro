# 📦 数据库持久化方案

## 问题诊断

当前使用 SQLite 本地文件存储 (`quiz.db`)，但 Render 免费版使用**临时文件系统**：
- ❌ 每次部署后数据清空
- ❌ 应用重启后数据丢失
- ❌ 无法长期保存学员学习记录

## 解决方案（三选一）

### 方案一：Neon PostgreSQL（推荐⭐⭐⭐⭐⭐）
**免费、无限存储、适合长期运行**

1. 访问 https://neon.tech 注册免费账号
2. 创建新数据库项目
3. 获取连接字符串（Connection String）
4. 在 Render 环境变量中添加：
   ```
   DATABASE_URL=postgresql://user:password@xxx.neon.tech/dbname?sslmode=require
   ```

**优点**：
- ✅ 完全免费
- ✅ 无限存储
- ✅ 自动备份
- ✅ 数据永久保存

**修改代码**：
```python
# app.py 顶部修改
import os
from urllib.parse import urlparse

# 检测是否使用 PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # 使用 PostgreSQL
    import psycopg2
    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
else:
    # 使用 SQLite（本地开发）
    def get_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
```

---

### 方案二：Railway PostgreSQL（备选⭐⭐⭐⭐）
**免费、$5/月升级选项**

1. 访问 https://railway.app 注册
2. 创建 PostgreSQL 数据库
3. 获取连接字符串
4. 在 Render 添加环境变量 `DATABASE_URL`

---

### 方案三：本地备份脚本（临时方案⭐⭐）
**适合短期使用，需要手动操作**

创建定时备份脚本，将数据库导出到外部存储：

```bash
# backup.sh
#!/bin/bash
# 每天备份数据库到 GitHub Gist 或其他云存储
cp quiz.db quiz_backup_$(date +%Y%m%d).db
# 上传到云存储...
```

---

## 推荐实施步骤（Neon PostgreSQL）

### 1. 创建 Neon 数据库（5 分钟）
1. 访问 https://neon.tech
2. 使用 GitHub 账号登录
3. 点击 "New Project"
4. 输入项目名称：`quiz-app-db`
5. 点击 "Create"

### 2. 获取连接字符串
1. 在 Dashboard 点击 "Connection Details"
2. 复制连接字符串（类似）：
   ```
   postgresql://quiz-app-db-user:xxx@ep-xxx.xxx.neon.tech/quiz-app-db?sslmode=require
   ```

### 3. 在 Render 设置环境变量
1. 访问 https://render.com/dashboard
2. 选择 `quiz-app-pro` 服务
3. 点击 "Environment"
4. 添加变量：
   - Key: `DATABASE_URL`
   - Value: `postgresql://...`（刚才复制的连接字符串）
5. 点击 "Save Changes"

### 4. 更新代码（我来完成）
- 修改 `app.py` 支持 PostgreSQL
- 添加 `psycopg2` 到 `requirements.txt`
- 更新数据库初始化逻辑

### 5. 部署测试
- 推送代码到 GitHub
- 等待 Render 自动部署
- 测试学员登录、答题、考试
- 验证数据持久化

---

## 数据迁移（如果需要）

如果已有学员数据，需要导出并导入到新数据库：

```bash
# 导出 SQLite 数据
sqlite3 quiz.db .dump > backup.sql

# 导入到 PostgreSQL
psql "$DATABASE_URL" < backup.sql
```

---

## 联系支持

如需帮助，请联系：
- Neon 支持：https://neon.tech/docs
- Render 支持：https://render.com/docs
