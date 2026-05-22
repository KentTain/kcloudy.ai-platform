## 1. 创建协议定义

- [x] 1.1 创建 `framework/tenant/protocols.py`
  - 定义 `TenantDatabaseConfig`、`TenantStorageConfig`、`TenantQueueConfig`、`TenantPubSubConfig` dataclass
  - 定义 `TenantInfo` Protocol（基础信息 + 资源配置属性）
  - 定义 `TenantProvider` Protocol（get_tenant、validate_access、get_user_tenants 方法）
  - 实现全局注册机制 `register_tenant_provider()` / `get_tenant_provider()`

## 2. 扩展 SimpleTenant

- [x] 2.1 修改 `framework/tenant/context.py`
  - 为 `SimpleTenant` 添加资源配置字段（database、storage、queue、pubsub）
  - 更新 `from_model()` 方法支持可选的资源配置提取

## 3. 实现 IAM 模块的 TenantProvider

- [x] 3.1 创建 `iam/services/tenant_provider_impl.py`
  - 实现 `IamTenantProvider` 类
  - 实现 `get_tenant()` 方法（调用 TenantService.get_by_id）
  - 实现 `validate_access()` 方法（查询 UserTenant 关联）
  - 实现 `get_user_tenants()` 方法（调用 TenantService.get_user_tenants）

## 4. 重构 TenantMiddleware

- [x] 4.1 修改 `framework/tenant/middleware.py`
  - 移除 `from iam.models import Tenant, TenantStatus` 导入
  - 移除 `from iam.models import UserTenant` 导入
  - 使用 `get_tenant_provider()` 获取租户信息
  - 使用 `provider.validate_access()` 验证访问权限
  - 使用 `tenant.status != "active"` 替代 `TenantStatus.ACTIVE` 比较

## 5. 重构 TenantTaskExecutor

- [x] 5.1 修改 `framework/queue/task_executor.py`
  - 移除 `from iam.services.tenant_service import TenantService` 导入
  - 使用 `get_tenant_provider()` 获取租户信息
  - 使用 `provider.get_tenant()` 恢复租户上下文

## 6. 注册 TenantProvider

- [x] 6.1 修改 `application_web.py`
  - 导入 `IamTenantProvider` 和 `register_tenant_provider`
  - 在应用创建时注册 TenantProvider

## 7. 清理旧代码

- [x] 7.1 删除 `framework/tenant/models.py`
- [x] 7.2 更新 `framework/tenant/__init__.py`
  - 移除 `Tenant`、`TenantSetting` 导出
  - 添加 `TenantInfo`、`TenantProvider`、`register_tenant_provider`、`get_tenant_provider` 导出
  - 添加资源配置类导出

## 8. 更新文档

- [x] 8.1 更新 `framework/CLAUDE.md`
  - 添加"模块依赖规则"章节
  - 明确 framework 禁止引用业务模块
  - 说明依赖倒置的解决方案（Protocol + 运行时注入）

## 9. 测试验证

- [x] 9.1 验证中间件租户解析功能正常
- [x] 9.2 验证任务执行器租户上下文恢复正常
- [x] 9.3 验证应用启动流程正常（TenantProvider 注册）
- [x] 9.4 运行现有测试确保无回归

## 10. 审查问题修复

- [x] 10.1 C1: 删除 context.py 中重复的 TenantInfo 定义
- [x] 10.2 W1: SimpleTenant.from_model 添加资源配置映射注释
- [x] 10.3 W2: 添加 IamTenantProvider 单元测试（5 个场景）
- [x] 10.4 W3: TenantInfo Protocol 添加 expired_at 属性
- [x] 10.5 中间件实现租户过期验证逻辑
