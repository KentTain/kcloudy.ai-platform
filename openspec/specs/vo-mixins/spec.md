# vo-mixins 规范

## 目的
待定 - 由归档变更 unify-vo-mixins 创建。归档后请更新目的。
## 需求
### 需求:统一 VO 基类继承体系

所有 VO（View Object）模型必须继承自 `VoMixin` 基类，确保统一的序列化配置和行为。

#### 场景:TreeNodeVo 继承 VoMixin
- **当** 定义 TreeNodeVo 类时
- **那么** 必须继承 `VoMixin` 和 `TreeNodeVoMixin`
- **并且** 必须包含 `id` 字段

#### 场景:VoMixin 提供 from_attributes 配置
- **当** ORM 模型转换为 VO 时
- **那么** 必须自动支持 `from_attributes=True` 配置

### 需求:PropertyVoMixin 提供属性容器字段

系统必须提供 `PropertyVoMixin`，用于属性类 VO 的复用。

#### 场景:PropertyVoMixin 包含完整字段
- **当** 使用 PropertyVoMixin 时
- **那么** 必须包含以下字段：
  - `name: str` - 名称
  - `display_name: str | None` - 显示名称
  - `description: str | None` - 描述
  - `can_edit: bool` - 是否可编辑（默认 True）
  - `is_require: bool` - 是否必填（默认 False）
  - `index: int` - 排序号（默认 0）

#### 场景:PropertyVoMixin 继承 VoMixin
- **当** 定义 PropertyVoMixin 时
- **那么** 必须继承 `VoMixin`

### 需求:PropertyAttributeVoMixin 提供属性值字段

系统必须提供 `PropertyAttributeVoMixin`，用于属性值 VO 的复用。

#### 场景:PropertyAttributeVoMixin 包含完整字段
- **当** 使用 PropertyAttributeVoMixin 时
- **那么** 必须包含以下字段：
  - `data_type: str` - 数据类型（默认 "string"）
  - `name: str` - 属性名称
  - `display_name: str | None` - 显示名称
  - `description: str | None` - 描述
  - `value: str | None` - 属性值
  - `ext_data: dict | None` - 扩展数据
  - `can_edit: bool` - 是否可编辑（默认 True）
  - `is_require: bool` - 是否必填（默认 False）
  - `index: int` - 排序号（默认 0）

#### 场景:PropertyAttributeVoMixin 继承 VoMixin
- **当** 定义 PropertyAttributeVoMixin 时
- **那么** 必须继承 `VoMixin`

### 需求:TreeNodeVoMixin 与 TreeNodeVo 分离

`TreeNodeVoMixin` 必须保持独立，可被其他需要树结构能力的 VO 复用。

#### 场景:TreeNodeVoMixin 可独立使用
- **当** 定义一个需要树结构字段的 VO 时
- **那么** 可以单独继承 `TreeNodeVoMixin` 而不继承 `TreeNodeVo`

#### 场景:TreeNodeVo 组合 Mixin
- **当** 使用 TreeNodeVo 时
- **那么** 必须自动获得 `VoMixin` 和 `TreeNodeVoMixin` 的所有能力
- **并且** 必须包含 `id` 字段

### 需求:向后兼容

变更必须保持向后兼容，现有使用 TreeNodeVo 的代码无需修改。

#### 场景:现有 VO 继续工作
- **当** 现有代码使用 TreeNodeVo 作为响应模型时
- **那么** API 响应格式必须保持不变

#### 场景:字段签名不变
- **当** 访问 TreeNodeVo 实例的字段时
- **那么** 必须支持与变更前相同的字段名称和类型

