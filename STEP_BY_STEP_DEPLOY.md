# 🚀 一步步部署指南

## 第一步：部署后端到Railway（5分钟）

### 1.1 打开Railway
- 访问：https://railway.app
- 点击 **"Login"** 用GitHub账号登录

### 1.2 创建新项目
- 点击 **"New Project"**
- 选择 **"Deploy from GitHub repo"**
- 授权Railway访问你的GitHub（如果还没授权）

### 1.3 选择仓库
- 找到并选择 **"lesley4373/youtube-transcriber"**
- Railway会自动检测到这是Python项目

### 1.4 配置部署
- Railway会自动开始部署
- 等待3-5分钟构建完成
- **重要**：记住你的后端URL！

✅ **完成标志**：看到绿色的"Active"状态和一个URL链接

---

## 第二步：部署前端到Vercel（3分钟）

### 2.1 打开Vercel
- 访问：https://vercel.com
- 点击 **"Login"** 用GitHub账号登录

### 2.2 创建新项目
- 点击 **"New Project"**
- 导入 **"lesley4373/youtube-transcriber"**

### 2.3 配置环境变量（关键步骤！）
**在部署前**，点击 **"Environment Variables"**：
- **Name**: `REACT_APP_API_URL`
- **Value**: `https://你的railway后端URL` （第一步得到的URL）

### 2.4 开始部署
- 点击 **"Deploy"**
- 等待2-3分钟构建完成

✅ **完成标志**：看到"Deployment completed"和一个前端URL

---

## 第三步：测试部署（2分钟）

### 3.1 基础测试
1. 打开你的Vercel前端URL
2. 界面应该正常显示
3. 输入一个短YouTube视频链接（建议1-3分钟的视频）

### 3.2 功能测试
推荐测试视频：
- `https://www.youtube.com/watch?v=dQw4w9WgXcQ` (经典短视频)
- `https://youtu.be/jNQXAC9IVRw` (Me at the zoo - YouTube第一个视频)

### 3.3 成功标志
- ✅ 视频开始处理（显示"Processing..."）
- ✅ 几分钟后显示转写结果
- ✅ 显示中英双语对照
- ✅ 有时间戳

---

## 🆘 故障排除

### 如果前端显示API错误：
1. 检查环境变量 `REACT_APP_API_URL` 是否正确
2. 确保Railway后端URL可以访问
3. 重新部署前端

### 如果转写失败：
1. 尝试更短的视频（<5分钟）
2. 检查YouTube链接是否有效
3. 等待几分钟重试

---

## 🎉 部署完成检查清单

- [ ] Railway后端部署成功（有绿色Active状态）
- [ ] Vercel前端部署成功（有部署URL）
- [ ] 环境变量配置正确
- [ ] 可以访问前端界面
- [ ] 转写功能正常工作

**你的应用地址**：
- 🌐 **前端**：`https://你的应用名.vercel.app`
- 🔧 **后端**：`https://你的应用名.railway.app`

## 📱 分享给朋友
部署完成后，直接把前端URL发给朋友就可以了！全世界任何人都能使用。