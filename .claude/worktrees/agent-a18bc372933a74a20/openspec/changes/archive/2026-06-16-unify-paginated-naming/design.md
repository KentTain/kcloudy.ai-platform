## 上下文

当前前后端通信对象（DTO）命名存在语义模糊：
- `BaseQueryParams` 同时承担分页基类职责，但命名未体现
- `XxxQuery` 无法区分是否含分页参数
- `XxxListResponse` 无法区分是分页列表还是全量列表
- 部分分页型响应缺失 `page`/`page_size` 字段

涉及模块：
- Python 后端：framework、tenant、iam、demo、ai 模块
- Vue 前端：framework、iam、tenant、ai 模块
- Rust 后端：demo 模块

## 目标 / 非目标

**目标：**
1. 建立清晰的查询对象继承体系：`BaseQuery` → `BasePaginatedQuery`
2. 建立清晰的响应对象命名规范：`XxxListResponse`（全量） vs `XxxPaginatedListResponse`（分页）
3. 统一分页响应字段：items + total + page + page_size
4. 前后端命名保持一致
5. 消除前端 Query 类型重复定义

**非目标：**
1. 不改变 API 端点路径
2. 不改变数据库结构
3. 不涉及非分页场景（树形查询、单条查询等）

## 决策

### 决策 1：查询对象继承体系

**选择**：单继承 + Mixin 模式

```
BaseQuery                     # 公共过滤字段基类（可选，如 keyword）
└── BasePaginatedQuery        # 分页基类，继承 BaseQuery，添加 page/page_size

TenantQuery                   # 租户查询，继承 BaseQuery，添加 status 等
└── TenantPaginatedQuery      # 租户分页查询，继承 TenantQuery + BasePaginatedQuery
```

**替代方案**：
- A. 组合模式（XxxQuery 内含 Pagination 对象）→ 放弃，破坏现有结构
- B. 多继承（XxxPaginatedQuery 继承 XxxQuery 和 BasePaginatedQuery）→ 采用

**理由**：多继承在 Python 中简单直接，TypeScript 使用 extends + 交叉类型也可实现。

### 决策 2：响应对象命名

**选择**：
- 分页列表：`XxxPaginatedListResponse`（含 items + total + page + page_size）
- 全量列表：`XxxListResponse`（仅 items 或 items + total）

**替代方案**：
- A. `XxxPageResponse` → 放弃，Page 容易与前端页面组件混淆
- B. `XxxPaginated` → 放弃，形容词作为类名不够直观

**理由**：`PaginatedListResponse` 明确表达"分页的列表响应"，语义清晰。

### 决策 3：缺失字段补齐策略

**选择**：在重命名时统一补齐 `page` 和 `page_size` 字段

**理由**：
- 分页响应必须包含完整分页元数据，否则前端无法计算总页数
- 保持一致性，避免前端需要判断响应格式

### 决策 4：前端泛型命名

**选择**：`PaginatedListResponse<T>`

**替代方案**：
- A. `PageResult<T>` → 放弃，与后端命名不一致
- B. `Paginated<T>` → 放弃，过于简洁，语义不如完整命名清晰

**理由**：与后端实体级 `XxxPaginatedListResponse` 命名一致，便于理解和维护。

## 风险 / 权衡

### 风险 1：破坏性变更影响 API 兼容性

**风险**：前端调用 API 时，响应类型名变化可能导致类型检查失败

**缓解措施**：
- 此变更为重命名，运行时行为不变
- TypeScript 编译时会提示类型错误，易于发现和修复
- 需同步更新所有引用点

### 风险 2：后端 IAM controller 散落参数改动量大

**风险**：将 `page: int = 1, page_size: int = 20` 改为 Query 对象，涉及多个 controller 方法签名变化

**缓解措施**：
- FastAPI 的 Depends 注入方式，改动量可控
- 逐个 controller 文件修改，避免遗漏

### 风险 3：继承链复杂度增加

**风险**：多继承可能导致钻石问题或理解成本

**缓解措施**：
- Python MRO 明确，无钻石问题
- TypeScript 使用交叉类型，语义清晰
- 在 BaseQuery 中只放通用过滤字段（如 keyword），避免过度抽象

## 迁移计划

### 阶段 1：后端基类创建（Python）
1. 创建 `BaseQuery` 和 `BasePaginatedQuery`
2. 标记 `BaseQueryParams` 为 deprecated（保留兼容）

### 阶段 2：后端响应重命名（Python）
1. 重命名所有分页型 `XxxListResponse` → `XxxPaginatedListResponse`
2. 补齐缺失的 `page`/`page_size` 字段
3. 更新所有引用（controller、service）

### 阶段 3：后端 controller 参数统一（Python）
1. 创建 `XxxPaginatedQuery` 类
2. 修改 controller 方法签名，使用 Depends 注入 Query 对象

### 阶段 4：前端类型重构（Vue）
1. 创建 `BaseQuery` + `BasePaginatedQuery`
2. 重命名 `PageResult<T>` → `PaginatedListResponse<T>`
3. 重命名实体 Query，删除重复定义
4. 更新所有 API 调用

### 阶段 5：Rust 后端同步
1. 重命名 `PageRequest` → `BasePaginatedQuery`
2. 重命名 `PageResponse<T>` → `PaginatedListResponse<T>`

### 阶段 6：文档更新
1. 更新 `server/CLAUDE.md` DTO 命名规范表
2. 更新 `web/CLAUDE.md` DTO 命名规范表

## 待解决问题

无。
