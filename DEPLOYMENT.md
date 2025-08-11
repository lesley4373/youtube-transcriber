# 🚀 部署指南

## GitHub开源部署步骤

### 1. 推送到GitHub

```bash
# 1. 在GitHub上创建新仓库 'youtube-transcriber'
# 2. 推送代码
git remote add origin https://github.com/yourusername/youtube-transcriber.git
git branch -M main
git push -u origin main
```

### 2. 后端部署（Railway.app）

1. 访问 [railway.app](https://railway.app)
2. 点击 "Start a New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择你的 youtube-transcriber 仓库
5. Railway会自动检测并部署后端

**获取后端URL**：部署完成后，Railway会提供一个URL，类似：
`https://your-app-name.railway.app`

### 3. 前端部署（Vercel）

1. 访问 [vercel.com](https://vercel.com)
2. 导入你的GitHub仓库
3. **重要**：设置环境变量
   - 名称：`REACT_APP_API_URL`
   - 值：`https://your-railway-backend-url.railway.app`

4. 点击Deploy

### 4. 更新前端API配置

在前端部署后，你需要更新 `src/App.js` 中的API URL：

```javascript
// 原来的动态配置
const host = window.location.hostname;
const apiUrl = `http://${host}:8000/transcribe`;

// 改为生产环境配置
const apiUrl = process.env.REACT_APP_API_URL 
  ? `${process.env.REACT_APP_API_URL}/transcribe`
  : `http://${window.location.hostname}:8000/transcribe`;
```

### 5. 替代部署方案

#### 方案A：Render.com（全栈）
- 后端：Render Web Service
- 前端：Render Static Site
- 优点：一个平台管理

#### 方案B：Netlify + Railway
- 前端：Netlify
- 后端：Railway
- 优点：Netlify有更好的CDN

#### 方案C：GitHub Pages + Heroku
- 前端：GitHub Pages
- 后端：Heroku
- 优点：完全免费

### 6. 环境变量配置

**后端环境变量**（Railway）：
```
PYTHONUNBUFFERED=1
PORT=8000
```

**前端环境变量**（Vercel）：
```
REACT_APP_API_URL=https://your-backend-url.railway.app
```

### 7. 自定义域名（可选）

1. **Vercel**：Project Settings → Domains → Add Domain
2. **Railway**：Project Settings → Custom Domain

### 8. 监控和日志

- **Railway**：Dashboard → Deployments → View Logs
- **Vercel**：Dashboard → Functions → View Function Logs

## 🎉 完成！

部署完成后，你的应用将在：
- **前端**：https://your-app.vercel.app
- **后端**：https://your-app.railway.app

任何人都可以访问和使用！

## 📞 故障排除

1. **CORS错误**：确保后端允许前端域名
2. **API连接失败**：检查环境变量配置
3. **构建失败**：查看构建日志，通常是依赖问题

## 💰 成本

- **Railway**：500小时/月免费
- **Vercel**：100GB带宽/月免费
- **总计**：完全免费！