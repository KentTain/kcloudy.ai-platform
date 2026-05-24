# CLAUDE.md

本文件为 Claude Code 在 docker/ 目录下工作时提供指导。

## 目录定位

`docker/` 目录包含项目的容器化部署配置，主要包括：

- Docker Compose 服务编排
- Nginx 反向代理配置
- 环境变量管理

## 文件结构

```text
docker/
├── .env                    # 环境变量（敏感，不提交）
├── docker-compose.yml      # 服务编排
└── nginx/
    ├── nginx.conf          # 主配置
    ├── proxy_params        # 通用代理参数
    └── conf.d/             # 站点配置
        ├── default.conf    # 默认 HTTPS 服务器
        ├── custom.conf     # K8s 集群代理
        ├── cc-hub.conf     # Claude Code Hub
        └── openclaw.conf   # OpenClaw Gateway
```

## 工作规范

### 修改 Nginx 配置

1. 修改配置文件后，验证语法：
   ```bash
   docker exec mynginx nginx -t
   ```

2. 重载配置（无需重启）：
   ```bash
   docker exec mynginx nginx -s reload
   ```

### 修改 Docker Compose

1. 修改 `docker-compose.yml` 后，重新创建服务：
   ```bash
   docker-compose up -d --force-recreate <service>
   ```

2. 添加新服务时，确保：
   - 加入 `alon-network` 网络
   - 配置健康检查（数据库类服务）
   - 使用 `.env` 变量管理敏感信息

### 环境变量管理

- 所有密码、令牌等敏感信息放在 `.env` 文件
- 使用 `${VAR:-default}` 语法提供默认值
- 新增变量时更新 `.env.example` 模板

## 服务依赖关系

```text
claude-app (Claude Code Hub)
├── depends_on: postgres (healthy)
└── depends_on: redis (healthy)

其他服务无强制依赖，可独立启动。
```

## Nginx 配置模式

### 添加新站点代理

在 `nginx/conf.d/` 创建新配置文件：

```nginx
# HTTP 重定向
server {
    listen 80;
    server_name example.kcloudy.com;
    return 301 https://$host$request_uri;
}

# HTTPS 代理
server {
    listen 443 ssl http2;
    server_name example.kcloudy.com;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;
    # ... SSL 配置 ...

    location / {
        proxy_pass http://target:port;
        include /etc/nginx/proxy_params;
    }
}
```

### SSL 配置标准

所有 HTTPS 站点应包含：

- TLS 1.2/1.3 协议
- 现代加密套件
- HSTS 头
- 会话缓存配置

参考 `proxy_params` 和现有配置文件。

## 常用操作

```bash
# 查看服务状态
docker-compose ps

# 查看特定服务日志
docker-compose logs -f nginx

# 进入容器调试
docker exec -it <container> sh

# 重启单个服务
docker-compose restart <service>

# 完全重建服务
docker-compose up -d --build --force-recreate <service>
```

## 注意事项

- 不要提交 `.env` 文件到版本控制
- 生产环境部署前检查所有默认密码
- Nginx 证书路径需与宿主机挂载一致
- 数据卷路径在不同环境可能需要调整
