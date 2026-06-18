## 新增需求

### 需求:Service 聚合方法返回完整 Schema 对象

Service 层必须提供聚合方法，用于组合多个数据源并返回完整的响应 Schema 对象。聚合方法负责协调多个 Service 调用、并行查询优化和数据组装。

#### 场景:获取用户详情聚合数据
- **当** Controller 调用 `user_service.get_user_detail(user_id)`
- **那么** Service 必须返回包含用户基础信息、角色、权限、租户列表的完整 `UserDetailResponse` 对象

#### 场景:并行查询优化
- **当** 聚合方法需要调用多个独立的 Service 方法
- **那么** 必须使用 `asyncio.gather` 并行执行这些调用

#### 场景:数据不存在时返回 None
- **当** 主实体（如用户）不存在
- **那么** 聚合方法必须返回 `None`，不执行后续查询

### 需求:Controller 简化为一行调用

Controller 必须只负责调用 Service 聚合方法并返回响应，禁止包含数据组装逻辑。

#### 场景:Controller 调用聚合方法
- **当** Controller 需要返回聚合数据
- **那么** 必须只调用一个 Service 方法，如 `await user_service.get_user_detail(user_id)`

#### 场景:Controller 不包含数据组装
- **当** Controller 需要组合多个数据源
- **那么** 禁止在 Controller 中调用多个 Service 并手动组装数据

### 需求:Service 同模块调用规则

同模块内的 Service 可以直接相互调用，跨模块调用必须通过 Inner 接口。

#### 场景:同模块 Service 调用
- **当** IAM 模块的 `user_service` 需要调用 `role_service`
- **那么** 必须直接导入并调用

#### 场景:跨模块 Service 调用
- **当** IAM 模块的 Service 需要调用 Tenant 模块的 Service
- **那么** 必须通过 `/tenant/inner/v1` 接口调用，禁止直接导入

### 需求:聚合方法命名规范

聚合方法必须使用明确的命名，表明返回的是完整聚合对象。

#### 场景:聚合方法命名
- **当** Service 提供聚合方法
- **那么** 方法名必须为 `get_<entity>_detail` 或 `get_<entity>_full`，如 `get_user_detail()`

#### 场景:聚合方法返回类型
- **当** 聚合方法返回数据
- **那么** 返回类型必须是对应的响应 Schema 类型，如 `UserDetailResponse | None`
