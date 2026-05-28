## 1. Vite 插件开发

- [ ] 1.1 创建 vite-plugins/module-check.ts，实现虚拟模块生成
- [ ] 1.2 实现 BUILD_MODULES 环境变量读取和解析
- [ ] 1.3 实现模块依赖检查逻辑
- [ ] 1.4 集成到 vite.config.ts 插件列表
- [ ] 1.5 测试不同 BUILD_MODULES 组合的构建结果

## 2. 构建配置更新

- [ ] 2.1 修改 vite.config.ts，导入 module-check 插件
- [ ] 2.2 配置 Rollup 的 manualChunks 优化代码分割
- [ ] 2.3 配置构建环境变量注入
- [ ] 2.4 测试 tree-shaking 效果，验证未选中模块代码被移除
- [ ] 2.5 更新 package.json 构建脚本，支持 BUILD_MODULES 参数

## 3. Dockerfile 多阶段构建

- [ ] 3.1 创建 docker/Dockerfile.vue，实现多阶段构建
- [ ] 3.2 实现 base 阶段：安装 Node.js 和 pnpm 依赖
- [ ] 3.3 实现 builder 阶段：编译代码，支持 BUILD_MODULES 参数
- [ ] 3.4 实现 runtime 阶段：Nginx 运行时，只包含构建产物
- [ ] 3.5 配置 Nginx 静态文件服务和 SPA 路由支持
- [ ] 3.6 测试镜像构建和运行

## 4. Docker Compose 配置

- [ ] 4.1 创建 docker/docker-compose.multi.yml，定义多服务配置
- [ ] 4.2 定义 demo-service 服务，使用 BUILD_MODULES=demo
- [ ] 4.3 定义 iam-service 服务，使用 BUILD_MODULES=iam
- [ ] 4.4 定义 tenant-service 服务，使用 BUILD_MODULES=tenant
- [ ] 4.5 定义 nginx 服务，配置多域名反向代理
- [ ] 4.6 配置服务健康检查
- [ ] 4.7 配置服务依赖关系（nginx 依赖前端服务）

## 5. Nginx 配置

- [ ] 5.1 创建 docker/nginx/multi-domain.conf，支持多域名代理
- [ ] 5.2 配置 demo.example.com 代理到 demo-service
- [ ] 5.3 配置 iam.example.com 代理到 iam-service
- [ ] 5.4 配置 tenant.example.com 代理到 tenant-service
- [ ] 5.5 配置 SSL 终止和 CORS 头
- [ ] 5.6 配置 API 网关统一转发规则

## 6. 环境变量和配置

- [ ] 6.1 创建 docker/.env.example，定义环境变量模板
- [ ] 6.2 定义 BUILD_MODULES 默认值
- [ ] 6.3 定义 API_GATEWAY_URL 默认值
- [ ] 6.4 定义各模块的 MODULE_DOMAIN 配置
- [ ] 6.5 更新 docker-compose.yml 支持环境变量替换

## 7. 部署文档

- [ ] 7.1 创建 docs/deploy/multi-module.md
- [ ] 7.2 编写单体部署步骤（所有模块打包在一起）
- [ ] 7.3 编写分离部署步骤（每个模块独立服务）
- [ ] 7.4 编写混合部署步骤（部分模块合并）
- [ ] 7.5 编写环境变量说明
- [ ] 7.6 编写常见问题解答（FAQ）
- [ ] 7.7 提供示例配置和命令

## 8. 测试验证

- [ ] 8.1 测试单体部署：BUILD_MODULES 未设置时构建所有模块
- [ ] 8.2 测试分离部署：各模块独立构建和运行
- [ ] 8.3 测试模块依赖检查：缺失依赖时构建失败
- [ ] 8.4 测试 Docker Compose 一键启动
- [ ] 8.5 测试多域名访问和跨域菜单跳转
- [ ] 8.6 验证镜像大小优化效果

## 9. 清理与兼容

- [ ] 9.1 确保默认行为与现有构建一致（向后兼容）
- [ ] 9.2 移除临时文件和调试代码
- [ ] 9.3 更新 README.md 构建命令说明
- [ ] 9.4 验证开发环境不受影响（pnpm dev 正常）
