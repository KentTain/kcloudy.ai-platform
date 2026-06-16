## 1. 后端基类创建（framework）

- [ ] 1.1 在 `framework/schemas/base.py` 中创建 `BaseQuery`（列表查询基类）和 `BasePaginatedQuery`（分页查询基类，继承 BaseQuery，添加 page/page_size），标记 `BaseQueryParams` 为 deprecated
- [ ] 1.2 在 `framework/schemas/base.py` 的 `__all__` 中导出新类名
- [ ] 1.3 在 `framework/common/responses.py` 中更新 `paginated_response()` 函数，确保返回结构与 `XxxPaginatedListResponse` 字段对齐

## 2. 后端 tenant 模块响应重命名

- [ ] 2.1 在 `tenant/schemas/admin/tenant.py` 中将 `TenantListResponse` 重命名为 `TenantPaginatedListResponse`
- [ ] 2.2 在 `tenant/schemas/admin/resource_config.py` 中将 `ResourceQuery` 拆分为 `ResourceQuery`（非分页）+ `ResourcePaginatedQuery`（继承 ResourceQuery + BasePaginatedQuery），将 5 个 `XxxPropertyListResponse` 重命名为 `XxxPropertyPaginatedListResponse`
- [ ] 2.3 在 `tenant/schemas/admin/module.py` 中将 `ModuleListResponse`、`ModulePermissionListResponse`、`ModuleRoleListResponse` 重命名为对应的 `PaginatedListResponse`（ModuleMenuListResponse 保持不变，全量树形）
- [ ] 2.4 在 `tenant/schemas/admin/tenant_module.py` 中将 `TenantModuleListResponse` 重命名为 `TenantModulePaginatedListResponse`
- [ ] 2.5 更新 tenant 模块所有 controller 和 service 文件中的引用

## 3. 后端 iam 模块响应重命名 + 参数统一

- [ ] 3.1 在 `iam/schemas/user.py` 中将 `UserListResponse` 重命名为 `UserPaginatedListResponse`，补齐 `page`/`page_size` 字段
- [ ] 3.2 在 `iam/schemas/role.py` 中将 `RoleListResponse` 重命名为 `RolePaginatedListResponse`，补齐 `page`/`page_size` 字段
- [ ] 3.3 在 `iam/schemas/permission.py` 中将 `PermissionListResponse` 重命名为 `PermissionPaginatedListResponse`，补齐 `page`/`page_size` 字段
- [ ] 3.4 在 `iam/schemas/console/system_setting.py` 中将 `ConsoleSystemSettingListResponse` 重命名为 `ConsoleSystemSettingPaginatedListResponse`，补齐 `page`/`page_size` 字段
- [ ] 3.5 在 `iam/schemas/admin/system_setting.py` 中将 `SystemSettingListResponse` 重命名为 `SystemSettingPaginatedListResponse`
- [ ] 3.6 MenuListResponse、UserMenuListResponse 保持不变（全量树形）
- [ ] 3.7 创建 `UserPaginatedQuery`、`RolePaginatedQuery`、`PermissionPaginatedQuery` 等分页查询类（继承对应 Query + BasePaginatedQuery）
- [ ] 3.8 修改 `iam/controllers/admin/user_controller.py`，将散落的 `page`/`page_size` 参数改为 `UserPaginatedQuery`
- [ ] 3.9 修改 `iam/controllers/admin/role_controller.py`，将散落的 `page`/`page_size` 参数改为 `RolePaginatedQuery`
- [ ] 3.10 修改 `iam/controllers/admin/system_setting_controller.py`，将散落的 `page`/`page_size` 参数改为对应 PaginatedQuery
- [ ] 3.11 修改 `iam/controllers/inner/tenant_permission_controller.py` 和 `tenant_role_controller.py`，将散落的 `page`/`page_size` 参数改为对应 PaginatedQuery
- [ ] 3.12 更新 iam 模块所有 service 文件中的引用

## 4. 后端 demo 模块响应重命名

- [ ] 4.1 在 `demo/schemas/dataset.py` 中将 `DatasetListResponse` 重命名为 `DatasetPaginatedListResponse`，补齐 `page`/`page_size` 字段
- [ ] 4.2 更新 demo 模块所有 controller 和 service 文件中的引用

## 5. 后端 ai 模块响应重命名

- [ ] 5.1 在 `ai/schemas/plugin.py` 中将 `PluginListResponseVo` 重命名为 `PluginPaginatedListResponseVo`
- [ ] 5.2 ConversationListResponse、ModelListResponse 保持不变（全量列表）
- [ ] 5.3 更新 ai 模块所有 controller 和 service 文件中的引用

## 6. 后端 Rust 模块同步

- [ ] 6.1 在 `server/rust/src/demo/schemas/mod.rs` 中将 `PageRequest` 重命名为 `BasePaginatedQuery`，将 `PageResponse<T>` 重命名为 `PaginatedListResponse<T>`
- [ ] 6.2 更新 Rust demo 模块 controller 和 service 中的引用

## 7. 前端 framework 类型重构

- [ ] 7.1 在 `framework/types/index.ts` 中创建 `BaseQuery`（列表查询基类）和 `BasePaginatedQuery`（继承 BaseQuery，添加 page/page_size），将 `PageParams` 标记为 deprecated
- [ ] 7.2 在 `framework/types/index.ts` 中将 `PageResult<T>` 重命名为 `PaginatedListResponse<T>`
- [ ] 7.3 更新 `framework/types/index.ts` 的导出列表

## 8. 前端 iam 模块类型重构

- [ ] 8.1 在 `iam/types/index.ts` 中将 `UserQuery`、`RoleQuery`、`PermissionQuery`、`LoginHistoryQuery` 重命名为对应的 `PaginatedQuery`，`DepartmentQuery` 去掉 `page`/`page_size` 字段（保留为非分页查询）
- [ ] 8.2 删除 `iam/api/user.ts` 中重复的 `UserQuery` 定义，改为从 `../types` 导入 `UserPaginatedQuery`
- [ ] 8.3 删除 `iam/api/role.ts` 中重复的 `RoleQuery` 定义，改为从 `../types` 导入 `RolePaginatedQuery`
- [ ] 8.4 删除 `iam/api/permission.ts` 中重复的 `PermissionQuery` 定义，改为从 `../types` 导入 `PermissionPaginatedQuery`
- [ ] 8.5 删除 `iam/api/department.ts` 中重复的 `DepartmentQuery` 定义，改为从 `../types` 导入
- [ ] 8.6 更新 `iam/api/auth.ts` 中的 `LoginHistoryQuery` 引用为 `LoginHistoryPaginatedQuery`
- [ ] 8.7 更新 `iam/types/index.ts` 中的 `MenuListResponse` 保持不变
- [ ] 8.8 更新 iam 模块所有 API 函数中的 `PageResult` 引用为 `PaginatedListResponse`

## 9. 前端 tenant 模块类型重构

- [ ] 9.1 在 `tenant/types/index.ts` 中将 `TenantQuery` 重命名为 `TenantPaginatedQuery`
- [ ] 9.2 在 `tenant/types/admin.ts` 中将 `ModuleQuery` 重命名为 `ModulePaginatedQuery`
- [ ] 9.3 在 `tenant/types/resource.ts` 中将 `ResourceQuery` 重命名为 `ResourcePaginatedQuery`
- [ ] 9.4 更新 tenant 模块所有 API 函数中的 `PageResult` 引用为 `PaginatedListResponse`，Query 引用为 PaginatedQuery

## 10. 前端 ai 模块类型同步

- [ ] 10.1 更新 `ai/api/model.ts` 中 `ModelListResponse` 保持不变（全量）
- [ ] 10.2 更新 `ai/api/conversation.ts` 中 `ConversationListResponse` 保持不变（全量）
- [ ] 10.3 更新 `framework/stores/menu.ts` 中 `MenuListResponse` 保持不变（全量）
- [ ] 10.4 更新 ai 模块 API 函数中 `PageResult` 引用为 `PaginatedListResponse`

## 11. 文档更新

- [ ] 11.1 更新 `server/CLAUDE.md` DTO 命名规范表：新增「非分页查询 → {Entity}Query」「分页查询 → {Entity}PaginatedQuery」「全量列表响应 → {Entity}ListResponse」「分页列表响应 → {Entity}PaginatedListResponse」
- [ ] 11.2 更新 `web/CLAUDE.md` DTO 命名规范表：同上，与后端保持一致

## 12. 验证

- [ ] 12.1 运行 Python 后端 Ruff 检查，确认无未解析引用
- [ ] 12.2 运行 Vue 前端 TypeScript 编译检查，确认无类型错误
- [ ] 12.3 运行 Python 后端测试 `uv run pytest`，确认无失败测试
- [ ] 12.4 运行 Vue 前端测试 `pnpm test:unit --run`，确认无失败测试
