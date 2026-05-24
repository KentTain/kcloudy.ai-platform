## Context

当前项目的租户配置方案（`TenantConfig`）采用扁平键值存储（config_key + JSONB config_value），缺少属性分组、类型元数据和结构化扩展能力。已有 .NET/Java 技术栈使用 `PropertyBase<T>` + `PropertyAttributeBase` 的 EAV 模式管理结构化配置，本设计借鉴该模式核心思想，以 Python/PostgreSQL 方式重新实现。

现有约束：
- 所有模型继承 `BaseModel`（UUID String(36) PK + created_at/updated_at）
- 多租户隔离通过 `TenantMixin` + `TenantQueryInterceptor` + `TenantEventListener` 实现
- 字段命名 snake_case，类命名 PascalCase
- SQLAlchemy 2.0 声明式类型 `Mapped[...] = mapped_column(...)`

## Goals / Non-Goals

**Goals:**

- 在 framework 层提供可复用的属性配置模式抽象（PropertyMixin + PropertyAttributeMixin）
- 在 IAM 模块实现租户级系统配置实体（SystemSetting + SystemSettingAttribute）
- 提供属性取值/提取/类型转换的工具类（PropertyUtil）
- 提供完整的 CRUD API（admin + console）
- 保证多租户数据隔离（两个模型都使用 TenantMixin）

**Non-Goals:**

- 不替换现有 TenantConfig 模型（两者并存）
- 不实现前端 UI（本次只做后端）
- 不做配置热更新/缓存机制（后续迭代）
- 不做配置版本历史/审计追踪（后续迭代）

## Decisions

### 决策 1：纯 EAV 两表模型

**选择**：SystemSetting（容器）+ SystemSettingAttribute（属性值）两张独立表

**理由**：
- 保留 .NET PropertyBase/PropertyAttributeBase 的完整 EAV 结构
- 每个属性值有独立元数据（类型、是否必填、排序）
- 可以按属性粒度查询和管理
- 与 TreeNodeMixin 模式一致：framework 提供抽象，业务模型继承并定义 relationship

**替代方案**：
- JSONB 混合模型（单表 + attributes JSONB 列）：更简单，但丢失属性级元数据和独立查询能力
- 增强 TenantConfig（加 group/data_type 列）：最小改动，但仍是扁平键值，缺少"一组配置"的概念

### 决策 2：JSONB 替代 Ext1-3 字段

**选择**：`value`（Text，主值）+ `ext_data`（JSONB，扩展数据）

**理由**：
- `value` 保持 EAV 的核心简洁性：统一字符串存储 + data_type 指导类型解析
- `ext_data` 用 JSONB 处理 .NET 中 Ext1-3 的扩展需求，一个字段替代三个扁平字段
- 职责分明：简单值用 value，复杂结构用 ext_data

### 决策 3：AttributeDataType 使用 str, Enum

**选择**：直接使用 `str, Enum`（不继承 EnumBase）

**理由**：
- EnumBase 当前定义在 demo/models/enums.py（业务模块），framework 不应依赖业务模块
- IAM 的 TenantStatus 已采用 `str, Enum` 直接继承的模式
- AttributeDataType 是 framework 级别枚举，放在 property.py 同文件

**替代方案**：先将 EnumBase 下沉到 framework/common/ —— 改动范围大，本次不做

### 决策 4：SystemSettingAttribute 也加 TenantMixin

**选择**：两个模型都继承 TenantMixin

**理由**：
- TenantQueryInterceptor 对所有有 tenant_id 的模型一致过滤
- TenantEventListener 自动注入 tenant_id
- admin 跨租户查询通过 set_skip_tenant(True) 控制
- 一个冗余 tenant_id 列换来全链路一致性，值得

### 决策 5：PropertyUtil 替代 PropertyMapperBase

**选择**：PropertyUtil 静态工具类，提供取值/提取/类型转换

**理由**：
- .NET 的 CheckNotEmpty/IsDateTime/IsInt 等校验 → Python 由 Pydantic Schema 在 API 层处理
- .NET 的 GetPropertyValueByKey/GetPropertyAttributesByPropertyName → PropertyUtil 的取值方法
- .NET 的类型校验 → PropertyUtil.coerce_value() 基于 AttributeDataType 转换
- 不需要独立的 MapperBase 类，Python 的 Pydantic + 工具类组合更自然

### 决策 6：两个 Mixin 放在同一文件

**选择**：PropertyMixin 和 PropertyAttributeMixin 放在 framework/database/mixins/property.py

**理由**：
- 两个 mixin 紧密配套（容器 + 属性值），同一文件便于维护
- AttributeDataType 枚举也放在同文件（与 mixin 紧密关联）
- 项目已有类似模式：TreeNodeMixin + TreeMixin alias 在同一 tree.py

## Risks / Trade-offs

- **[EAV 查询复杂度]** → 读一个完整配置需要 join 或 selectin 加载。Mitigation：relationship 使用 `lazy="selectin"` 避免 N+1
- **[tenant_id 冗余]** → SystemSettingAttribute 的 tenant_id 与父实体的 tenant_id 重复。Mitigation：TenantEventListener 保证一致性，冗余换取全局租户过滤的一致性
- **[value 字符串存储]** → 所有值存为字符串，类型转换依赖 AttributeDataType 和 PropertyUtil.coerce_value。Mitigation：Pydantic 在 API 层做二次校验，类型转换失败抛异常
- **[与 TenantConfig 并存]** → 两套配置模型可能造成使用者困惑。Mitigation：文档明确区分：TenantConfig 适合简单键值，SystemSetting 适合结构化分组配置