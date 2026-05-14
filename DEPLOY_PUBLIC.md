# 🌐 智慧家庭题库 - 公网部署指南

## 方案一：Cloudflare Tunnel（推荐⭐ 免费稳定）

### 步骤

1. **注册 Cloudflare 账号**
   - 访问 https://dash.cloudflare.com/sign-up
   - 免费注册账号

2. **安装 cloudflared**
   ```bash
   # macOS
   brew install cloudflared
   
   # 或手动下载
   # https://github.com/cloudflare/cloudflared/releases
   ```

3. **创建 Tunnel**
   ```bash
   # 登录 Cloudflare
   cloudflared tunnel login
   
   # 创建 tunnel
   cloudflared tunnel create quiz-app
   ```

4. **配置路由**
   ```bash
   cloudflared tunnel route dns quiz-app quiz.yourdomain.com
   ```

5. **运行 Tunnel**
   ```bash
   cloudflared tunnel run quiz-app --url http://localhost:5002
   ```

6. **分享链接**
   - 学员访问：`https://quiz.yourdomain.com`
   - 任何网络都可以访问！

---

## 方案二：ngrok（快速测试）

### 步骤

1. **注册 ngrok**
   - 访问 https://ngrok.com
   - 免费注册获取 authtoken

2. **安装 ngrok**
   ```bash
   brew install ngrok
   ```

3. **配置 token**
   ```bash
   ngrok config add-authtoken YOUR_TOKEN_HERE
   ```

4. **启动隧道**
   ```bash
   ngrok http 5002
   ```

5. **获取链接**
   - ngrok 会生成类似：`https://abc123.ngrok.io`
   - 分享给学员即可

⚠️ **注意**：免费版 ngrok 域名每次重启会变化

---

## 方案三：云服务器部署（永久稳定）

### 推荐配置
- 阿里云/腾讯云 轻量应用服务器
- 2 核 2G 足够
- 约 ¥60-100/月

### 部署步骤

1. **购买服务器**
   - 选择 Ubuntu 22.04
   - 开放端口：80, 443, 5002

2. **上传代码**
   ```bash
   scp -r quiz-app-pro root@your-server-ip:/opt/
   ```

3. **安装依赖**
   ```bash
   cd /opt/quiz-app-pro
   pip3 install flask pandas
   ```

4. **运行服务**
   ```bash
   # 使用 gunicorn 生产环境
   pip3 install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5002 app:app
   ```

5. **配置域名（可选）**
   - 购买域名
   - 解析到服务器 IP
   - 配置 Nginx 反向代理

---

## 方案四：内网穿透工具对比

| 工具 | 费用 | 稳定性 | 域名 | 推荐度 |
|------|------|--------|------|--------|
| Cloudflare Tunnel | 免费 | ⭐⭐⭐⭐⭐ | 自定义 | ⭐⭐⭐⭐⭐ |
| ngrok | 免费/付费 | ⭐⭐⭐ | 随机/固定 | ⭐⭐⭐ |
| frp | 免费 | ⭐⭐⭐⭐ | 自定义 | ⭐⭐⭐⭐ |
| 云服务器 | ¥60+/月 | ⭐⭐⭐⭐⭐ | 自定义 | ⭐⭐⭐⭐⭐ |

---

## 🚀 快速开始（推荐 Cloudflare）

如果你现在就要用，我推荐：

1. **临时测试**：用 ngrok，5 分钟搞定
2. **长期使用**：用 Cloudflare Tunnel 或云服务器

需要我帮你安装配置哪个方案？

---

## 📱 学员访问

部署完成后，学员可以：
- ✅ 在任何网络环境下访问
- ✅ 手机/电脑都可以
- ✅ 数据自动保存
- ✅ 无需安装 APP

---

**中移铁通 ✨ 智慧家庭题库**
