## 为什么

前后端通信对象（DTO）的命名规范中，`{Entity}Query` 混合了分页查询和非分页查询两种语义，`{Entity}ListResponse` 混合了分页列表和全量列表两种形态。这导致：
- 无法从类名判断是否含分页参数
- 无法从类名判断响应是否包含分页元数据
- 部分分页型 ListResponse 缺失 `page`/`page_size` 字段，响应结构不统一
- 前端 Query 类型在 types 和 api 文件中重复定义
- 后端 IAM 模块 controller 中散落 `page`/`page_size` 参数，未使用 Query 类

## 变更内容

### 查询对象分离
- 将 `BaseQueryParams` 拆分为 `BaseQuery`（列表查询基类）和 `BasePaginatedQuery`（分页查询基类，继承 BaseQuery，新增 page/page_size）
- 实体查询同步拆分：`XxxQuery`（非分页查询）+ `XxxPaginatedQuery`（分页查询，继承 XxxQuery + BasePaginatedQuery）
- 前端 `PageParams` 拆分为 `BaseQuery` + `BasePaginatedQuery`

### 分页列表响应重命名
- **BREAKING**: 所有分页型 `XxxListResponse` 重命名为 `XxxPaginatedListResponse`
- 统一补齐缺失的 `page`/`page_size` 字段（当前 IAM 模块的部分 ListResponse 只有 items + total）
- 全量型 ListResponse（树形列表等）保持 `XxxListResponse` 不变
- 前端 `PageResult<T>` 重命名为 `PaginatedListResponse<T>`

### 前端 Query 去重
- 删除 iam/api/*.ts 中重复定义的 Query 接口，统一从 types/index.ts 导入

### 后端散落参数统一
- IAM 模块 controller 中散落的 `page: int = 1, page_size: int = 20` 参数统一改为 `XxxPaginatedQuery` 接收

### 规范文档更新
- 更新 server/CLAUDE.md 和 web/CLAUDE.md 中的 DTO 命名规范表

## 功能 (Capabilities)

### 新增功能
- `paginated-query`: 分页查询对象体系——BaseQuery 基类、BasePaginatedQuery 分页查询基类、实体级 XxxPaginatedQuery
- `paginated-list-response`: 分页列表响应对象——XxxPaginatedListResponse 命名规范、PaginatedListResponse<T> 泛型、统一字段补齐

### 修改功能

（无现有规范需要修改）

## 影响

### 后端 Python（server/python/src/）
- `framework/schemas/base.py`：BaseQueryParams → BaseQuery + BasePaginatedQuery
- `tenant/schemas/admin/tenant.py`：TenantListResponse → TenantPaginatedListResponse
- `tenant/schemas/admin/resource_config.py`：ResourceQuery → ResourcePaginatedQuery，5 个 PropertyListResponse → PropertyPaginatedListResponse
- `tenant/schemas/admin/module.py`：4 个 ListResponse → PaginatedListResponse
- `tenant/schemas/admin/tenant_module.py`：TenantModuleListResponse → TenantModulePaginatedListResponse
- `iam/schemas/user.py`：UserListResponse → UserPaginatedListResponse（补齐 page/page_size）
- `iam/schemas/role.py`：RoleListResponse → RolePaginatedListResponse（补齐 page/page_size）
- `iam/schemas/permission.py`：PermissionListResponse → PermissionPaginatedListResponse（补齐 page/page_size）
- `iam/schemas/menu.py`：MenuListResponse 保持（全量树形）
- `iam/schemas/user_menu.py`：UserMenuListResponse 保持（全量树形）
- `iam/schemas/console/system_setting.py`：ConsoleSystemSettingListResponse → PaginatedListResponse（补齐 page/page_size）
- `iam/schemas/admin/system_setting.py`：SystemSettingListResponse → SystemSettingPaginatedListResponse
- `iam/controllers/admin/*.py`：散落分页参数 → XxxPaginatedQuery
- `iam/controllers/inner/*.py`：散落分页参数 → XxxPaginatedQuery
- `demo/schemas/dataset.py`：DatasetListResponse → DatasetPaginatedListResponse（补齐 page/page_size）
- `ai/schemas/plugin.py`：PluginListResponseVo → PluginPaginatedListResponseVo
- `ai/schemas/conversation.py`：ConversationListResponse 保持（全量）
- `ai/schemas/model.py`：ModelListResponse 保持（全量）
- 所有引用以上类名的 controller、service 文件

### 前端 Vue（web/vue/src/）
- `framework/types/index.ts`：PageParams → BaseQuery + BasePaginatedQuery，PageResult<T> → PaginatedListResponse<T>
- `iam/types/index.ts`：6 个 Query 重命名 + 拆分
- `iam/api/user.ts`、`iam/api/role.ts`、`iam/api/permission.ts`、`iam/api/department.ts`：删除重复 Query，从 types 导入
- `iam/api/auth.ts`：LoginHistoryQuery → LoginHistoryPaginatedQuery
- `tenant/types/index.ts`：TenantQuery → TenantPaginatedQuery
- `tenant/types/admin.ts`：ModuleQuery → ModulePaginatedQuery
- `tenant/types/resource.ts`：ResourceQuery → ResourcePaginatedQuery
- `tenant/api/*.ts`：更新引用
- `ai/api/model.ts`、`ai/api/conversation.ts`：更新类型名
- `framework/stores/menu.ts`：MenuListResponse 保持
- 所有引用 PageResult 的组件和 API 文件

### 后端 Rust（server/rust/src/）
- `demo/schemas/mod.rs`：PageRequest → BasePaginatedQuery，PageResponse<T> → PaginatedListResponse<T>

### 文档
- `server/CLAUDE.md`：DTO 命名规范表更新
- `web/CLAUDE.md`：DTO 命名规范表更新
