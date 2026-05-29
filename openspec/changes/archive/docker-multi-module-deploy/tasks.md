## 1. Dockerfile 实现

- [x] 1.1 创建 `web/vue/Dockerfile`，定义多阶段构建
- [x] 1.2 实现 BUILD_MODULES 构建参数处理
- [x] 1.3 实现模块配置文件生成逻辑（src/config/modules.ts）

## 2. Nginx 配置实现

- [x] 2.1 创建 `web/vue/nginx.conf`，配置子域名路由
- [x] 2.2 配置 API 反向代理（/api/ → backend:8000）
- [x] 2.3 配置 SPA 路由回退（try_files）
- [x] 2.4 配置静态资源缓存策略
- [x] 2.5 配置 Gzip 压缩

## 3. Docker Compose 配置

- [x] 3.1 创建项目根目录 `docker-compose.yml`
- [x] 3.2 定义 platform-app 服务（全模块版本）
- [x] 3.3 定义 demo-app 服务（Demo 模块独立部署）
- [x] 3.4 定义 iam-app 服务（IAM 模块独立部署）
- [x] 3.5 定义 tenant-app 服务（Tenant 模块独立部署）
- [x] 3.6 配置后端服务依赖和网络

## 4. 构建脚本更新

- [x] 4.1 更新 `web/vue/package.json`，添加模块构建脚本
- [x] 4.2 创建 `web/vue/scripts/generate-modules-config.ts` 脚本

## 5. 环境变量配置

- [x] 5.1 创建 `web/vue/.env.docker` 模板文件
- [x] 5.2 配置 MODULE_BASE_PATH 环境变量支持

## 6. 文档更新

- [x] 6.1 更新 `docker/README.md`，说明多模块部署方式
- [x] 6.2 更新 `docker/CLAUDE.md`，说明多模块部署命令

## 7. 构建验证

- [x] 7.1 验证平台版构建（BUILD_MODULES=demo,iam,tenant）
- [x] 7.2 验证 Demo 模块独立构建
- [x] 7.3 验证 IAM 模块独立构建
- [x] 7.4 验证 Tenant 模块独立构建
- [ ] 7.5 验证 docker-compose 启动和访问（需要 Docker 镜像拉取）
