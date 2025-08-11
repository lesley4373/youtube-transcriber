FROM node:18-alpine

WORKDIR /app

# 复制package.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源码
COPY . .

# 构建应用
RUN npm run build

# 使用nginx提供静态文件
FROM nginx:alpine
COPY --from=0 /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]