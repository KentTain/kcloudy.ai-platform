## 为什么

当前项目中存在两种数据库 Session 使用模式：Demo 模块使用依赖注入模式（推荐），而 IAM、Tenant、AI 模块仍在使用 `async_session()` 代理模式。这种不一致导致：
- 代码风格不统一，增加维护成本
- Service 层难以进行单元测试（需要 mock 上下文管理器）
- 违反依赖倒置原则，Service 直接依赖基础设施层

统一为依赖注入模式可提高代码可测试性、一致性和可维护性。

## 变更内容

- 将所有 Service 层方法从 `async with async_session() as session:` 改为接收 `session: AsyncSession` 参数
- Controller 层使用 `Depends(get_db_session)` 注入 session 并传递给 Service
- Listener 和 Task 通过专门的依赖函数获取 session
- 标记 `async_session` 为废弃，保留向后兼容

## 功能 (Capabilities)

### 新增功能

- `session-injection`: 统一的数据库 Session 依赖注入模式，涵盖 Controller、Service、Listener、Task 各层

### 修改功能

无新增功能，纯重构变更。

## 影响

### 受影响的代码

| 模块 | 文件数 | `async_session()` 调用次数 |
|------|--------|---------------------------|
| iam | ~13 | ~85 处 |
| tenant | ~8 | ~75 处 |
| ai | ~6 | ~20 处 |
| framework | ~3 | ~7 处 |
| **合计** | **~30** | **~187 处** |

### 受影响的 API 端点

所有 `/iam/*`、`/tenant/*`、`/ai/*` 下的 API 端点行为保持不变，仅内部实现方式变更。

### 兼容性考虑

- `async_session` 代理类保留，标记为废弃
- 现有代码可逐步迁移，无需一次性全部修改
