# Demo Frontend Dockerfile
# 基于 nginx:alpine 镜像，提供静态资源服务

FROM nginx:alpine

# 安装 gettext 用于 envsubst
RUN apk add --no-cache gettext

# 移除默认 nginx 配置
RUN rm -rf /etc/nginx/conf.d/default.conf

# 复制 nginx 配置模板
COPY nginx.conf /etc/nginx/templates/default.conf.template

# 复制本地已构建好的应用
COPY dist /usr/share/nginx/html

# 复制入口脚本
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# 暴露 80 端口
EXPOSE 80

# 设置默认后端 API URL（可在运行时覆盖）
ENV BACKEND_API_URL=http://localhost:8000

# 使用入口脚本
ENTRYPOINT ["/docker-entrypoint.sh"]
