## ADDED Requirements

### Requirement: Base 模型类
系统 SHALL 提供统一的 SQLAlchemy Base 模型类，包含 UUID 主键、时间戳等通用字段。

#### Scenario: 继承 Base 创建模型
- **WHEN** 定义 `class User(Base):` 并添加自定义字段
- **THEN** 模型自动拥有 `id` (UUID)、`created_at`、`updated_at` 字段

#### Scenario: UUID 自动生成
- **WHEN** 创建模型实例时不指定 `id`
- **THEN** 系统自动生成 UUID 作为主键

### Requirement: Mixin 混入类
系统 SHALL 提供审计、租户、树结构等 Mixin 类，可组合使用。

#### Scenario: 添加审计字段
- **WHEN** 模型添加 `AuditMixin`
- **THEN** 模型获得 `created_by`、`updated_by` 字段

#### Scenario: 添加租户隔离
- **WHEN** 模型添加 `TenantMixin`
- **THEN** 模型获得 `tenant_id` 字段，查询自动过滤租户

#### Scenario: 添加树结构
- **WHEN** 模型添加 `TreeMixin`
- **THEN** 模型获得 `parent_id`、`level`、`path` 字段，支持树形查询

### Requirement: 自定义类型
系统 SHALL 提供 UUID、雪花ID、JSON、枚举等自定义 SQLAlchemy 类型。

#### Scenario: UUID 字符串类型
- **WHEN** 使用 `StringUUID` 类型定义字段
- **THEN** 数据库存储为字符串，Python 中为 UUID 对象

#### Scenario: 雪花ID 类型
- **WHEN** 使用 `BigIntegerSnowflakeID` 类型定义字段
- **THEN** 数据库存储为 BigInteger，Python 中自动生成雪花ID

### Requirement: 查询拦截器
系统 SHALL 提供查询拦截器，自动处理软删除、租户隔离等。

#### Scenario: 软删除过滤
- **WHEN** 模型有 `deleted_at` 字段
- **THEN** 查询自动添加 `deleted_at IS NULL` 条件

#### Scenario: 租户隔离
- **WHEN** 启用租户隔离且当前有租户上下文
- **THEN** 查询自动添加 `tenant_id = ?` 条件

### Requirement: 数据库事件
系统 SHALL 提供数据库事件监听，支持插入、更新、删除前后回调。

#### Scenario: 插入前事件
- **WHEN** 注册 `before_insert` 事件处理器
- **THEN** 插入数据前调用处理器

#### Scenario: 审计日志自动记录
- **WHEN** 启用审计事件
- **THEN** 数据变更自动记录到审计日志表

### Requirement: 树结构操作
系统 SHALL 提供树形结构的常用操作方法。

#### Scenario: 获取子树
- **WHEN** 调用 `node.get_descendants()`
- **THEN** 返回该节点下所有子孙节点

#### Scenario: 移动节点
- **WHEN** 调用 `node.move_to(new_parent)`
- **THEN** 节点移动到新父节点下，更新 path 和 level
