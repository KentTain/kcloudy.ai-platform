# 分页列表响应规范

定义分页列表响应对象的命名规范和字段完整性要求。

## 目的

建立清晰的响应对象命名规范，区分分页列表响应和全量列表响应，确保分页响应包含完整的元数据字段。

## 新增需求

### 需求:分页列表响应命名规范

分页列表响应类必须使用 `{Entity}PaginatedListResponse` 命名模式。全量列表响应类使用 `{Entity}ListResponse` 命名模式。

#### 场景:分页列表响应命名

- **当** 响应对象包含分页元数据（total、page、page_size）
- **那么** 类名必须使用 `{Entity}PaginatedListResponse` 格式（如 `TenantPaginatedListResponse`、`UserPaginatedListResponse`）

#### 场景:全量列表响应命名

- **当** 响应对象仅包含列表数据，不含分页元数据
- **那么** 类名必须使用 `{Entity}ListResponse` 格式（如 `MenuListResponse`、`ConversationListResponse`）

### 需求:分页列表响应字段完整

分页列表响应必须包含完整的分页元数据字段：`items`、`total`、`page`、`page_size`。禁止出现只有 `items` + `total` 而缺失 `page`/`page_size` 的分页响应。

#### 场景:分页响应包含四个字段

- **当** 定义 `XxxPaginatedListResponse` 类
- **那么** 该类必须包含以下字段：
  - `items: list[XxxResponse]` — 数据列表
  - `total: int` — 总数量
  - `page: int` — 当前页码
  - `page_size: int` — 每页数量

#### 场景:补齐缺失的分页字段

- **当** 现有分页型 `XxxListResponse` 缺失 `page` 或 `page_size` 字段
- **那么** 重命名为 `XxxPaginatedListResponse` 时必须补齐 `page` 和 `page_size` 字段

### 需求:前端分页响应泛型

前端必须提供分页响应泛型接口，与后端响应格式对齐，替代原有的 `PageResult<T>`。

#### 场景:PaginatedListResponse 泛型定义（旧格式）

- **当** 定义 `PaginatedListResponse<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `items: T[]`
  - `total: number`
  - `page: number`
  - `page_size: number`

#### 场景:SuccessExtra 泛型定义（新格式）

- **当** 定义 `SuccessExtra<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `code: number`
  - `msg: string`
  - `data: T`
  - `total: number`
  - `page: number`
  - `page_size: number`

#### 场景:DataTable 使用 SuccessExtra

- **当** useDataTable 的 `remoteFetchFn` 返回数据
- **那么** 返回类型必须为 `Promise<SuccessExtra<TData[]>>`
- **那么** `data` 字段直接是数组，不是嵌套对象

#### 场景:API 调用使用泛型

- **当** API 函数返回分页数据
- **那么** 推荐使用 `SuccessExtra<XxxResponse[]>` 类型
- **那么** `PaginatedListResponse` 和 `ApiResponse<PaginatedListResponse<XxxResponse>>` 已废弃

### 需求:PageResult 废弃

前端 `PageResult<T>` 必须被 `PaginatedListResponse<T>` 替代。禁止在新代码中使用 `PageResult<T>`。

#### 场景:PageResult 不再使用

- **当** 前端代码需要分页响应类型
- **那么** 禁止使用 `PageResult<T>`，必须使用 `SuccessExtra<T[]>` 或 `PaginatedListResponse<T>`

### 需求:ApiResponse 字段对齐

前端 `ApiResponse<T>` 类型必须与后端响应格式对齐。后端已统一使用 `msg` 字段，前端必须同步更新。

#### 场景:ApiResponse 字段更新

- **当** 定义 `ApiResponse<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `code: number`
  - `msg: string`
  - `data: T`
- **那么** 禁止使用 `message` 字段名

### 需求:PaginatedListResponse 废弃标记

`PaginatedListResponse<T>` 必须标记为废弃，推荐使用 `SuccessExtra<T[]>` 替代。

#### 场景:类型迁移提示

- **当** 代码使用 `PaginatedListResponse<T>`
- **那么** TypeScript 显示废弃警告，提示使用 `SuccessExtra<T[]>`

### 需求:后端分页响应函数对齐

后端 `paginated_response()` 工具函数返回的 JSON 结构必须与 `XxxPaginatedListResponse` 字段名一致。

#### 场景:paginated_response 结构对齐

- **当** 调用 `paginated_response()` 函数
- **那么** 返回的 data 对象必须包含 `items` 和 `pagination` 字段
- **那么** `pagination` 对象必须包含 `page`、`page_size`、`total`、`total_pages`、`has_next`、`has_prev`

### 需求:DTO 命名规范文档更新

`server/CLAUDE.md` 和 `web/CLAUDE.md` 中的通信对象（DTO）命名规范表必须更新，新增分页查询和分页列表响应的命名规则。

#### 场景:后端命名规范表更新

- **当** 更新 `server/CLAUDE.md` 的 DTO 命名规范表
- **那么** 必须包含以下行：
  - 非分页查询 → `{Entity}Query` → `DepartmentQuery`
  - 分页查询 → `{Entity}PaginatedQuery` → `TenantPaginatedQuery`
  - 全量列表响应 → `{Entity}ListResponse` → `MenuListResponse`
  - 分页列表响应 → `{Entity}PaginatedListResponse` → `TenantPaginatedListResponse`

#### 场景:前端命名规范表更新

- **当** 更新 `web/CLAUDE.md` 的 DTO 命名规范表
- **那么** 必须包含与后端一致的命名规则
