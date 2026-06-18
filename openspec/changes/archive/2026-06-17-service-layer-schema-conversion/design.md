## 上下文

### 当前状态
项目中存在两种 Service 层模式：
1. **IAM 模式（较好）**：Controller 调用 Service，使用 `UserResponse.model_validate(user)` 自动转换
2. **AI 模块模式（待改进）**：Controller 手动遍历 Entity 构建字典

**问题代码示例** (`iam/controllers/console/user_controller.py:71-122`)：
```python
@router.get("/users/me")
async def get_current_user():
    user = await user_service.get_by_id(user_id)              # 查询 1
    roles = await user_roles_service.get_user_roles(user_id)  # 查询 2
    permissions = await permission_check_service...            # 查询 3
    user_tenants = await user_service.get_user_tenants...     # 查询 4
    tenants_info = await tenant_service.get_tenants_by_ids()  # 查询 5
    # 手动组装 30+ 行代码...
```

### 约束
- 必须保持 API 向后兼容
- 不引入新的抽象层（如独立的 Converter 层）
- 遵循现有的 Pydantic Schema 规范

### 利益相关者
- 后端开发团队
- 前端开发团队（API 不变，无影响）

## 目标 / 非目标

**目标：**
1. Service 层提供聚合方法，返回完整 Schema 对象
2. Schema 层提供 `from_entity()` 类方法处理复杂转换
3. Controller 简化为一行调用
4. 支持并行查询优化性能
5. 更新开发规范文档

**非目标：**
- 不引入独立的 Converter/Mapper 层
- 不改变现有 API 接口签名
- 不涉及缓存策略（后续变更处理）
- 不涉及 Repository 模式引入

## 决策

### 决策 1：Service 返回 Schema 而非 Entity

**选择**：Service 聚合方法直接返回 Pydantic Schema

**理由**：
- Pydantic Schema 已是项目标准
- 减少中间 Entity 类型定义
- Controller 代码极简

**替代方案**：
- 方案 A：Service 返回 Entity + Controller 转换
  - 优点：Service 更"纯粹"
  - 缺点：增加样板代码，Controller 仍有转换职责
- 方案 B：引入独立 Converter 层
  - 优点：职责分离清晰
  - 缺点：增加层级复杂度，项目规模不需要

### 决策 2：Schema 提供 `from_entity()` 类方法

**选择**：在 Schema 中定义类方法处理复杂转换

```python
class UserDetailResponse(BaseModel):
    @classmethod
    def from_user(cls, user: User, roles: list[Role], ...) -> "UserDetailResponse":
        return cls(
            id=user.id,
            roles=[r.code for r in roles],
            ...
        )
```

**理由**：
- 转换逻辑集中在 Schema，易于测试
- 支持计算字段（如 `id=f"{provider}/{model}"`）
- 符合 Pydantic 最佳实践

### 决策 3：Service 内部使用 `asyncio.gather` 并行查询

**选择**：聚合方法内部并行执行独立查询

```python
async def get_user_detail(self, user_id: str) -> UserDetailResponse:
    roles_task = user_roles_service.get_user_roles(user_id)
    permissions_task = permission_check_service.get_user_permissions(user_id)
    tenants_task = self._get_user_tenants_with_detail(user_id)

    roles, permissions, tenants = await asyncio.gather(
        roles_task, permissions_task, tenants_task
    )
    ...
```

**理由**：
- 减少接口响应时间
- 代码清晰，易于理解
- 不引入额外依赖

### 决策 4：Service 调用规则

| 场景 | 规则 |
|------|------|
| 同模块 Service 调用 | ✅ 允许直接调用 |
| 跨模块 Service 调用 | ⚠️ 通过 Inner 接口或框架机制 |
| 聚合方法位置 | 放在"主" Service（如 user_service） |

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| Service 职责变重（包含转换逻辑） | 保持单一职责原则，聚合方法只做数据组装和转换 |
| 跨模块调用可能产生循环依赖 | 明确模块依赖方向：IAM → Tenant（单向），反向通过 Inner 接口 |
| 并行查询增加代码复杂度 | 仅在聚合方法中使用，简单查询保持顺序执行 |
| Schema 类方法可能变长 | 提取私有方法或拆分为多个 Schema 类 |

## 迁移计划

### 第一阶段：示例实现
1. 在 `user_service.py` 实现 `get_user_detail()` 聚合方法
2. 在 `UserDetailResponse` Schema 添加 `from_user()` 方法
3. 简化 `get_current_user()` Controller

### 第二阶段：推广模式
1. 在 `ai/schemas/model.py` 添加 `from_entity()` 方法
2. 简化 `ai/controllers/v1/model.py` 的转换逻辑

### 第三阶段：更新规范
1. 更新 `server/CLAUDE.md` 添加 Service 层职责规范
2. 更新 `server/python/CLAUDE.md` 添加开发规范

### 回滚策略
- 聚合方法为新增代码，不影响现有方法
- 可随时回退到原始 Controller 实现方式
