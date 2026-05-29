# Docker 部署配置

本目录包含 InitProject 项目的 Docker Compose 部署配置和 Nginx 反向代理配置。

## 目录结构

```text
docker/
├── .env                    # 环境变量配置（敏感信息，已忽略）
├── docker-compose.yml      # Docker Compose 编排文件（基础设施服务）
├── readme.md               # 本文档
├── claude.md               # Claude Code 指导文档
└── nginx/                  # Nginx 配置文件
    ├── nginx.conf          # Nginx 主配置
    ├── mime.types          # MIME 类型定义
    ├── proxy_params        # 通用代理参数
    └── conf.d/             # 站点配置目录
        ├── default.conf       # 默认服务器配置（HTTPS 捕获）
        ├── custom.conf        # K8s 集群服务代理配置
        ├── cc-hub.conf        # Claude Code Hub 网关
        ├── openclaw.conf      # OpenClaw 网关
        └── infrastructure.conf # 基础设施服务代理配置
```

## 多模块部署

项目支持多模块独立部署，配置文件位于项目根目录的 `docker-compose.yml`。

### 部署架构

```
部署模式：
├── 平台版 (platform.example.com:3000)
│   └── 包含所有模块 (demo, iam, tenant)
│
└── 独立模块版
    ├── demo.example.com:3001 → Demo 模块
    ├── iam.example.com:3002 → IAM 模块
    └── tenant.example.com:3003 → Tenant 模块
```

### 快速开始

```bash
# 1. 复制环境变量模板
cp web/vue/.env.docker .env

# 2. 启动平台版（包含所有模块）
docker-compose up -d

# 3. 查看日志
docker-compose logs -f platform-app
```

### 独立模块部署

```bash
# 启动 Demo 模块独立部署
docker-compose --profile standalone up -d demo-app

# 启动 IAM 模块独立部署
docker-compose --profile standalone up -d iam-app

# 启动 Tenant 模块独立部署
docker-compose --profile standalone up -d tenant-app

# 启动所有独立模块
docker-compose --profile standalone up -d
```

### 构建命令

```bash
# 构建平台版镜像
docker-compose build platform-app

# 构建指定模块镜像
docker-compose build demo-app

# 使用自定义模块组合构建
docker build \
  --build-arg BUILD_MODULES=demo,iam \
  -t init-project-custom \
  ./web/vue
```

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| VERSION | latest | 镜像版本标签 |
| PLATFORM_PORT | 3000 | 平台版端口 |
| DEMO_PORT | 3001 | Demo 模块端口 |
| IAM_PORT | 3002 | IAM 模块端口 |
| TENANT_PORT | 3003 | Tenant 模块端口 |
| BACKEND_PORT | 8000 | 后端服务端口 |
| POSTGRES_DB | init_project | PostgreSQL 数据库名 |
| POSTGRES_USER | postgres | PostgreSQL 用户名 |
| POSTGRES_PASSWORD | postgres | PostgreSQL 密码 |
| REDIS_PASSWORD | redis123 | Redis 密码 |
| VITE_API_BASE_URL | /api | API 基础路径 |

## 服务组件

| 服务 | 容器名 | 端口 | 说明 |
|------|--------|------|------|
| nginx | mynginx | 80, 443 | 反向代理 / HTTPS 网关 |
| nexus | nexus | 9090-9092 | Maven/Docker 私有仓库 |
| mysql | mysql-db | 3306 | MySQL 8.0 数据库 |
| sqlserver | sqlserver-db | 1433 | SQL Server 2019 |
| postgres | pgvector-db | 5432 | PostgreSQL 17 + pgvector |
| redis | redis-cache | 6379 | Redis 7 缓存 |
| minio | minio-storage | 9000, 9001 | MinIO 对象存储 |
| claude-app | claude-code-hub | 23000 | Claude Code Hub |

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
# 启动所有服务
docker-compose up -d

# 启动特定服务
docker-compose up -d nginx postgres redis

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f <service_name>
```

### 3. 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

## 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `NEXUS_ADMIN_USERNAME` | administrator | Nexus 管理员用户名 |
| `NEXUS_ADMIN_PASSWORD` | - | Nexus 管理员密码 |
| `MYSQL_ROOT_PASSWORD` | - | MySQL root 密码 |
| `MYSQL_DATABASE` | alon_demo | 默认数据库 |
| `MYSQL_USER` | mysql_admin | MySQL 用户 |
| `MYSQL_PASSWORD` | - | MySQL 用户密码 |
| `MSSQL_SA_PASSWORD` | - | SQL Server SA 密码 |
| `POSTGRES_DB` | alon_demo | PostgreSQL 数据库 |
| `POSTGRES_USER` | admin | PostgreSQL 用户 |
| `POSTGRES_PASSWORD` | - | PostgreSQL 密码 |
| `REDIS_PASSWORD` | - | Redis 密码 |
| `MINIO_ROOT_USER` | admin | MinIO 用户 |
| `MINIO_ROOT_PASSWORD` | - | MinIO 密码 |
| `CC_ADMIN_TOKEN` | - | Claude Code Hub 管理令牌 |
| `APP_PORT` | 23000 | Claude Code Hub 端口 |

## Nginx 配置说明

### 域名代理映射

Nginx 配置支持以下子域名代理：

#### 应用服务

| 域名模式 | 代理目标 | 说明 |
|----------|----------|------|
| `cc-hub.kcloudy.com` | localhost:23000 | Claude Code Hub |
| `claw.kcloudy.com` | localhost:18789 | OpenClaw Gateway |
| `nexus.kcloudy.com` | K8s-Master:9090 | Nexus 仓库 |
| `sso.kcloudy.com` | K8s-Master:1001 | SSO 服务 |
| `admin.kcloudy.com` | K8s-Master:1003 | 管理后台 |
| `*.cfg.kcloudy.com` | K8s-Work01:1101 | 配置服务 |
| `*.app.kcloudy.com` | K8s-Work01:1105 | 应用服务 |
| `*.acc.kcloudy.com` | K8s-Work02:2001 | 账户服务 |
| `*.doc.kcloudy.com` | K8s-Work02:2005 | 文档服务 |

#### 基础设施服务

| 域名 | 代理目标 | 说明 |
|------|----------|------|
| `minio.kcloudy.com` | localhost:9001 | MinIO Console 管理界面 |
| `minio-api.kcloudy.com` | localhost:9000 | MinIO S3 API |
| `pgadmin.kcloudy.com` | localhost:5050 | pgAdmin (需部署) |
| `redis.kcloudy.com` | localhost:8081 | Redis Commander (需部署) |
| `mysql.kcloudy.com` | localhost:8080 | Adminer/phpMyAdmin (需部署) |
| `mssql.kcloudy.com` | localhost:8082 | SQL Server Admin (需部署) |

> **注意**: 数据库管理工具（pgAdmin、Redis Commander、Adminer）需要单独部署后才能使用对应域名。

### HTTPS 配置

- SSL 证书路径：`/etc/nginx/certs/fullchain.pem`
- 私钥路径：`/etc/nginx/certs/privkey.pem`
- 协议：TLS 1.2 / TLS 1.3
- 自动 HTTP 到 HTTPS 重定向
- HSTS 安全头已启用

## 数据持久化

服务数据存储在以下目录：

| 服务 | 宿主机路径 | 容器路径 |
|------|------------|----------|
| MySQL | `/share/k8s-master/mysql/` | `/var/lib/mysql` |
| PostgreSQL | `./data/postgres` | `/var/lib/postgresql/data` |
| Redis | `./data/redis` | `/data` |
| MinIO | `./data/minio` | `/data` |
| Nexus | `/share/k8s-master/data/nexus/` | `/nexus-data` |
| Nginx | `/share/k8s-master/nginx/` | `/etc/nginx` |

## 健康检查

以下服务配置了健康检查：

- **PostgreSQL**: `pg_isready` 命令检查
- **Redis**: `redis-cli ping` 检查
- **MinIO**: HTTP 健康端点检查

## 网络配置

所有服务使用 `alon-network` 桥接网络，容器间可通过服务名互相访问。

## 注意事项

1. **生产环境请修改所有默认密码**
2. `.env` 文件包含敏感信息，请确保不被提交到版本控制
3. SSL 证书需要放置在正确的位置
4. 数据卷映射需要确保宿主机目录存在并有正确权限

## License

Copyright © 2025 Moles. All Rights Reserved.
