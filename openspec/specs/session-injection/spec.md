# Session 依赖注入规范

定义数据库 Session 的依赖注入模式，确保所有模块一致使用。

## 新增需求

### 需求:Controller 必须通过依赖注入获取 Session

Controller 层禁止在方法内部创建数据库 Session，必须通过 FastAPI Depends 注入。

#### 场景:Controller 使用依赖注入
- **当** Controller 方法定义 `session: AsyncSession = Depends(get_db_session)` 参数
- **那么** 方法内可直接使用 session 进行数据库操作

#### 场景:事务自动管理
- **当** Controller 方法正常返回
- **那么** Session 事务自动提交
- **当** Controller 方法抛出异常
- **那么** Session 事务自动回滚

### 需求:Service 方法必须接收 Session 参数

Service 层方法禁止内部创建 Session，必须从调用方接收 session 参数。

#### 场景:Service 方法签名
- **当** 定义 Service 方法时
- **那么** 方法签名必须包含 `session: AsyncSession` 参数
- **且** 参数位置在 self 之后、其他参数之前

#### 场景:Service 方法可测试
- **当** 编写 Service 单元测试时
- **那么** 可直接传入 mock session 对象
- **无需** mock async_session 上下文管理器

### 需求:Listener 必须使用专门的 Session 依赖

Listener 层处理消息时必须使用 `get_listener_session()` 或类似依赖函数获取 Session。

#### 场景:Listener 获取 Session
- **当** Listener 处理消息
- **那么** 通过依赖函数获取 Session
- **禁止** 直接使用 `async_session()` 代理

### 需求:Task 必须使用专门的 Session 依赖

Task 层执行定时任务时必须使用 `get_task_session()` 或类似依赖函数获取 Session。

#### 场景:Task 获取 Session
- **当** Task 执行定时任务
- **那么** 通过依赖函数获取 Session
- **禁止** 直接使用 `async_session()` 代理

### 需求:async_session 标记为废弃

`async_session` 代理类必须标记为废弃，并在文档中说明迁移路径。

#### 场景:废弃警告
- **当** 开发者使用 `async_session`
- **那么** IDE 或 linter 显示废弃警告
- **且** 文档明确说明应使用 `Depends(get_db_session)`

### 需求:开发文档必须更新

Python 后端开发文档必须包含 Session 使用规范说明。

#### 场景:文档包含 Session 规范
- **当** 开发者阅读 `server/python/CLAUDE.md`
- **那么** 文档包含 Session 依赖注入使用说明
- **且** 包含正确示例代码
