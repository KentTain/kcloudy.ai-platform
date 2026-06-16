## 为什么

当前项目中 Controller 承担了数据组装职责，导致：
1. 代码重复：多个 Controller 重复调用多个 Service 并手动组装数据
2. 无法复用：其他地方需要相同聚合数据时，无法复用逻辑
3. 性能问题：多次独立数据库查询，缺乏并行优化
4. 职责混乱：Controller 应只负责路由和响应封装，不应包含数据组装逻辑

**为什么现在做**：项目正处于快速迭代阶段，明确 Service 层职责规范可以防止技术债务累积，并为后续开发提供一致的模式参考。

## 变更内容

### Service 层职责增强
- **新增**：Service 层提供聚合方法（如 `get_user_detail()`），返回完整的聚合 Schema
- **新增**：Schema 层提供 `from_entity()` 类方法，处理复杂转换逻辑
- **新增**：Service 层支持 `asyncio.gather` 并行查询优化
- **修改**：Controller 简化为一行调用 Service 聚合方法

### 开发规范更新
- **修改**：将 Service 层职责规范写入 `server/CLAUDE.md` 和 `server/python/CLAUDE.md`
- **新增**：Schema 层转换方法规范

## 功能 (Capabilities)

### 新增功能
- `service-aggregation-pattern`: Service 层聚合方法模式，定义如何组合多个数据源返回完整响应对象
- `schema-conversion-method`: Schema 层转换方法模式，定义 `from_entity()` 类方法处理复杂转换

### 修改功能
无现有功能规范变更，此变更主要填补规范空白。

## 影响

### 受影响的代码
- `iam/services/user_service.py`: 新增 `get_user_detail()` 聚合方法
- `iam/controllers/console/user_controller.py`: 简化 `get_current_user()` 实现
- `ai/controllers/v1/model.py`: 提取转换逻辑到 Schema 层
- `ai/schemas/model.py`: 新增 `from_entity()` 类方法

### 受影响的文档
- `server/CLAUDE.md`: 新增 Service 层职责规范
- `server/python/CLAUDE.md`: 新增 Service 层开发规范

### 兼容性
- 完全向后兼容，现有 API 接口不变
- 新增聚合方法为增量添加，不影响现有 Service 方法
