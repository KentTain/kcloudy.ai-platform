# Docker 部署配置

本目录包含 AI Platform 项目的 Docker Compose 部署配置和 Nginx 反向代理配置。

## 目录结构

```text
docker/
├── .env                              # 环境变量配置（敏感信息，不提交）
├── docker-compose.infrastructure.yml # 基础设施服务
├── docker-compose.backend.yml        # 后端服务
├── docker-compose.frontend.yml       # 前端服务
└── nginx/                            # Nginx 配置文件
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

## 快速开始

### 1. 环境准备

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（重要！修改默认密码）
vim .env
```

### 2. 启动服务

```bash
# 启动基础设施（数据库、缓存、对象存储等）
docker compose -f docker-compose.infrastructure.yml up -d

# 启动平台版（包含所有模块的前后端）
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  up -d

# 启动独立模块版
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  --profile standalone \
  up -d
```

### 3. 停止服务

```bash
# 停止所有服务
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  down

# 停止并删除数据卷
docker compose \
  -f docker-compose.infrastructure.yml \
  -f docker-compose.backend.yml \
  -f docker-compose.frontend.yml \
  down -v
```

## 服务组件

### 基础设施服务

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| nginx | kcloudy-nginx | 80, 443 | 反向代理 / HTTPS 网关 |
| postgres | kcloudy-postgres | 5432 | PostgreSQL 17 + pgvector |
| mysql | kcloudy-mysql | 3306 | MySQL 8.0 |
| sqlserver | kcloudy-sqlserver | 1433 | SQL Server 2019 |
| redis | kcloudy-redis | 6379 | Redis 7 缓存 |
| minio | kcloudy-minio | 9000, 9001 | MinIO 对象存储 |
| sandbox | kcloudy-sandbox | 8194 | 代码沙箱服务 (dify-sandbox) |
| nexus | kcloudy-nexus | 9090-9092 | Maven/Docker 私有仓库 |
| claude-code-hub | kcloudy-claude-hub | 23000 | Claude Code Hub |

### 后端服务

| 服务名 | 角色 | 端口 | 说明 |
|--------|------|------|------|
| backend-platform-api | web | 8000 | 平台版 Web API |
| backend-platform-task | task | - | 平台版定时任务调度器 |
| backend-platform-listener | listener | - | 平台版消息监听器 |
| backend-demo-api | web | 8010 | Demo 模块 API (standalone) |
| backend-iam-api | web | 8020 | IAM 模块 API (standalone) |
| backend-tenant-api | web | 8030 | Tenant 模块 API (standalone) |

### 前端服务

| 服务名 | 端口 | 模块 |
|--------|------|------|
| platform-app | 3000 | demo, iam, tenant |
| demo-app | 3010 | demo (standalone) |
| iam-app | 3020 | iam (standalone) |
| tenant-app | 3030 | tenant (standalone) |

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| POSTGRES_DB | init_project | PostgreSQL 数据库名 |
| POSTGRES_USER | postgres | PostgreSQL 用户名 |
| POSTGRES_PASSWORD | postgres | PostgreSQL 密码 |
| REDIS_PASSWORD | redis123 | Redis 密码 |
| MINIO_ROOT_USER | minio | MinIO 用户 |
| MINIO_ROOT_PASSWORD | minio123 | MinIO 密码 |
| DATABASE_URL | postgresql://... | 后端数据库连接 |
| REDIS_URL | redis://... | 后端 Redis 连接 |
| VERSION | latest | 镜像版本标签 |
| PLATFORM_PORT | 3000 | 平台版前端端口 |
| BACKEND_PORT | 8000 | 平台版后端端口 |

## Nginx 配置说明

### 配置文件结构

| 文件 | 说明 |
|------|------|
| snippets/ssl.conf | SSL 公共配置，被所有 HTTPS 站点引用 |
| snippets/error-pages.conf | 错误页面配置 |
| 00-default.conf | 默认服务器，捕获未匹配的请求 |
| 10-init-project.conf | AI Platform 前后端代理 |
| 20-infrastructure.conf | 基础设施服务代理（MinIO 等） |
| 30-ai-services.conf | AI 服务网关（Claude Code Hub、OpenClaw） |
| 40-k8s-master.conf | K8s Master 节点服务代理 |
| 50-k8s-work01.conf | K8s Work01 节点服务代理 |
| 60-k8s-work02.conf | K8s Work02 节点服务代理 |

### 域名代理映射

#### AI Platform 应用

| 域名 | 代理目标 | 说明 |
|------|----------|------|
| platform.kcloudy.com | platform-app + backend-platform-api | 平台版 |
| demo.kcloudy.com | demo-app + backend-demo-api | Demo 模块 |
| iam.kcloudy.com | iam-app + backend-iam-api | IAM 模块 |
| tenant.kcloudy.com | tenant-app + backend-tenant-api | Tenant 模块 |
| api.kcloudy.com | backend-platform-api | 平台版 API |
| demo-api.kcloudy.com | backend-demo-api | Demo API |
| iam-api.kcloudy.com | backend-iam-api | IAM API |
| tenant-api.kcloudy.com | backend-tenant-api | Tenant API |

#### 基础设施服务

| 域名 | 代理目标 | 说明 |
|------|----------|------|
| minio.kcloudy.com | minio:9001 | MinIO Console |
| minio-api.kcloudy.com | minio:9000 | MinIO S3 API |
| cc-hub.kcloudy.com | claude-code-hub:3000 | Claude Code Hub |

## 数据持久化

| 服务 | 卷名 | 容器路径 |
|------|------|----------|
| PostgreSQL | postgres_data | /var/lib/postgresql/data |
| MySQL | mysql_data | /var/lib/mysql |
| SQL Server | sqlserver_data | /var/opt/mssql |
| Redis | redis_data | /data |
| MinIO | minio_data | /data |
| Nexus | nexus_data | /nexus-data |

## 健康检查

以下服务配置了健康检查：

- **Nginx**: `nginx -t` 配置检查
- **PostgreSQL**: `pg_isready` 命令检查
- **MySQL**: `mysqladmin ping` 命令检查
- **Redis**: `redis-cli ping` 命令检查
- **MinIO**: HTTP 健康端点检查
- **后端 Web**: HTTP `/health` 端点检查
- **后端 Task/Listener**: 进程存活检查

## 网络配置

所有服务使用 `kcloudy-network` 桥接网络，容器间可通过服务名互相访问。

## 注意事项

1. **生产环境请修改所有默认密码**
2. `.env` 文件包含敏感信息，请确保不被提交到版本控制
3. SSL 证书需要放置在 `nginx/certs/` 目录
4. 数据卷路径在不同环境可能需要调整
