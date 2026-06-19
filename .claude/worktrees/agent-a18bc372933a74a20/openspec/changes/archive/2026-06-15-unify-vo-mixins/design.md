## 上下文

### 当前状态

项目中存在两套并行的 VO 体系：

```
framework/common/schemas.py:
├── BaseModel (Pydantic 基类)
├── VoMixin (VO 基类)
├── TreeNodeVoMixin (树结构 Mixin，未被使用)
└── AuditedOperatorVoMixin (审计 Mixin)

framework/schemas/tree.py:
├── TreeNodeVo (直接继承 Pydantic BaseModel)
└── TreeNodeTreeVo (继承 TreeNodeVo)
```

问题：
1. `TreeNodeVoMixin` 与 `TreeNodeVo` 字段重复
2. ORM 层有 `PropertyMixin`/`PropertyAttributeMixin`，VO 层缺少对应实现

### 约束

- 保持 API 响应格式不变
- 遵循项目现有的 Mixin 组合模式
- 所有 VO 类应继承自 `VoMixin`

## 目标 / 非目标

**目标：**
- 统一 VO 继承体系，所有 VO 基类继承 `VoMixin`
- 新增 `PropertyVoMixin` 和 `PropertyAttributeVoMixin`
- 保持向后兼容，现有代码无需修改

**非目标：**
- 不修改 ORM 层的 Mixin
- 不改变现有 API 的响应格式
- 不创建新的业务实体

## 决策

### 决策 1：TreeNodeVo 重构为组合模式

**选择：** `TreeNodeVo(VoMixin, TreeNodeVoMixin)` 多重继承

**理由：**
- 符合项目现有的 Mixin 组合模式（如 `SystemSetting(BaseModel, TenantMixin, PropertyMixin)`）
- 保持 `TreeNodeVoMixin` 可独立复用
- `TreeNodeVo` 添加 `id` 字段，形成完整的节点 VO

**替代方案：**
- 直接让 `TreeNodeVoMixin` 包含 `id` 字段 → 拒绝，因为 Mixin 应只提供能力扩展，不应包含实体标识

### 决策 2：PropertyVoMixin 字段设计

**选择：** 与 ORM 层 `PropertyMixin` 字段一一对应

```python
class PropertyVoMixin(VoMixin):
    name: str
    display_name: str | None = None
    description: str | None = None
    can_edit: bool = True
    is_require: bool = False
    index: int = 0
```

**理由：**
- 保持 ORM 与 VO 层的一致性
- 使用 `Field()` 添加 description，增强 OpenAPI 文档

### 决策 3：PropertyAttributeVoMixin 字段设计

**选择：** 与 ORM 层 `PropertyAttributeMixin` 字段一一对应

```python
class PropertyAttributeVoMixin(VoMixin):
    data_type: str = "string"
    name: str
    display_name: str | None = None
    description: str | None = None
    value: str | None = None
    ext_data: dict | None = None
    can_edit: bool = True
    is_require: bool = False
    index: int = 0
```

**理由：**
- `data_type` 默认 `"string"` 对应 ORM 层的 `AttributeDataType.STRING.value`
- `ext_data` 使用 `dict | None` 对应 ORM 层的 `JSONB`

### 决策 4：文件组织

**选择：** 新增 Mixin 放在 `framework/common/schemas.py`

**理由：**
- 与现有 `TreeNodeVoMixin`、`AuditedOperatorVoMixin` 放在同一文件
- 保持 framework 层 VO 基类的集中管理
- `framework/schemas/__init__.py` 负责导出

### 决策 5：重构现有 Property 相关 VO

**选择：** 将 `SystemSettingResponse` 等 VO 改为使用 Mixin

**现状分析：**

```python
# 当前 SystemSettingResponse（重复定义字段）
class SystemSettingResponse(BaseModel):
    id: str
    tenant_id: str
    code: str
    name: str                    # ← PropertyMixin 字段
    display_name: str | None     # ← PropertyMixin 字段
    description: str | None      # ← PropertyMixin 字段
    can_edit: bool               # ← PropertyMixin 字段
    is_require: bool             # ← PropertyMixin 字段
    index: int                   # ← PropertyMixin 字段
    ...
```

**重构后：**

```python
# 使用 PropertyVoMixin
class SystemSettingResponse(VoMixin, PropertyVoMixin):
    id: str
    tenant_id: str
    code: str
    application_id: str | None
    application_name: str | None
    attributes: list[SystemSettingAttributeResponse]
    created_at: datetime
    updated_at: datetime
```

**理由：**
- 消除字段重复定义
- 保持 ORM 层与 VO 层的一致性
- 减少维护成本

**涉及文件：**
| 文件 | VO 类 | 使用的 Mixin |
|------|-------|-------------|
| `iam/schemas/admin/system_setting.py` | `SystemSettingResponse` | `PropertyVoMixin` |
| `iam/schemas/admin/system_setting.py` | `SystemSettingAttributeResponse` | `PropertyAttributeVoMixin` |
| `iam/schemas/console/system_setting.py` | `ConsoleSystemSettingResponse` | `PropertyVoMixin` |
| `iam/schemas/console/system_setting.py` | `ConsoleSystemSettingAttributeResponse` | `PropertyAttributeVoMixin` |

## 风险 / 权衡

### 风险 1：继承链变更导致序列化行为变化

**风险：** TreeNodeVo 改为多重继承后，Pydantic 序列化行为可能有细微差异

**缓解措施：**
- 保持 `model_config = ConfigDict(from_attributes=True)` 配置
- 编写单元测试验证序列化输出

### 风险 2：字段默认值不一致

**风险：** Mixin 默认值与 ORM 层默认值不一致

**缓解措施：**
- 对照 ORM Mixin 的 `mapped_column(default=...)` 设置相同的 Pydantic `Field(default=...)`

### 权衡：兼容性 vs 清晰性

- 选择保持兼容性：TreeNodeVo 字段签名不变
- 现有代码无需修改即可继续使用

## 迁移计划

### 阶段 1：新增 Mixin（无破坏性）
1. 在 `framework/common/schemas.py` 添加 `PropertyVoMixin`、`PropertyAttributeVoMixin`
2. 更新 `framework/schemas/__init__.py` 导出

### 阶段 2：重构 TreeNodeVo
1. 修改 `TreeNodeVo` 继承 `VoMixin, TreeNodeVoMixin`
2. 添加 `id` 字段
3. 运行测试验证

### 阶段 3：重构现有 Property 相关 VO
1. 重构 `iam/schemas/admin/system_setting.py` 中的 Response 类
2. 重构 `iam/schemas/console/system_setting.py` 中的 Response 类
3. 验证 API 响应格式不变

### 阶段 4：验证
1. 运行现有单元测试
2. 手动验证 API 响应格式

### 回滚策略
- Git revert 即可回滚，无数据库迁移
