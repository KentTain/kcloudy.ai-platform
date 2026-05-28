## 为什么

前端模块系统已实现模块化架构，但当前部署方式仍为单体构建和部署。需要支持构建时选择模块组合、独立域名部署和 Docker Compose 编排，实现真正的模块化部署能力。

## 变更内容

### 新增

- Vite 插件（vite-plugins/module-check.ts）：构建时模块检查和代码生成
- Dockerfile 支持多阶段构建和 BUILD_MODULES 参数
- Docker Compose 配置支持多服务编排（demo、iam、tenant 独立服务）
- 部署文档（docs/deploy/multi-module.md）

### 修改

- vite.config.ts：集成模块检查插件
- docker-compose.yml：支持多模块部署配置

## 功能 (Capabilities)

### 新增功能

- build-time-module-selection: 构建时模块选择，通过 BUILD_MODULES 环境变量控制打包哪些模块
- multi-domain-deploy: 多域名部署支持，每个模块可独立部署到不同域名
- docker-compose-orchestration: Docker Compose 多服务编排，支持模块组合部署

### 修改功能

（无现有规范，均为新增）

## 影响

### 代码影响

新增文件：
- web/vue/vite-plugins/module-check.ts
- web/vue/src/config/modules.ts（构建时生成）
- docker/Dockerfile.vue（多阶段构建）
- docker/docker-compose.multi.yml
- docs/deploy/multi-module.md

修改文件：
- web/vue/vite.config.ts
- docker/docker-compose.yml

### 构建影响

- 构建命令支持 BUILD_MODULES 参数：BUILD_MODULES=demo,iam pnpm build
- 构建产物按模块分割，支持独立部署
- 未选中的模块代码不会打包到产物中

### 部署影响

- 支持单体部署（所有模块打包在一起）
- 支持分离部署（每个模块独立服务）
- 支持混合部署（部分模块合并，部分独立）

### 兼容性考虑

- 默认行为保持不变（所有模块打包）
- 渐进式迁移：先验证单体部署，再尝试分离部署

### 依赖

- 依赖前端模块系统（frontend-module-system 变更）
