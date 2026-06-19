## 上下文

前端模块分离方案的最后一环，实现 Docker 多模块部署配置。前端模块系统已支持动态模块注册，后端菜单系统已提供菜单 API，现在需要 Docker 构建和部署配置来完成独立部署能力。

参考设计文档：`docs/designs/前端Vue的模块分离设计方案.md`

### 约束

- 前端使用 Vue 3 + Vite 构建
- 子域名部署，Cookie 共享（Domain=.example.com）
- 使用 nginx 作为反向代理
- 支持平台版（全模块）和独立模块版两种部署模式

## 目标 / 非目标

**目标：**

- 创建支持 BUILD_MODULES 参数的 Dockerfile
- 配置子域名路由的 nginx
- 定义平台版和独立模块版的 docker-compose.yml
- 实现构建时模块配置文件生成

**非目标：**

- Kubernetes 部署配置
- CI/CD 流水线配置
- 生产环境安全加固（HTTPS、安全头等）

## 决策

### 决策 1：构建时模块选择 vs 运行时模块加载

**选择：** 构建时模块选择

**理由：**
- 减少构建产物体积，未使用的模块代码不打包
- 更简单的实现，无需复杂的动态加载逻辑
- 与 Vite 的 tree-shaking 配合更好

**替代方案：**
- 运行时动态加载 → 增加复杂度，需要模块服务器

### 决策 2：多阶段构建策略

**选择：** 单一 Dockerfile + 构建参数

**理由：**
- 减少维护成本，单一配置文件
- 灵活支持任意模块组合
- 构建缓存复用

**替代方案：**
- 每个模块独立 Dockerfile → 维护成本高，重复代码多

### 决策 3：子域名路由策略

**选择：** nginx 统一处理子域名路由

**理由：**
- 集中配置，便于管理
- 支持 SSL 证书统一配置
- 跨模块菜单跳转由 nginx 处理

**替代方案：**
- 各模块独立 nginx 配置 → 配置分散，难以维护

### 决策 4：模块配置文件生成

**选择：** 构建时生成 `config/modules.ts`

**理由：**
- 类型安全，TypeScript 编译时检查
- 与 Vite 构建流程集成
- 无运行时开销

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 构建参数错误导致模块缺失 | 验证 BUILD_MODULES 格式，提供默认值 |
| 子域名 Cookie 共享问题 | nginx 配置 Domain=.example.com |
| 跨模块菜单跳转体验 | nginx 配置重定向，前端添加 loading 提示 |
| 构建缓存失效 | 使用多阶段构建，分离依赖安装和构建 |

## 迁移计划

### 步骤 1：创建 Dockerfile

```dockerfile
# web/vue/Dockerfile
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine AS builder

ARG BUILD_MODULES=demo,iam,tenant
# 生成模块配置文件
RUN echo "export const ENABLED_MODULES = ['${BUILD_MODULES//,/','}'];" > src/config/modules.ts

# 构建
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### 步骤 2：创建 nginx 配置

```nginx
# web/vue/nginx.conf
server {
    listen 80;
    server_name ~^(?<subdomain>.+)\.example\.com$;

    # 子域名路由
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API 代理
    location /api/ {
        proxy_pass http://backend:8000;
    }
}
```

### 步骤 3：创建 docker-compose.yml

```yaml
# docker-compose.yml
services:
  platform-app:
    build:
      context: ./web/vue
      args:
        BUILD_MODULES: demo,iam,tenant
    ports:
      - "3000:80"

  demo-app:
    build:
      context: ./web/vue
      args:
        BUILD_MODULES: demo
    ports:
      - "3001:80"
```

## 待解决问题

无。
