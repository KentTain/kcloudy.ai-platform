# CLAUDE.md

本文件为 Claude Code 在 docker/ 目录下工作时提供指导。

## 目录定位

`docker/` 目录包含项目的容器化部署配置，主要包括：

- Docker Compose 服务编排（拆分为基础设施、后端、前端三个文件）
- Nginx 反向代理配置
- 环境变量管理

## 文件结构

```text
docker/
├── .env                              # 环境变量（敏感，不提交）
├── docker-compose.infrastructure.yml # 基础设施服务
├── docker-compose.backend.yml        # 后端服务
├── docker-compose.frontend.yml       # 前端服务
└── nginx/
    ├── nginx.conf                    # 主配置
    ├── mime.types                    # MIME 类型定义
    ├── proxy_params                  # 通用代理参数
    ├── snippets/                     # 公共配置片段
    │   ├── ssl.conf                  # SSL 公共配置
    │   └── error-pages.conf          # 错误页面配置
    └── conf.d/                       # 站点配置目录
        ├── 00-default.conf           # 默认服务器配置
        ├── 10-init-project.conf      # AI Platform 应用网关
        ├── 20-infrastructure.conf    # 基础设施服务代理
        ├── 30-ai-services.conf       # AI 服务网关
        ├── 40-k8s-master.conf        # K8s Master 服务代理
        ├── 50-k8s-work01.conf        # K8s Work01 服务代理
        └── 60-k8s-work02.conf        # K8s Work02 服务代理
```

## 部署模式

### 平台版（默认）

```bash
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  up -d
```

### 独立模块版

```bash
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  --profile standalone \
  up -d
```

### 仅基础设施

```bash
docker compose -f docker-compose.infrastructure.yml up -d
```

## 工作规范

### 修改 Nginx 配置

1. 修改配置文件后，验证语法：

   ```bash
   docker exec kcloudy-nginx nginx -t
   ```

2. 重载配置（无需重启）：

   ```bash
   docker exec kcloudy-nginx nginx -s reload
   ```

### 添加新站点代理

在 `nginx/conf.d/` 创建新配置文件，使用数字前缀控制加载顺序：

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

    include /etc/nginx/snippets/ssl.conf;

    location / {
        proxy_pass http://target:port;
        include /etc/nginx/proxy_params;
    }
}
```

### 修改 Docker Compose

1. 修改后重新创建服务：

   ```bash
   docker compose \
     -f docker-compose.infrastructure.yml \
     -f docker-compose.backend.yml \
     -f docker-compose.frontend.yml \
     up -d --force-recreate <service>
   ```

2. 添加新服务时，确保：
   - 加入 `kcloudy-network` 网络
   - 配置健康检查（数据库类服务）
   - 使用 `.env` 变量管理敏感信息

### 环境变量管理

- 所有密码、令牌等敏感信息放在 `.env` 文件
- 使用 `${VAR:-default}` 语法提供默认值
- 新增变量时更新 `.env.example` 模板

## 服务依赖关系

```text
claude-code-hub
├── depends_on: postgres (healthy)
└── depends_on: redis (healthy)

后端服务
├── depends_on: postgres (healthy)
└── depends_on: redis (healthy)

前端服务
└── depends_on: 后端服务 (healthy)

sandbox (代码沙箱)
└── 用于 code_executor 组件执行不受信任的代码
```

## 新增服务说明

### Sandbox 服务（代码沙箱）

用于 `ai.components.code_executor` 组件，提供安全的代码执行环境。

**服务配置**：
- 镜像：`langgenius/dify-sandbox:0.2.12`
- 容器名：`kcloudy-sandbox`
- 端口：`8194`（可通过 `SANDBOX_PORT` 环境变量配置）
- 网络：`kcloudy-network`

**使用场景**：
- 执行用户提供的 Python3 代码
- 执行 JavaScript 代码
- 执行 Jinja2 模板渲染

**安全特性**：

- 隔离的执行环境
- 资源限制（CPU、内存、执行时间）
- 网络隔离

**启动命令**：

```bash
docker compose -f docker-compose.backend.yml up -d sandbox
```

## 常用操作

```bash
# 查看服务状态
docker compose -f docker-compose.infrastructure.yml ps

# 查看特定服务日志
docker compose -f docker-compose.infrastructure.yml logs -f nginx

# 进入容器调试
docker exec -it kcloudy-nginx sh

# 重启单个服务
docker compose -f docker-compose.infrastructure.yml restart nginx

# 完全重建服务
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  up -d --build --force-recreate <service>
```

## 注意事项

- 不要提交 `.env` 文件到版本控制
- 生产环境部署前检查所有默认密码
- Nginx 证书路径需与宿主机挂载一致
- 数据卷路径在不同环境可能需要调整
