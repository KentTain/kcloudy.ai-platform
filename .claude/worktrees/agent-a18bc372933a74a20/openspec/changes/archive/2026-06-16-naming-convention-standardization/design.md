## 上下文

当前项目前后端通信对象（DTO）命名存在三方面不一致：

1. **后端 Schema 后缀不统一**：tenant 模块使用 `CreateRequest`/`UpdateRequest` + `Vo`，demo 模块使用 `Create`/`Update` + `Vo`，resource_config 使用 `Response`/`ListResponse`
2. **前端类型后缀非标**：广泛使用 `Params`/`QueryParams` 后缀，而非业界通用的 CRUD 命名
3. **CLAUD.md 文档缺失**：web/CLAUDE.md 未定义请求/响应类型命名规范

本次变更为纯重构（rename），不涉及业务逻辑修改。

## 目标 / 非目标

**目标：**
- 统一后端所有模块的 Schema 命名后缀
- 统一前端所有模块的类型命名后缀
- 更新 CLAUDE.md 文档固化规范
- 更新所有引用旧名的代码位置

**非目标：**
- 不改动数据库模型（Model）层
- 不改动 API 路由路径
- 不改动业务逻辑和字段结构

## 决策

### 决策 1：响应对象统一使用 `Response` 而非 `Vo`

- **选择**：`TenantResponse` 而非 `TenantVo`
- **理由**：`Response` 是更通用的业界命名（REST API 惯例），`Vo` 是 Java 生态概念，在 Python/TypeScript 项目中含义不够直观
- **替代方案**：保留 `Vo` — 但与 REST API 的响应语义不直接对应

### 决策 2：请求对象去掉 `Request` 后缀

- **选择**：`TenantCreate` 而非 `TenantCreateRequest`
- **理由**：上下文已表明是请求 Schema，`Request` 后缀冗余；且与前端类型命名对称
- **替代方案**：保留 `Request` 后缀以显式表明用途 — 但 demo 模块已使用无后缀模式，证明无歧义

### 决策 3：前端 `Params` 替换为标准化后缀

- **选择**：`TenantCreate` 而非 `CreateTenantParams`
- **理由**：使用 `{Entity}{Action}` 形式更符合 REST 语义，且与后端命名对齐，降低前后端对接时的认知成本
- **替代方案**：保留 `Create{Entity}Params` — 但前端查询类型已混用 `QueryParams` 后缀，不一致

### 决策 4：采用 `{Action}{Entity}` 形式处理特殊操作

- **选择**：`AssignRoleRequest` 而非 `RoleAssignRequest`
- **理由**：特殊操作（绑定、分配、重置等）以动词开头更自然，且与现有 `UserRegisterRequest` 等模式一致
- **替代方案**：统一所有操作为 `{Entity}{Action}` — 但特殊操作语义各异，动词优先更能体现操作意图

### 完整映射表

| 当前（后端） | 新命名（后端） | 当前（前端） | 新命名（前端） |
|-------------|---------------|-------------|---------------|
| `TenantVo` | `TenantResponse` | `TenantQueryParams` | `TenantQuery` |
| `TenantCreateRequest` | `TenantCreate` | `CreateTenantParams` | `TenantCreate` |
| `TenantUpdateRequest` | `TenantUpdate` | `UpdateTenantParams` | `TenantUpdate` |
| `TenantListVo` | `TenantListResponse` | — | — |
| `*ConfigResponse` | `*PropertyResponse` | `*ConfigQueryParams` | `*ConfigQuery` |
| `*ConfigListResponse` | `*PropertyListResponse` | `Create*Params` | `*Create` |
| `DatasetVo` | `DatasetResponse` | `Update*Params` | `*Update` |
| `DatasetCreate` | 保持不变 | `CreateDatasetParams` | `DatasetCreate` |
| `UserVo` | `UserResponse` | `UpdateDatasetParams` | `DatasetUpdate` |
| `UserListVo` | `UserListResponse` | `LoginRequest` | 保持不变 |
| `LoginVo` | `LoginResponse` | `UserQueryParams` | `UserQuery` |

## 风险 / 权衡

- **[引用遗漏]** → 纯 rename 风险较低，Python 侧使用类名引用，前端 TypeScript 有类型检查
- **[前端与后端类型不同步的风险]** → 前后端类型定义各自独立，本变更同步更新
- **[`*PropertyResponse` 的命名长度]** → 如 `CacheConfigPropertyResponse` 类名偏长，但语义精确可接受

## 迁移计划

1. 更新 CLAUDE.md（规范先行）
2. 后端逐个模块 rename（从依赖最少的模块开始：demo → tenant → iam）
3. 前端逐个模块 rename，同步更新 API/Store/Pages 中的引用
4. 运行类型检查和测试验证
