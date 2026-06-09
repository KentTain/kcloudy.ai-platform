## 1. 数据库模型与迁移

- [x] 1.1 创建资源配置模型（DatabaseConfig、StorageConfig、CacheConfig、QueueConfig、PubSubConfig）
- [x] 1.2 创建 TenantBusinessConfig 模型（max_users、max_storage_mb、max_api_calls）
- [x] 1.3 修改 Tenant 模型，新增 5 个资源配置 FK 字段
- [x] 1.4 创建模块定义层模型（Module、ModuleMenu、ModulePermission、ModuleRole、ModuleRolePermission）
- [x] 1.5 创建 TenantModule 模型（租户模块分配关联）
- [x] 1.6 修改 IAM 模块模型（Menu、Permission、Role 新增 ref_id、tenant_id）
- [x] 1.7 生成 Alembic 迁移脚本

## 2. 资源配置管理

- [x] 2.1 创建资源配置 Schemas（CreateRequest、UpdateRequest、Response、ListQuery）
- [x] 2.2 实现 DatabaseConfigService（CRUD + 连通性测试）
- [x] 2.3 实现 StorageConfigService（CRUD + 连通性测试）
- [x] 2.4 实现 CacheConfigService（CRUD + 连通性测试）
- [x] 2.5 实现 QueueConfigService（CRUD + 连通性测试）
- [x] 2.6 实现 PubSubConfigService（CRUD + 连通性测试）
- [x] 2.7 实现密码加密工具（AES 加密/解密/脱敏）
- [x] 2.8 创建资源配置 Controllers（五类资源各 6 个端点）

## 3. 租户资源绑定

- [x] 3.1 创建租户资源绑定 Schemas（ResourceBindingRequest、ResourceBindingResponse）
- [x] 3.2 实现租户资源绑定 API（GET/PUT /tenants/{id}/resources）
- [x] 3.3 添加资源配置引用校验（绑定配置必须存在）

## 4. 模块定义层管理

- [x] 4.1 创建模块定义层 Schemas（Module、ModuleMenu、ModulePermission、ModuleRole）
- [x] 4.2 实现 ModuleService（CRUD + 删除保护校验）
- [x] 4.3 实现 ModuleMenuService（CRUD + 树形结构 + 删除保护）
- [x] 4.4 实现 ModulePermissionService（CRUD）
- [x] 4.5 实现 ModuleRoleService（CRUD + 系统角色保护）
- [x] 4.6 实现模块角色权限关联管理（整体替换）
- [x] 4.7 实现模块创建时自动生成默认角色（管理员 + 普通用户）
- [x] 4.8 创建模块定义层 Controllers

## 5. 租户模块分配

- [x] 5.1 创建租户模块分配 Schemas（AssignModuleRequest、TenantModuleResponse）
- [x] 5.2 实现 TenantModuleService（分配/取消/查询）
- [x] 5.3 实现分配校验（模块存在、未重复、已启用、必须模块不可设过期）
- [x] 5.4 实现取消校验（必须模块禁止取消、用户角色使用检查）
- [x] 5.5 创建租户模块分配 Controllers

## 6. 领域事件发布

- [x] 6.1 定义领域事件数据结构（ModuleAssigned、ModuleUnassigned 等 11 种事件）
- [x] 6.2 实现事件发布器（EventPublisher，支持 Redis Stream）
- [x] 6.3 在模块分配操作中发布 ModuleAssigned/ModuleUnassigned 事件
- [x] 6.4 在模块菜单操作中发布 ModuleMenuCreated/Updated/Deleted 事件
- [x] 6.5 在模块权限操作中发布 ModulePermissionCreated/Updated/Deleted 事件
- [x] 6.6 在模块角色操作中发布 ModuleRoleCreated/Updated/Deleted 事件
- [x] 6.7 在模块角色权限变更时发布 ModuleRolePermissionChanged 事件

## 7. IAM 同步处理器

- [x] 7.1 实现事件监听器（EventSubscriber，监听 Redis Stream）
- [x] 7.2 实现 ModuleAssigned 事件处理器（创建租户菜单/权限/角色）
- [x] 7.3 实现 ModuleUnassigned 事件处理器（级联删除租户实例层数据）
- [x] 7.4 实现 ModuleMenuCreated/Updated/Deleted 事件处理器
- [x] 7.5 实现 ModulePermissionCreated/Updated/Deleted 事件处理器
- [x] 7.6 实现 ModuleRoleCreated/Updated/Deleted 事件处理器
- [x] 7.7 实现 ModuleRolePermissionChanged 事件处理器
- [x] 7.8 实现租户实例层只读查询 API（GET /iam/tenants/{tenantId}/menus 等）

## 8. 测试与验证

- [x] 8.1 编写资源配置 CRUD 单元测试（已在任务 2 完成）
- [x] 8.2 编写资源配置连通性测试（已在任务 2 完成）
- [x] 8.3 编写模块定义层 CRUD 测试
- [x] 8.4 编写租户模块分配测试（含边界条件）
- [x] 8.5 编写事件发布测试
- [x] 8.6 编写 IAM 同步处理器测试
- [ ] 8.7 编写集成测试（完整分配流程验证）—— 待后续完善
- [ ] 8.8 手动验证端到端流程 —— 待用户执行
