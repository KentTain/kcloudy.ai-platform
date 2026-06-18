## 上下文

当前项目存在两种数据库 Session 使用模式：

1. **依赖注入模式（Demo 模块）**：Controller 通过 `Depends(get_db_session)` 注入 session，传递给 Service 方法
2. **Session Proxy 模式（IAM/Tenant/AI 模块）**：Service 方法内部使用 `async with async_session() as session:`

Session Proxy 模式的问题：
- 每个方法需要重复 `async with async_session()` 样板代码
- Service 难以单元测试（需要 mock 上下文管理器）
- 事务边界在 Service 内部管理，增加复杂度
- 违反依赖倒置原则

## 目标 / 非目标

**目标：**
- 统一所有模块使用依赖注入模式
- 提高 Service 层可测试性
- 保持 API 行为不变
- 更新开发文档，明确 Session 使用规范

**非目标：**
- 不修改数据库连接池实现
- 不改变多租户隔离机制
- 不修改事务管理策略

## 决策

### 决策 1：Controller 层统一使用 `Depends(get_db_session)`

**选择：** 在 Controller 路由处理函数中通过 FastAPI Depends 注入 session

**理由：**
- 与 Demo 模块保持一致
- FastAPI 原生支持，事务由框架管理
- session 生命周期与 HTTP 请求绑定

**替代方案：**
- 方案 A（已拒绝）：保留 Session Proxy 模式 - 不一致，难以测试
- 方案 B（已拒绝）：在每个 Service 构造函数注入 session - 需要大量重构，且 Service 为单例模式不适用

### 决策 2：Service 方法签名统一添加 `session: AsyncSession` 参数

**选择：** Service 方法接收 session 作为第一个参数（self 之后）

**模式：**
```python
class XxxService:
    async def method(self, session: AsyncSession, ...) -> ...:
        # 使用 session
```

**理由：**
- 纯函数式设计，易于测试
- session 由调用方提供，依赖倒置

### 决策 3：Listener 和 Task 使用专门的依赖函数

**选择：** 创建 `get_listener_session()` 和 `get_task_session()` 依赖函数

**理由：**
- Listener/Task 没有 HTTP 请求上下文
- 需要独立的 session 管理
- 保持与 Controller 类似的注入模式

### 决策 4：保留 `async_session` 作为废弃兼容层

**选择：** 保留 `_SessionProxy` 类，添加废弃警告

**理由：**
- 渐进式迁移，避免一次性大规模修改
- 给予团队适应时间

## 风险 / 权衡

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 大规模代码修改可能引入 bug | 高 | 按模块逐步迁移，每个模块完成后运行测试 |
| 迁移期间代码风格不一致 | 低 | 在文档中明确推荐模式，新代码强制使用依赖注入 |
| Listener/Task 迁移复杂度 | 中 | 提供专门的依赖函数，参考 Demo 模块实现 |

## 迁移计划

### 阶段 1：基础设施准备
1. 确认 `get_db_session` 依赖函数正确工作
2. 创建 `get_listener_session()` 和 `get_task_session()` 依赖函数（如需要）
3. 标记 `async_session` 为废弃

### 阶段 2：按模块迁移（建议顺序）
1. **tenant 模块**：基础模块，无其他业务依赖
2. **iam 模块**：依赖 tenant
3. **ai 模块**：依赖 tenant 和 iam
4. **framework 模块**：仅迁移 clients/ 目录

### 阶段 3：清理
1. 移除废弃的 `async_session` 兼容层
2. 更新文档

### 回滚策略
- 每个模块迁移完成后独立提交
- 出现问题可回滚单个模块的提交
