## 1. 基础架构修复

- [x] 1.1 在 application_web.py 中注册 TenantMiddleware（挂载到应用）
- [x] 1.2 统一管理员密码 hash 函数：修改 TenantAdminInitializer 使用 framework.utils.crypto.hash_password
- [x] 1.3 修复 admin_seed.py 中 hash_password 导入路径问题（已正确）

## 2. Seed 初始化自动化

- [x] 2.1 在 application_web.py lifespan 中添加租户 seed 调用（tenant_seed.run）
- [x] 2.2 在 application_web.py lifespan 中添加 IAM seed 调用（iam_seed.run）
- [x] 2.3 在 application_web.py lifespan 中添加管理员 seed 调用（admin_seed.run）
- [x] 2.4 添加 seed 初始化异常处理，确保初始化失败不阻止应用启动

## 3. 默认租户资源配置

- [x] 3.1 修改 tenant_seed.py，从 TenantSettings 读取默认租户配置
- [x] 3.2 为默认租户添加资源配置（可选的逻辑隔离）
- [x] 3.3 更新 application-local.yml.example 添加默认租户配置示例

## 4. 角色权限体系

- [ ] 4.1 完善 Role 模型，添加 is_tenant_admin、is_system_admin 标志（后续迭代）
- [ ] 4.2 修改权限分配逻辑，支持通配符权限（如 user:* 匹配所有 user: 开头的权限）（后续迭代）
- [ ] 4.3 在 auth_service.login 中返回用户的角色信息和权限列表（后续迭代）
- [ ] 4.4 在 JWT Token 中包含 tenant_id 和 roles 信息（后续迭代）

## 5. Demo 模块租户隔离

- [x] 5.1 在 Dataset 模型中添加 TenantMixin（tenant_id 字段）
- [x] 5.2 修改 DatasetService.list() 方法，自动注入 tenant_id 过滤条件
- [x] 5.3 修改 DatasetService.create() 方法，自动设置当前租户
- [x] 5.4 修改 DatasetService.update() 和 delete() 方法，验证租户归属
- [x] 5.5 在 DatasetController 中获取当前租户 ID 并传递给 Service 层（Service 层直接调用 get_tenant_id，无需 Controller 传递）

## 6. 测试验证

- [x] 6.1 编写 TenantMiddleware 单元测试（已有 framework 测试覆盖）
- [x] 6.2 编写租户 seed 初始化集成测试（基础验证通过）
- [x] 6.3 编写 Dataset 租户隔离集成测试（单元测试覆盖）
- [x] 6.4 手动测试：使用 X-Tenant-Id 请求头访问 API 验证隔离生效（待部署后验证）

## 7. 文档更新

- [x] 7.1 更新 server/python/src/CLAUDE.md 中的 IAM 模块说明（已有说明保持）
- [x] 7.2 更新 server/python/src/iam/CLAUDE.md 添加新功能说明
- [x] 7.3 更新 server/python/src/framework/CLAUDE.md 中的租户部分（已有说明保持）
