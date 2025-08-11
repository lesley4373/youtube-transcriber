# YouTube Transcriber 部署指南

## 🌐 让其他人访问您的应用

### 方法1：局域网访问（最简单）
同一WiFi网络下的用户可以直接访问：
- 访问地址：http://192.168.8.3:3000
- 确保防火墙允许3000和8000端口

### 方法2：使用 Cloudflared Tunnel（推荐）
```bash
# 安装 cloudflared
brew install cloudflared

# 启动隧道（无需注册）
cloudflared tunnel --url http://localhost:3000
```

### 方法3：使用 LocalTunnel
```bash
# 安装
npm install -g localtunnel

# 启动隧道
lt --port 3000 --subdomain youtube-transcriber
# 将获得类似: https://youtube-transcriber.loca.lt
```

### 方法4：使用 Serveo（无需安装）
```bash
ssh -R 80:localhost:3000 serveo.net
```

### 方法5：部署到云服务（永久方案）

#### Render.com（免费）
1. 创建 Dockerfile：
```dockerfile
# 后端 Dockerfile
FROM python:3.9
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y ffmpeg
COPY backend/ .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

2. 推送到GitHub
3. 在 Render.com 创建Web Service
4. 连接GitHub仓库并部署

#### Railway.app（简单快速）
```bash
# 安装 Railway CLI
npm install -g @railway/cli

# 登录并部署
railway login
railway init
railway up
```

#### Vercel（前端）+ Deta/Supabase（后端）
- 前端部署到 Vercel
- 后端部署到 Deta Space 或 Supabase Functions

### 方法6：使用 Docker Compose 一键部署

创建 `docker-compose.yml`：
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000
```

运行：
```bash
docker-compose up -d
```

## 🔒 安全建议

1. **添加认证**：在生产环境中添加用户认证
2. **限制速率**：防止滥用，添加请求限制
3. **HTTPS**：使用SSL证书确保安全传输
4. **API密钥**：保护后端API，添加密钥验证

## 📱 移动端适配

应用已经响应式设计，手机用户可以直接访问使用。

## 💡 快速测试

最快的方式是使用 Cloudflared：
```bash
# 前端隧道
cloudflared tunnel --url http://localhost:3000

# 获得类似：https://xxx-xxx.trycloudflare.com
```

分享这个链接给朋友即可！