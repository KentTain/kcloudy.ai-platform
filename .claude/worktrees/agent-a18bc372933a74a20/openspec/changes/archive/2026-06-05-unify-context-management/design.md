## 上下文

### 当前状态

当前系统存在两套独立的上下文管理机制：

1. **TenantContext** (`framework/tenant/context.py`)
   - 存储：独立的 `_tenant_context: ContextVar[SimpleTenant | None]`
   - 功能：租户信息 + 租户配置（database_config, storage_config, cache_config）
   - 使用场景：中间件、任务执行器、租户切换

2. **Context** (`framework/common/ctx.py`)
   - 存储：独立的 `_context_var: ContextVar[Context | None]`
   - 功能：用户信息（user_id, user_name, roles）+ 租户 ID
   - 使用场景：Service 层、ORM 事件、拦截器

### 问题

- **用户信息缺失**：`IAMAuthMiddleware` 未注册，用户信息仅存在于 `request.state`，未同步到 `Context`
- **双重存储**：租户信息在两套系统中重复存储，存在不一致风险
- **测试用户混乱**：`X-User-Id` 请求头语义不清，易与生产环境混淆

### 约束

- 必须保持向后兼容，现有 `TenantContext` 调用无需修改
- Service 层使用习惯（`get_user_id()`, `get_tenant_id()`）保持不变
- ORM 事件（`before_insert`, `before_update`）只能使用 `ContextVar`

## 目标 / 非目标

**目标：**
- 统一上下文存储到单一的 `_context_var`，消除双重存储
- 在生产环境正确设置用户信息到 `Context`
- 提供安全的开发测试机制（`X-Test-User-Id`）
- 保持现有 API 和代码调用习惯不变

**非目标：**
- 不改变 ORM 事件、拦截器等现有使用 `Context` 的代码
- 不改变 Service 层获取用户/租户信息的方式
- 不引入新的外部依赖

## 决策

### 决策 1：统一使用 ContextVar

**选择**：将所有上下文信息（用户 + 租户）统一存储到 `_context_var`

**理由**：
- `ContextVar` 协程安全，适合异步环境
- ORM 事件只能访问 `ContextVar`，不能访问 `request.state`
- 单一数据源，避免不一致

**替代方案**：
- 方案 A：统一使用 `request.state` → ✗ ORM 事件无法访问
- 方案 B：保持双系统，增加同步逻辑 → ✗ 增加复杂度和出错风险
- 方案 C：统一使用 `ContextVar` → ✓ 选择此方案

### 决策 2：TenantContext 改造为适配器

**选择**：`TenantContext` 成为 `Context` 的适配器，底层读取 `_context_var`

**理由**：
- 保持向后兼容，现有代码无需修改
- 单一数据源，避免不一致
- 逐步迁移的风险最低

**实现**：
```python
class TenantContext:
    @staticmethod
    def get_tenant_id() -> str | None:
        ctx = get_context()
        return ctx.tenant_id
    
    @staticmethod
    def set_current_tenant(tenant: Any) -> None:
        ctx = get_context()
        ctx.tenant_id = tenant.id
        ctx.tenant_name = tenant.name
        ctx.tenant_code = tenant.code
        # 租户配置存到 extra
        if hasattr(tenant, 'database'):
            ctx.extra['database_config'] = tenant.database
```

### 决策 3：中间件执行顺序

**选择**：`TenantMiddleware` → `IAMAuthMiddleware` → `TestUserMiddleware`

**理由**：
1. 先解析租户（`TenantMiddleware`）
2. 再验证用户并校验租户归属（`IAMAuthMiddleware`）
3. 最后允许测试用户覆盖（`TestUserMiddleware`，仅开发环境）

**执行流程**：
```
Request
  │
  ├─▶ TenantMiddleware
  │     • 解析 X-Tenant-Id 或域名
  │     • 验证租户状态
  │     • 设置租户信息到 Context
  │
  ├─▶ IAMAuthMiddleware
  │     • 验证 JWT Token
  │     • 验证用户租户归属
  │     • 设置用户信息到 Context
  │
  ├─▶ TestUserMiddleware (仅非生产环境)
  │     • 检查 X-Test-User-Id 请求头
  │     • 覆盖用户信息
  │
  └─▶ Business Logic
```

### 决策 4：Context 类扩展

**选择**：扩展 `Context` 类，添加租户完整信息

**理由**：
- 类型安全，IDE 提示友好
- 支持未来租户配置需求

**字段设计**：
```python
@dataclass
class Context:
    # 用户信息
    user_id: str | None = None
    user_name: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    
    # 租户信息
    tenant_id: str | None = None
    tenant_name: str | None = None
    tenant_code: str | None = None
    
    # 其他
    workspace_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)  # 租户配置等
```

### 决策 5：测试用户安全机制

**选择**：`X-Test-User-Id` 仅在非生产环境生效

**理由**：
- 明确语义，避免与生产环境混淆
- 环境检查，防止生产环境滥用

**实现**：
```python
class TestUserMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, enabled: bool = False):
        super().__init__(app)
        self.enabled = enabled
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # 仅在非生产环境且启用时生效
        if not self.enabled or settings.ENV == "production":
            return response
        
        test_user_id = request.headers.get("X-Test-User-Id")
        if test_user_id:
            ctx = get_context()
            ctx.user_id = test_user_id
            _logger.warning(f"使用测试用户: {test_user_id}")
        
        return response
```

## 风险 / 权衡

### 风险 1：中间件注册顺序错误
- **风险**：如果顺序错误，租户信息可能未设置导致用户验证失败
- **缓解**：在代码注释中明确说明注册顺序，并在 `application_web.py` 中添加检查逻辑

### 风险 2：向后兼容性破坏
- **风险**：`TenantContext` 改造可能影响现有行为
- **缓解**：保持 API 不变，增加单元测试验证兼容性

### 风险 3：测试用户功能被滥用
- **风险**：开发人员可能误用于生产环境
- **缓解**：
  - 环境检查（仅非生产环境生效）
  - 日志警告
  - 文档明确说明用途

### 权衡 1：Context 类变重
- **权衡**：Context 类字段增多，职责扩大
- **理由**：单一数据源的价值大于类的复杂度增加

### 权衡 2：租户配置存储在 extra
- **权衡**：租户配置（database_config 等）存储在 `extra` 字典中，类型不安全
- **理由**：这些配置目前未被使用，未来可根据需求迁移到强类型字段

## 迁移计划

### 阶段 1：基础设施改造
1. 扩展 `Context` 类（添加 tenant_name, tenant_code 等）
2. 改造 `TenantContext` 为适配器
3. 编写单元测试验证兼容性

### 阶段 2：中间件重构
1. 重构 `TenantMiddleware`（移除测试用户逻辑）
2. 重构 `IAMAuthMiddleware`（同步用户信息到 Context）
3. 新增 `TestUserMiddleware`
4. 调整中间件注册顺序

### 阶段 3：测试和验证
1. 运行所有单元测试和集成测试
2. 手动验证用户信息正确设置
3. 验证开发测试场景（X-Test-User-Id）

### 阶段 4：清理和文档
1. 移除废弃代码（如有）
2. 更新文档和注释

### 回滚策略
- 如出现问题，可通过 Git 回滚到变更前版本
- 中间件注册顺序可通过配置快速调整
- TenantContext 改造为适配器，可快速切换回独立存储

## 开放问题

暂无待定决策。
