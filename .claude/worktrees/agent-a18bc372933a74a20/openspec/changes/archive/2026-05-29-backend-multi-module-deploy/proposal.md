## 为什么

前端 Vue 多模块 Docker 构建及部署已完成，后端 Python 需要相同的构建和部署能力。通过构建时模块选择，实现按需打包和独立部署，支持平台版（全模块）和独立模块版两种部署模式。

## 变更内容

### 新增

- **Dockerfile**：支持 BUILD_MODULES 和 APP_ROLE 构建参数
- **docker-entrypoint.sh**：根据角色启动不同应用（web/task/listener）
- **配置文件**：构建时生成 src/config/modules.py

### 修改

- **application_web.py**：从配置文件读取 ENABLED_MODULES
- **application_task.py**：从配置文件读取 ENABLED_MODULES
- **application_listener.py**：从配置文件读取 ENABLED_MODULES
- **docker-compose.yml**：添加后端服务矩阵（平台版 + 独立模块版）
- **docker/README.md**：更新部署文档
- **docker/CLAUDE.md**：更新开发手册

## 功能 (Capabilities)

### 新增功能

- backend-dockerfile-multi-module: 后端多模块 Dockerfile，支持 BUILD_MODULES 参数
- backend-role-separation: 角色分离部署，支持 web/task/listener 三种角色
- backend-compose-deploy: Docker Compose 后端部署配置

### 修改功能

无现有功能的需求变更。

## 影响

### 文件影响

| 文件 | 影响 |
|------|------|
| server/python/Dockerfile | 新增 |
| server/python/docker-entrypoint.sh | 新增 |
| server/python/.env.docker | 新增 |
| server/python/src/config/modules.py | 构建时生成 |
| server/python/src/application_web.py | 修改，读取配置 |
| server/python/src/application_task.py | 修改，读取配置 |
| server/python/src/application_listener.py | 修改，读取配置 |
| docker-compose.yml | 修改，添加后端服务 |
| docker/README.md | 修改，添加后端部署说明 |
| docker/CLAUDE.md | 修改，添加构建命令 |
| docs/designs/前后端多模块的构建及部署文档.md | 新增 |

### 部署架构

`
部署模式：┬─ 平台版 (platform.example.com:8000)
│  ├─ backend-platform-api (Web)
│  ├─ backend-platform-task (Task)
│  └─ backend-platform-listener (Listener)
│
└─ 独立模块版
├─ Demo 模块 (demo.example.com:8010)
│  ├─ backend-demo-api
│  ├─ backend-demo-task
│  └─ backend-demo-listener
├─ IAM 模块 (iam.example.com:8020)
│  └─ backend-iam-api
└─ Tenant 模块 (tenant.example.com:8030)
└─ backend-tenant-api
`

### 依赖关系

- **依赖变更 1**：前端模块系统提供模块 API
- **依赖变更 2**：后端菜单系统提供菜单 API
- **依赖变更 3**：前端 docker-multi-module-deploy 已完成
