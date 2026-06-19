## 新增需求

### 需求:Docker Compose 支持平台版部署

系统必须提供 Docker Compose 配置，支持平台版（全模块）部署。

平台版部署必须：
- 包含前端平台服务
- 包含后端三个角色服务（api/task/listener）
- 配置服务依赖和网络
- 配置健康检查

#### 场景:启动平台版
- **当** 执行 `docker-compose up -d`
- **那么** 启动 platform-app, backend-platform-api, backend-platform-task, backend-platform-listener

#### 场景:平台版服务依赖
- **当** 启动平台版服务
- **那么** 后端服务等待 postgres 和 redis 健康检查通过

### 需求:Docker Compose 支持独立模块部署

系统必须支持独立模块部署，使用 Docker Compose profiles 特性。

独立模块部署必须：
- 使用 `profile: standalone` 标记
- 提供前端独立服务
- 提供后端独立服务
- 配置端口映射

#### 场景:启动 Demo 模块独立版
- **当** 执行 `docker-compose --profile standalone up -d demo-app backend-demo-api`
- **那么** 只启动 Demo 模块相关服务

#### 场景:独立模块端口隔离
- **当** 启动多个独立模块
- **那么** 每个模块使用不同端口（Demo:8010, IAM:8020, Tenant:8030）

### 需求:后端服务矩阵

系统必须定义完整的后端服务矩阵。

服务矩阵：

**平台版：**
- backend-platform-api: BUILD_MODULES=demo,iam,tenant, APP_ROLE=web, 端口 8000
- backend-platform-task: BUILD_MODULES=demo,iam,tenant, APP_ROLE=task
- backend-platform-listener: BUILD_MODULES=demo,iam,tenant, APP_ROLE=listener

**Demo 模块独立版：**
- backend-demo-api: BUILD_MODULES=demo, APP_ROLE=web, 端口 8010
- backend-demo-task: BUILD_MODULES=demo, APP_ROLE=task
- backend-demo-listener: BUILD_MODULES=demo, APP_ROLE=listener

**IAM 模块独立版：**
- backend-iam-api: BUILD_MODULES=iam, APP_ROLE=web, 端口 8020

**Tenant 模块独立版：**
- backend-tenant-api: BUILD_MODULES=tenant, APP_ROLE=web, 端口 8030

#### 场景:服务矩阵完整性
- **当** 查看服务列表
- **那么** 包含所有定义的服务

### 需求:环境变量配置

系统必须提供环境变量配置支持。

环境变量必须：
- 数据库连接配置（DATABASE_URL）
- Redis 连接配置（REDIS_URL）
- 端口配置（可自定义）
- 模块配置（可选运行时覆盖）

#### 场景:环境变量模板
- **当** 创建 .env 文件
- **那么** 可以从 .env.docker 模板复制

#### 场景:环境变量覆盖
- **当** 设置 BACKEND_PORT=9000
- **那么** 后端服务使用端口 9000

## 修改需求

无。

## 移除需求

无。
