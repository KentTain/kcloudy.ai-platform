## 1. 基础设施准备

- [ ] 1.1 在 pyproject.toml 中添加插件系统依赖（uv、psutil、pyyaml）
- [ ] 1.2 在 framework/configs/settings.py 中添加插件相关配置（plugin_base_dir、冻结阈值等）
- [ ] 1.3 创建 src/ai_plugin/ 顶级目录结构

## 2. ai_plugin SDK 迁移

- [ ] 2.1 迁移 ai_plugin/sdk/entities/ 目录（agent.py, tool.py, model/, endpoint.py, oauth.py）
- [ ] 2.2 迁移 ai_plugin/sdk/interfaces/ 目录（model/, tool/）
- [ ] 2.3 迁移 ai_plugin/sdk/errors/ 目录（invoke.py, model.py, tool.py, validate.py）
- [ ] 2.4 迁移 ai_plugin/sdk/file/ 目录（constants.py, entities.py, file.py）
- [ ] 2.5 迁移 ai_plugin/sdk/schemas/ 目录（llm.py, message.py, model.py）
- [ ] 2.6 更新所有 sdk/ 内的导入路径为新目录结构

## 3. ai_plugin 服务端迁移

- [ ] 3.1 迁移 ai_plugin/server/core/entities/ 目录（plugin/, invocation.py, message.py）
- [ ] 3.2 迁移 ai_plugin/server/core/server/ 目录（io_server.py, router.py, stdio/, tcp/）
- [ ] 3.3 迁移 ai_plugin/server/core/ 核心文件（plugin_executor.py, plugin_registration.py, runtime.py）
- [ ] 3.4 迁移 ai_plugin/server/core/utils/ 目录（class_loader.py, yaml_loader.py, http_parser.py）
- [ ] 3.5 迁移 ai_plugin/server/config/ 目录（config.py, logger_format.py）
- [ ] 3.6 迁移 ai_plugin/server/invocations/ 目录（model/, app/, file.py）
- [ ] 3.7 迁移 ai_plugin/cli/ 目录（CLI 工具）
- [ ] 3.8 迁移 ai_plugin/plugin.py 入口文件
- [ ] 3.9 更新所有 server/ 内的导入路径为新目录结构

## 4. ai/components/plugin 引擎迁移

- [ ] 4.1 创建 ai/components/plugin/ 目录结构
- [ ] 4.2 迁移 ai/components/plugin/engine/config/ 目录（settings.py）
- [ ] 4.3 迁移 ai/components/plugin/engine/models/ 目录（plugin.py, request.py）
- [ ] 4.4 迁移 ai/components/plugin/engine/utils/ 目录（helpers.py, logger.py）
- [ ] 4.5 迁移 ai/components/plugin/engine/core/helper/ 目录（PluginConfigProcessor）
- [ ] 4.6 迁移 ai/components/plugin/engine/core/session/ 目录（session.py, session_manager.py）
- [ ] 4.7 迁移 ai/components/plugin/engine/core/security/ 目录（security.py）
- [ ] 4.8 迁移 ai/components/plugin/engine/core/communication/ 目录（protocol.py, manager.py）
- [ ] 4.9 迁移 ai/components/plugin/engine/core/monitoring/ 目录（monitoring.py）
- [ ] 4.10 迁移 ai/components/plugin/engine/core/warmup/ 目录（plugin_warmup_manager.py）
- [ ] 4.11 迁移 ai/components/plugin/engine/core/runtime/ 目录（base.py, factory.py, local_runtime.py）
- [ ] 4.12 迁移 ai/components/plugin/engine/core/plugin_manager.py（TenantPluginManager, PluginManagerFactory）
- [ ] 4.13 迁移 ai/components/plugin/engine/core/install_task_manager.py
- [ ] 4.14 迁移 ai/components/plugin/engine/api/routes/ 目录（plugin.py, tool.py, model.py, websocket.py, health.py）
- [ ] 4.15 迁移 ai/components/plugin/engine/api/ 目录（middleware.py）
- [ ] 4.16 迁移 ai/components/plugin/client/ 目录（base.py, model_client.py, tool_client.py, stream_printer.py, plugin/）
- [ ] 4.17 迁移 ai/components/plugin/commands/ 目录（plugin.py CLI 命令）
- [ ] 4.18 迁移 ai/components/plugin/remotable.py 和 setup.py
- [ ] 4.19 更新所有 ai/components/plugin/ 内的导入路径

## 5. 数据层迁移

- [ ] 5.1 创建 ai/models/plugin.py（枚举定义：PluginType, PluginStatus, RuntimeType, CredentialScope 等）
- [ ] 5.2 创建 ai/models/plugin.py（模型定义：Plugin, PluginInstallation, PluginCredential, PluginInstallTask, PluginDeclaration）
- [ ] 5.3 创建 ai/schemas/plugin.py（PluginConfig, PluginInfoVo, PluginCredentialVo 等请求/响应模型）
- [ ] 5.4 创建数据库迁移脚本（创建 ai.plugins 等表）
- [ ] 5.5 创建跨 Schema 外键迁移脚本（关联 tenant.tenants, iam.users）

## 6. 服务层迁移

- [ ] 6.1 创建 ai/services/credential_service.py（凭证加密/解密/脱敏/格式校验）
- [ ] 6.2 创建 ai/services/plugin.py（PluginManagementService）
- [ ] 6.3 适配服务层使用 framework 基础设施（crypto, storage, ctx）

## 7. 控制器层迁移

- [ ] 7.1 创建 ai/controllers/admin/v1/plugin.py（插件安装/卸载/启动/停止/升级）
- [ ] 7.2 创建 ai/controllers/console/v1/plugin.py（插件列表/详情/凭证管理）
- [ ] 7.3 创建 ai/controllers/inner/v1/plugin.py（内部接口：插件信息/调用）
- [ ] 7.4 在 ai/module.py 中注册路由

## 8. 测试与验证

- [ ] 8.1 编写 ai_plugin SDK 单元测试
- [ ] 8.2 编写插件管理服务单元测试
- [ ] 8.3 编写凭证服务单元测试
- [ ] 8.4 编写控制器集成测试
- [ ] 8.5 验证数据库迁移和跨 Schema 外键
- [ ] 8.6 验证插件安装/启动/调用/停止完整流程

## 9. 文档更新

- [ ] 9.1 更新 ai/CLAUDE.md 添加插件系统说明
- [ ] 9.2 更新 server/python/pyproject.toml 的 hatch.build.targets.wheel.packages
