#!/bin/sh
set -e

# 替换 nginx 配置中的环境变量
envsubst "$BACKEND_API_URL" < /etc/nginx/templates/default.conf.template > /etc/nginx/conf.d/default.conf

# 启动 nginx
exec nginx -g "daemon off;"
