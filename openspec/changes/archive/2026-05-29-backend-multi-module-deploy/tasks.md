## 1. Dockerfile 实现

- [x] 1.1 创建 `server/python/Dockerfile`，定义多阶段构建
- [x] 1.2 实现 BUILD_MODULES 构建参数处理
- [x] 1.3 实现 APP_ROLE 构建参数处理
- [x] 1.4 实现构建时 modules.py 配置文件生成
- [x] 1.5 配置健康检查和标签

## 2. Entrypoint 脚本实现

- [x] 2.1 创建 `server/python/docker-entrypoint.sh`
- [x] 2.2 实现 APP_ROLE 角色判断逻辑
- [x] 2.3 添加启动前日志输出
- [x] 2.4 添加错误处理和退出码

## 3. 应用入口修改

- [x] 3.1 修改 `application_web.py`，从 config.modules 读取 ENABLED_MODULES
- [x] 3.2 修改 `application_task.py`，从 config.modules 读取 ENABLED_MODULES
- [x] 3.3 修改 `application_listener.py`，从 config.modules 读取 ENABLED_MODULES
- [x] 3.4 添加日志输出，显示加载的模块列表

## 4. Docker Compose 配置

- [x] 4.1 更新根目录 `docker-compose.yml`，替换 backend placeholder
- [x] 4.2 定义平台版三个服务（api/task/listener）
- [x] 4.3 定义 Demo 模块独立部署服务（api/task/listener）
- [x] 4.4 定义 IAM 模块独立部署服务（api）
- [x] 4.5 定义 Tenant 模块独立部署服务（api）
- [x] 4.6 配置服务依赖和网络

## 5. 环境变量配置

- [x] 5.1 创建 `server/python/.env.docker` 模板文件
- [x] 5.2 配置数据库连接环境变量
- [x] 5.3 配置 Redis 连接环境变量
- [x] 5.4 配置模块相关环境变量

## 6. 设计文档

- [x] 6.1 创建 `docs/designs/前后端多模块的构建及部署文档.md`
- [x] 6.2 文档前端多模块构建方案
- [x] 6.3 文档后端多模块构建方案
- [x] 6.4 文档部署架构和最佳实践

## 7. 部署文档更新

- [x] 7.1 更新 `docker/README.md`，添加后端多模块部署说明
- [x] 7.2 更新 `docker/CLAUDE.md`，添加后端构建命令说明
- [x] 7.3 添加角色分离部署说明
- [x] 7.4 添加环境变量配置说明

## 8. 构建验证

- [x] 8.1 验证平台版构建（BUILD_MODULES=demo,iam,tenant）
- [x] 8.2 验证 Demo 模块独立构建 ✓
- [x] 8.3 验证 IAM 模块独立构建 ✓
- [x] 8.4 验证 Tenant 模块独立构建 ✓
- [x] 8.5 验证角色分离启动 ✓ (modules.py 已生成)（web/task/listener） ⚠️ 同上
- [ ] 8.6 验证 docker-compose 启动和访问 (需要数据库/Redis 环境)
