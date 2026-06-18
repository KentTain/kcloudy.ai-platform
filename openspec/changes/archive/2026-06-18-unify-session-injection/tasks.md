## 1. 基础设施准备

- [x] 1.1 确认 `get_db_session` 依赖函数正确支持多租户
- [x] 1.2 创建 `get_listener_session()` 依赖函数（如需要）
- [x] 1.3 在 `async_session` 添加废弃警告注释
- [x] 1.4 更新 `server/python/CLAUDE.md` 添加 Session 使用规范说明

## 2. Tenant 模块迁移

- [x] 2.1 迁移 `tenant/services/tenant_service.py` - 所有方法添加 session 参数
- [x] 2.2 迁移 `tenant/services/tenant_module_service.py`
- [x] 2.3 迁移 `tenant/services/module_service.py`
- [x] 2.4 迁移 `tenant/services/module_role_service.py`
- [x] 2.5 迁移 `tenant/services/module_permission_service.py`
- [x] 2.6 迁移 `tenant/services/module_menu_service.py`
- [x] 2.7 迁移 `tenant/services/base_resource_service.py`
- [x] 2.8 迁移 `tenant/services/database_config_service.py`
- [x] 2.9 迁移 `tenant/services/storage_config_service.py`
- [x] 2.10 迁移 `tenant/services/cache_config_service.py`
- [x] 2.11 迁移 `tenant/services/pubsub_config_service.py`
- [x] 2.12 迁移 `tenant/services/queue_config_service.py`
- [x] 2.13 迁移 `tenant/services/module_menu_permission_service.py`
- [x] 2.14 迁移 `tenant/controllers/admin/tenant_module_controller.py`
- [x] 2.15 迁移 `tenant/middlewares/admin_auth_middleware.py`
- [x] 2.16 运行 tenant 模块测试验证

## 3. IAM 模块迁移

- [x] 3.1 迁移 `iam/services/user_service.py` - 所有方法添加 session 参数
- [x] 3.2 迁移 `iam/services/auth_service.py`
- [x] 3.3 迁移 `iam/services/role_service.py`
- [x] 3.4 迁移 `iam/services/permission_service.py`
- [x] 3.5 迁移 `iam/services/menu_service.py`
- [x] 3.6 迁移 `iam/services/department_service.py`
- [x] 3.7 迁移 `iam/services/oauth_service.py`
- [x] 3.8 迁移 `iam/services/user_menu_service.py`
- [x] 3.9 迁移 `iam/services/system_setting_service.py`
- [x] 3.10 迁移 `iam/services/department_service.py`
- [x] 3.11 迁移 `iam/services/module_auto_assigner.py`
- [x] 3.12 迁移 `iam/services/module_sync_service.py`
- [x] 3.13 迁移 `iam/services/tenant_role_creator.py`
- [x] 3.14 迁移 `iam/controllers/inner/user_controller.py`
- [x] 3.15 迁移 `iam/controllers/inner/tenant_role_controller.py`
- [x] 3.16 迁移 `iam/controllers/inner/tenant_permission_controller.py`
- [x] 3.17 迁移 `iam/controllers/inner/tenant_menu_controller.py`
- [x] 3.18 迁移 `iam/controllers/inner/department_controller.py`
- [x] 3.19 迁移 `iam/controllers/admin/user_controller.py`
- [x] 3.20 迁移 `iam/listeners/handlers/event_handler.py`
- [x] 3.21 迁移 `iam/initializers/tenant_admin_initializer.py`
- [x] 3.22 运行 iam 模块测试验证

## 4. AI 模块迁移

- [x] 4.1 迁移 `ai/services/chat_service.py` - 所有方法添加 session 参数
- [x] 4.2 迁移 `ai/services/conversation_service.py`
- [x] 4.3 迁移 `ai/services/credential_service.py`
- [x] 4.4 迁移 `ai/services/plugin.py`
- [x] 4.5 迁移 `ai/components/plugin/engine/core/plugin_manager.py`
- [x] 4.6 运行 ai 模块测试验证

## 5. Framework 模块迁移

- [x] 5.1 迁移 `framework/clients/tenant_client.py`
- [x] 5.2 迁移 `framework/clients/iam_client.py`
- [x] 5.3 迁移 `framework/module/sync_service.py`
- [x] 5.4 运行 framework 模块测试验证

## 6. 清理和验证

- [x] 6.1 移除废弃的 `async_session` 兼容层（可选，确认无使用后）
- [x] 6.2 运行全部测试确保无回归
- [x] 6.3 更新 `server/python/CLAUDE.md` 最终版本
