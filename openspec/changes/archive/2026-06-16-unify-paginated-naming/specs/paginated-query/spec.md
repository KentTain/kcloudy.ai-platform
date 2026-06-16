## 新增需求

### 需求:列表查询基类

系统必须提供 `BaseQuery` 作为列表查询基类，包含非分页的通用过滤字段。`BaseQuery` 禁止包含分页参数（page、page_size）。

Python 后端定义于 `framework/schemas/base.py`，Vue 前端定义于 `framework/types/index.ts`。

#### 场景:BaseQuery 仅包含通用过滤字段

- **当** 定义 `BaseQuery` 类
- **那么** 该类仅包含通用过滤字段（如 `keyword`），禁止包含 `page` 或 `page_size`

#### 场景:实体查询继承 BaseQuery

- **当** 定义实体查询类 `XxxQuery`（如 `TenantQuery`、`ResourceQuery`）
- **那么** 该类继承 `BaseQuery`，添加实体特有的过滤字段（如 `status`、`type`）
- **那么** 该类禁止包含 `page` 或 `page_size` 字段

### 需求:分页查询基类

系统必须提供 `BasePaginatedQuery` 作为分页查询基类，继承 `BaseQuery`，添加分页参数。所有分页查询必须继承 `BasePaginatedQuery`。

Python 后端定义于 `framework/schemas/base.py`，Vue 前端定义于 `framework/types/index.ts`。

#### 场景:BasePaginatedQuery 包含分页参数

- **当** 定义 `BasePaginatedQuery` 类
- **那么** 该类继承 `BaseQuery`
- **那么** 该类必须包含 `page: int = 1` 和 `page_size: int = 20` 字段

#### 场景:实体分页查询继承 BasePaginatedQuery

- **当** 定义实体分页查询类 `XxxPaginatedQuery`（如 `TenantPaginatedQuery`）
- **那么** 该类继承 `XxxQuery` 和 `BasePaginatedQuery`（Python 多继承）或 `XxxQuery` 扩展 `BasePaginatedQuery`（TypeScript）
- **那么** 该类自动拥有实体过滤字段和分页参数

### 需求:实体分页查询命名规范

实体分页查询类必须使用 `{Entity}PaginatedQuery` 命名模式。非分页查询类使用 `{Entity}Query` 命名模式。

#### 场景:分页查询命名

- **当** 定义包含分页参数（page/page_size）的实体查询类
- **那么** 类名必须使用 `{Entity}PaginatedQuery` 格式（如 `TenantPaginatedQuery`、`UserPaginatedQuery`）

#### 场景:非分页查询命名

- **当** 定义不包含分页参数的实体查询类
- **那么** 类名必须使用 `{Entity}Query` 格式（如 `DepartmentQuery`）

### 需求:controller 参数使用 Query 类

后端 controller 中的分页查询接口必须使用 `XxxPaginatedQuery` 接收参数，禁止在方法签名中散落 `page`/`page_size` 参数。

#### 场景:controller 使用 PaginatedQuery 接收参数

- **当** controller 方法需要接收分页查询参数
- **那么** 必须通过 `XxxPaginatedQuery` 类接收，禁止将 `page`/`page_size` 作为独立参数声明

#### 场景:controller 使用 Query 接收非分页参数

- **当** controller 方法仅需过滤条件不需要分页
- **那么** 必须通过 `XxxQuery` 类接收参数

### 需求:前端 Query 类型去重

前端 `XxxQuery` 类型必须只在 `types/index.ts` 中定义一次，禁止在 `api/*.ts` 文件中重复定义。API 文件必须从 types 模块导入。

#### 场景:API 文件导入 Query 类型

- **当** API 函数需要使用 Query 类型
- **那么** 必须从 `../types` 导入，禁止在 API 文件中重新定义同名接口

### 需求:旧基类废弃

`BaseQueryParams`（Python 后端）和 `PageParams`（Vue 前端）必须被 `BaseQuery` + `BasePaginatedQuery` 替代。旧类名禁止在新代码中使用。

#### 场景:BaseQueryParams 不再使用

- **当** 创建新的查询类
- **那么** 禁止继承 `BaseQueryParams`，必须继承 `BaseQuery` 或 `BasePaginatedQuery`

#### 场景:PageParams 不再使用

- **当** 前端代码需要分页参数类型
- **那么** 禁止使用 `PageParams`，必须使用 `BasePaginatedQuery`
