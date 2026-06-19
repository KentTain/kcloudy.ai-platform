## 1. Tenant 模块基础结构

- [x] 1.1 创建 `server/python/src/tenant/` 模块目录结构
- [x] 1.2 创建 `tenant/models/__init__.py`，使用 `create_module_base("tenant")` 创建 Base
- [x] 1.3 创建 `tenant/module.py`，实现 `TenantModule` 类声明
- [x] 1.4 创建 `tenant/app.py`，实现独立应用工厂

## 2. Tenant 模型迁移

- [x] 2.1 创建 `tenant/models/tenant.py`，迁移 `Tenant` 模型
- [x] 2.2 创建 `tenant/models/tenant_config.py`，迁移 `TenantConfig` 模型
- [x] 2.3 创建 `tenant/models/tenant_admin.py`，迁移 `TenantAdmin` 模型
- [x] 2.4 创建 `tenant/models/enums.py`，迁移租户相关枚举
- [x] 2.5 更新 `tenant/models/__init__.py`，导出所有模型

## 3. Tenant 服务迁移

- [x] 3.1 创建 `tenant/services/tenant_service.py`，迁移 `TenantService`
- [x] 3.2 创建 `tenant/services/tenant_provider_impl.py`，迁移 `TenantProviderImpl`
- [x] 3.3 创建 `tenant/services/__init__.py`，导出服务

## 4. Tenant Schemas 迁移

- [x] 4.1 创建 `tenant/schemas/admin/tenant.py`，迁移管理员端租户 Schema
- [x] 4.2 创建 `tenant/schemas/console/tenant.py`，迁移用户端租户 Schema
- [x] 4.3 创建 `tenant/schemas/__init__.py`，导出所有 Schema

## 5. Tenant 控制器迁移

- [x] 5.1 创建 `tenant/controllers/admin/tenant_controller.py`，迁移管理员端控制器
- [x] 5.2 创建 `tenant/controllers/console/tenant_controller.py`，迁移用户端控制器
- [x] 5.3 创建 `tenant/controllers/__init__.py`，导出路由

## 6. Tenant 内部接口

- [x] 6.1 创建 `tenant/controllers/inner/tenant_controller.py`，实现租户内部接口
- [x] 6.2 实现 `GET /inner/v1/tenants/{tenant_id}` 获取单个租户
- [x] 6.3 实现 `POST /inner/v1/tenants/batch` 批量获取租户
- [x] 6.4 实现 `GET /inner/v1/tenants/{tenant_id}/validate` 验证租户访问权限
- [x] 6.5 实现 `GET /inner/v1/health` 健康检查端点

## 7. Tenant 迁移和 Seed

- [x] 7.1 创建 `tenant/migrations/env.py`，配置 Alembic 环境
- [x] 7.2 创建 `tenant/migrations/versions/001_tenant_tables.py`，初始化租户表
- [x] 7.3 创建 `tenant/migrations/seeds/tenant_seed.py`，租户 seed 数据
- [x] 7.4 更新 `tenant/module.py`，注册 seed 函数

## 8. IAM 模块更新

- [x] 8.1 删除 `iam/models/tenant.py`、`tenant_config.py`、`tenant_admin.py`
- [x] 8.2 更新 `iam/models/__init__.py`，移除租户模型导出
- [x] 8.3 删除 `iam/controllers/admin/tenant_controller.py`
- [x] 8.4 删除 `iam/controllers/console/tenant_controller.py`
- [x] 8.5 更新 `iam/module.py`，添加 `tenant` 依赖，移除租户路由注册
- [x] 8.6 更新 `iam/services/__init__.py`，移除租户服务导出

## 9. IAM 内部接口

- [x] 9.1 创建 `iam/controllers/inner/user_controller.py`，实现用户内部接口
- [x] 9.2 实现 `GET /inner/v1/users/{user_id}` 获取单个用户
- [x] 9.3 实现 `POST /inner/v1/users/batch` 批量获取用户
- [x] 9.4 实现 `GET /inner/v1/users/{user_id}/departments` 获取用户部门
- [x] 9.5 创建 `iam/controllers/inner/department_controller.py`，实现部门内部接口
- [x] 9.6 实现 `GET /inner/v1/departments/tree` 获取部门树
- [x] 9.7 实现 `GET /inner/v1/health` 健康检查端点
- [x] 9.8 更新 `iam/module.py`，注册 inner 路由

## 10. 模块客户端封装

- [x] 10.1 创建 `framework/clients/__init__.py`
- [x] 10.2 创建 `framework/clients/inner_http_client.py`，实现内部 HTTP 客户端
- [x] 10.3 创建 `framework/clients/tenant_client.py`，实现 `TenantClient`
- [x] 10.4 创建 `framework/clients/iam_client.py`，实现 `IamClient`
- [x] 10.5 更新 `framework/configs/settings.py`，添加 inner 接口配置项

## 11. 前端 Tenant 模块

- [x] 11.1 创建 `web/vue/src/tenant/` 模块目录结构
- [x] 11.2 创建 `web/vue/src/tenant/api/tenant.ts`，迁移租户 API
- [x] 11.3 创建 `web/vue/src/tenant/types/index.ts`，迁移租户类型定义
- [x] 11.4 创建 `web/vue/src/tenant/pages/tenants/`，迁移租户页面
- [x] 11.5 创建 `web/vue/src/tenant/router/index.ts`，迁移租户路由
- [x] 11.6 创建 `web/vue/src/tenant/index.ts`，模块入口

## 12. 前端 IAM 模块更新

- [x] 12.1 删除 `web/vue/src/iam/api/tenant.ts`
- [x] 12.2 删除 `web/vue/src/iam/pages/tenants/` 目录
- [x] 12.3 更新 `web/vue/src/iam/router/index.ts`，移除租户路由
- [x] 12.4 更新 `web/vue/src/iam/index.ts`，移除租户 API 导出

## 13. 测试更新

- [x] 13.1 创建 `tests/tenant/` 测试目录结构
- [x] 13.2 创建 `tests/tenant/unit/test_tenant_service.py`
- [x] 13.3 创建 `tests/tenant/integration/test_tenant_api.py`
- [x] 13.4 创建 `tests/tenant/integration/test_inner_api.py`
- [x] 13.5 更新 `tests/iam/` 移除租户相关测试
- [x] 13.6 创建 `tests/framework/unit/test_inner_client.py`

## 14. 文档更新

- [x] 14.1 创建 `server/python/src/tenant/CLAUDE.md`，Tenant 模块文档
- [x] 14.2 更新 `server/python/src/iam/CLAUDE.md`，移除租户相关内容
- [x] 14.3 更新 `server/python/src/CLAUDE.md`，添加 Tenant 模块说明
- [x] 14.4 创建 `web/vue/src/tenant/CLAUDE.md`，前端 Tenant 模块文档

## 15. 迁移脚本和数据迁移

- [x] 15.1 创建数据库备份脚本
- [x] 15.2 创建迁移验证脚本（检查 tenant schema 创建成功）
- [x] 15.3 执行重建迁移（删除现有表，重新执行迁移）
- [x] 15.4 验证 seed 数据正确初始化
- [x] 15.5 运行全量测试验证功能回归
