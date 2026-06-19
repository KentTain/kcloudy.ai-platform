## 为什么

前端模块系统和后端菜单系统已实现，需要 Docker 构建和部署配置来支持模块独立部署。通过子域名隔离各模块，实现按需打包和独立运行，支持平台版（全模块）和独立模块版两种部署模式。

## 变更内容

### 新增

- **Dockerfile**：支持 `BUILD_MODULES` 构建参数，按需打包指定模块
- **docker-compose.yml**：定义平台版和独立模块版的多容器部署
- **nginx 配置**：子域名路由和反向代理配置
- **构建脚本**：生成 `config/modules.ts` 模块配置文件

### 修改

- **package.json**：添加构建脚本支持模块选择

## 功能 (Capabilities)

### 新增功能

- `dockerfile-multi-module`: 多模块 Dockerfile，支持 BUILD_MODULES 参数
- `docker-compose-deploy`: Docker Compose 部署配置，支持平台版和独立模块版
- `nginx-subdomain`: Nginx 子域名路由配置

### 修改功能

无现有功能的需求变更。

## 影响

### 文件影响

| 文件 | 影响 |
|------|------|
| `web/vue/Dockerfile` | 新增 |
| `web/vue/nginx.conf` | 新增 |
| `docker-compose.yml` | 新增（项目根目录） |
| `web/vue/package.json` | 修改，添加构建脚本 |

### 部署架构

```
部署模式：
├── 平台版 (platform.example.com)
│   └── 包含所有模块 (demo, iam, tenant)
│
└── 独立模块版
    ├── demo.example.com → Demo 模块
    ├── iam.example.com → IAM 模块
    └── tenant.example.com → Tenant 模块
```

### 依赖关系

- **依赖变更 1**：后端菜单系统提供菜单 API
- **依赖变更 2**：前端模块系统提供动态模块注册
