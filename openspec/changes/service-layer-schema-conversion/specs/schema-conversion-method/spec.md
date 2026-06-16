## 新增需求

### 需求:Schema 提供 from_entity 类方法

Schema 必须提供 `from_entity()` 类方法，用于处理复杂转换逻辑。简单转换使用 Pydantic 的 `from_attributes=True` 配置。

#### 场景:简单字段映射
- **当** Schema 字段与 Entity 字段一一对应
- **那么** 必须使用 `model_config = ConfigDict(from_attributes=True)` 自动映射

#### 场景:复杂字段转换
- **当** Schema 字段需要计算、拼接或其他转换逻辑
- **那么** 必须提供 `from_entity()` 类方法处理转换

#### 场景:计算字段示例
- **当** 模型 ID 需要拼接为 `{provider}/{model}` 格式
- **那么** `from_entity()` 方法必须处理拼接逻辑
```python
@classmethod
def from_entity(cls, provider: str, model: ProviderModel) -> "ModelItem":
    return cls(
        id=f"{provider}/{model.model}",
        name=model.model,
        description=model.label.zh_Hans or model.label.en_US,
    )
```

### 需求:Schema 转换方法参数规范

`from_entity()` 方法的参数必须清晰表达所需的数据源。

#### 场景:单实体转换
- **当** 只需要一个 Entity 即可完成转换
- **那么** 方法签名必须为 `from_entity(cls, entity: EntityType) -> "SchemaType"`

#### 场景:多数据源转换
- **当** 需要多个数据源完成转换
- **那么** 方法签名必须明确列出所有参数，如 `from_user(cls, user: User, roles: list[Role], ...)`

### 需求:Schema 转换方法禁止包含业务逻辑

`from_entity()` 方法必须只包含字段映射和简单计算，禁止包含数据库查询或业务规则验证。

#### 场景:允许的计算逻辑
- **当** 转换需要字符串拼接、类型转换、默认值处理
- **那么** 必须在 `from_entity()` 方法中处理

#### 场景:禁止的数据库查询
- **当** 转换需要查询关联数据
- **那么** 必须由 Service 层查询后传入，禁止在 Schema 中查询

#### 场景:禁止的业务规则
- **当** 转换需要验证业务规则
- **那么** 必须在 Service 层处理，Schema 只负责数据转换

### 需求:Schema 响应类型命名规范

聚合响应 Schema 必须使用明确的命名，表明这是完整聚合对象。

#### 场景:聚合响应命名
- **当** Schema 包含多个数据源的聚合数据
- **那么** 必须命名为 `{Entity}DetailResponse`，如 `UserDetailResponse`

#### 场景:简单响应命名
- **当** Schema 只包含单个 Entity 的数据
- **那么** 必须命名为 `{Entity}Response`，如 `UserResponse`
