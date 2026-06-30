# ProviderManager 完全重写设计规格

## 1. 概述

### 1.1 背景

在完成插件系统与模型配置整合（`2026-06-30-plugin-model-simplification`）后，`ProviderManager` 中仍存在以下问题：

1. **废弃方法未清理**：5 个方法标记为 deprecated 但未删除
2. **TODO 注释残留**：7 处 `TODO: 需要数据库模型支持` 注释未处理
3. **默认模型功能不可用**：`DefaultModelService` 调用的方法返回空值
4. **代码冗余**：`get_configurations()` 流程中调用多个返回空字典的方法

### 1.2 目标

1. **完全重写 ProviderManager**：移除所有废弃代码和 TODO 注释
2. **新增 plugin_default_models 表**：支持租户级别的默认模型配置
3. **重构 DefaultModelService**：基于新数据模型实现默认模型管理
4. **清理 ProviderConfiguration**：移除冗余的凭证管理方法

### 1.3 范围

| 包含 | 不包含 |
|------|--------|
| 重写 ProviderManager | 插件安装流程改造 |
| 新增 plugin_default_models 表 | 前端配置页面改造 |
| 重构 DefaultModelService | 插件 manifest 格式变更 |
| 清理 ProviderConfiguration | 新增 REST API（使用现有 inner 接口） |
| 支持自定义模型（openai-api-compatible） | 多租户隔离逻辑变更 |

---

## 2. 数据模型设计

### 2.1 新增表：plugin_default_models

统一管理租户的默认模型配置，支持标准模型和自定义模型。

```sql
CREATE TABLE ai.plugin_default_models (
    -- 主键
    id VARCHAR(36) PRIMARY KEY,
    
    -- 基础字段
    tenant_id VARCHAR(36) NOT NULL,
    model_type VARCHAR(32) NOT NULL,  -- llm, text-embedding, rerank, speech2text, tts
    
    -- 插件关联（标准模型 + 自定义模型都必填）
    plugin_id VARCHAR(128) NOT NULL,  -- 标准插件或 "openai-api-compatible"
    
    -- 标准模型（插件 manifest 中的模型）
    model_name VARCHAR(255),          -- 从插件 manifest 选择，自定义模型时为 null
    
    -- 自定义模型专用字段
    credential_id VARCHAR(36),        -- 关联 plugin_credentials（可指定使用哪个凭证）
    custom_base_url VARCHAR(512),     -- 自定义 API 端点
    custom_model_name VARCHAR(255),   -- 自定义模型名称
    
    -- 审计字段
    is_valid BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE ON UPDATE CURRENT_TIMESTAMP,
    created_by VARCHAR(36),
    updated_by VARCHAR(36),
    
    -- 唯一约束：每个租户 + 模型类型只能有一个默认
    UNIQUE(tenant_id, model_type)
);

-- 索引
CREATE INDEX ix_plugin_default_models_plugin_id ON ai.plugin_default_models(plugin_id);
CREATE INDEX ix_plugin_default_models_credential_id ON ai.plugin_default_models(credential_id);
```

### 2.2 字段使用场景

| 字段 | 标准模型 | 自定义模型（openai-api-compatible） |
|------|---------|-------------------------------------|
| `plugin_id` | 插件 ID（如 `alon/tongyi`） | `openai-api-compatible` |
| `model_name` | 从 manifest 选择的模型名 | `null` |
| `credential_id` | `null`（使用插件默认凭证） | 关联到具体的凭证记录 |
| `custom_base_url` | `null` | 自定义 API 端点 |
| `custom_model_name` | `null` | 自定义模型名称 |

### 2.3 数据模型类

```python
# server/python/src/ai/models/plugin_default_model.py

class PluginDefaultModel(BaseModel, AuditMixin, ActiveRecordMixin, TenantMixin):
    """租户默认模型配置"""
    
    __tablename__ = "plugin_default_models"
    __table_args__ = (
        UniqueConstraint("tenant_id", "model_type", name="uq_plugin_default_models_tenant_type"),
    )
    
    # 模型类型
    model_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="模型类型：llm, text-embedding, rerank 等",
    )
    
    # 插件关联
    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID，标准插件或 openai-api-compatible",
    )
    
    # 标准模型
    model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="标准模型名称，从插件 manifest 选择",
    )
    
    # 自定义模型专用
    credential_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        index=True,
        comment="关联的凭证ID，用于自定义模型",
    )
    custom_base_url: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
        comment="自定义 API 端点",
    )
    custom_model_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="自定义模型名称",
    )
    
    # 是否有效
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="是否有效",
    )
```

---

## 3. ProviderManager 重写设计

### 3.1 删除的方法

| 方法 | 删除原因 |
|------|---------|
| `_get_all_custom_models()` | 已废弃，返回空字典，模型定义来自插件 manifest |
| `get_default_model()` | 已废弃，返回 None，默认模型从 `plugin_default_models` 查询 |
| `update_default_model_record()` | 已废弃，空操作，默认模型通过 `PluginDefaultModelService` 管理 |
| `_get_all_providers()` | 已废弃，返回空字典，供应商定义来自插件 manifest |
| `_get_all_provider_model_settings()` | 已废弃，返回空字典，模型设置来自插件 manifest |

### 3.2 保留/简化的方法

#### 3.2.1 `get_configurations()` 简化

**原流程（冗余）**：
```
1. _get_all_providers() → 空字典
2. ModelProviderFactory.get_providers() → 插件 manifest
3. _get_all_provider_model_settings() → 空字典
4. _get_all_custom_models() → 空字典
5. 循环构造 ProviderConfiguration（处理空数据）
6. _inject_plugin_credentials() → 凭证注入
```

**新流程（简化）**：
```
1. ModelProviderFactory.get_providers() → 插件 manifest
2. 循环构造 ProviderConfiguration（无需处理空数据）
3. _inject_plugin_credentials() → 凭证注入
```

#### 3.2.2 `get_default_provider_model_name()` 重构

**原实现**：
```python
async def get_default_provider_model_name(self, tenant_id, model_type, db_session):
    # 调用废弃方法（返回 None）
    default_model = await self.get_default_model(tenant_id, model_type)
    if default_model:
        return default_model.provider.provider, default_model.model
    
    # 实际生效的逻辑
    return await self._get_first_provider_first_model(tenant_id, model_type, db_session)
```

**新实现**：
```python
async def get_default_provider_model_name(self, tenant_id, model_type, db_session):
    # 从 plugin_default_models 表查询
    default_model = await PluginDefaultModel.one_by_conditions(
        db_session,
        conditions=[
            PluginDefaultModel.tenant_id == tenant_id,
            PluginDefaultModel.model_type == model_type,
            PluginDefaultModel.is_valid == True,
        ],
    )
    
    if default_model:
        # 构造 provider 名称
        if default_model.model_name:
            # 标准模型：plugin_id/model_name
            return default_model.plugin_id, default_model.model_name
        else:
            # 自定义模型：plugin_id/custom_model_name
            return default_model.plugin_id, default_model.custom_model_name
    
    # 没有配置默认模型，返回第一个可用模型
    return await self._get_first_provider_first_model(tenant_id, model_type, db_session)
```

### 3.3 新增的方法

| 方法 | 说明 |
|------|------|
| `_get_default_model_from_db()` | 从 `plugin_default_models` 表查询默认模型 |
| `_build_provider_name()` | 根据 `PluginDefaultModel` 构造完整的 provider 名称 |

---

## 4. ProviderConfiguration 重构设计

### 4.1 删除的方法

| 方法 | 删除原因 |
|------|---------|
| `add_or_update_custom_credentials()` | 凭证通过 `plugin_credentials` API 管理 |
| `delete_custom_credentials()` | 同上 |

### 4.2 简化的方法

#### 4.2.1 `custom_credentials_validate()`

**原实现**：包含数据库记录查询逻辑（TODO 注释）

**新实现**：只保留凭证验证和加密逻辑

```python
async def custom_credentials_validate(self, credentials: dict) -> dict:
    """
    验证供应商凭证
    
    :param credentials: 供应商凭证
    :return: 验证并加密后的凭证
    """
    # 获取凭证表单中的敏感变量
    secret_variables = self._extract_secret_variables(
        self.provider.provider_credential_schema.credential_form_schemas
        if self.provider.provider_credential_schema else []
    )
    
    # 通过供应商工厂验证凭证
    model_provider_factory = ModelProviderFactory(self.tenant_id)
    credentials = await model_provider_factory.provider_credentials_validate(
        provider=self.provider.provider,
        credentials=credentials,
    )
    
    # 加密敏感凭证
    for key, value in credentials.items():
        if key in secret_variables:
            credentials[key] = encrypt_token(self.tenant_id, value)
    
    return credentials
```

#### 4.2.2 `custom_model_credentials_validate()`

同上，简化为只保留验证和加密逻辑。

---

## 5. DefaultModelService 重构设计

### 5.1 新的服务类

```python
# server/python/src/ai/services/plugin_default_model_service.py

class PluginDefaultModelService:
    """租户默认模型服务"""
    
    async def get_default_model(
        self, 
        session: AsyncSession, 
        model_type: ModelType
    ) -> PluginDefaultModel | None:
        """
        获取默认模型
        
        :param session: 数据库会话
        :param model_type: 模型类型
        :return: 默认模型配置
        """
        
    async def set_default_model(
        self,
        session: AsyncSession,
        model_type: ModelType,
        plugin_id: str,
        model_name: str | None = None,        # 标准模型
        credential_id: str | None = None,     # 自定义模型
        custom_base_url: str | None = None,   # 自定义模型
        custom_model_name: str | None = None, # 自定义模型
    ) -> PluginDefaultModel:
        """
        设置默认模型（upsert）
        
        :param session: 数据库会话
        :param model_type: 模型类型
        :param plugin_id: 插件 ID
        :param model_name: 标准模型名称（从 manifest 选择）
        :param credential_id: 凭证 ID（自定义模型）
        :param custom_base_url: 自定义 API 端点
        :param custom_model_name: 自定义模型名称
        :return: 默认模型配置
        """
        
    async def clear_default_model(
        self, 
        session: AsyncSession, 
        model_type: ModelType
    ) -> None:
        """
        清除默认模型（软删除）
        
        :param session: 数据库会话
        :param model_type: 模型类型
        """
```

### 5.2 ManagementService 集成

```python
# server/python/src/ai/components/model/services/management_service.py

class DefaultModelService:
    """默认模型管理器（重构）"""
    
    def __init__(self, tenant_id: str):
        self._tenant_id = tenant_id
        self._service = PluginDefaultModelService()
    
    async def get_default_model(self, model_type: ModelType) -> PluginDefaultModel | None:
        """获取默认模型"""
        async with get_db_session() as session:
            return await self._service.get_default_model(session, model_type)
    
    async def set_default_model(
        self,
        model_type: ModelType,
        plugin_id: str,
        model_name: str | None = None,
        credential_id: str | None = None,
        custom_base_url: str | None = None,
        custom_model_name: str | None = None,
    ) -> PluginDefaultModel:
        """设置默认模型"""
        async with get_db_session() as session:
            result = await self._service.set_default_model(
                session, model_type, plugin_id, model_name,
                credential_id, custom_base_url, custom_model_name
            )
            await session.commit()
            return result
    
    async def clear_default_model(self, model_type: ModelType) -> None:
        """清除默认模型"""
        async with get_db_session() as session:
            await self._service.clear_default_model(session, model_type)
            await session.commit()
```

---

## 6. 数据流设计

### 6.1 标准模型对话流程

```
用户请求: { "model": { "name": "qwen-plus", "provider": "alon/tongyi/openai" } }
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 解析 provider                                                            │
│    ModelProviderID("alon/tongyi/openai")                                    │
│    → plugin_id = "alon/tongyi"                                              │
│    → provider_name = "openai"                                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 获取插件配置                                                              │
│    ProviderManager.get_configurations(tenant_id, db_session=session)        │
│    → 从插件 manifest 获取模型定义                                            │
│    → _inject_plugin_credentials() 注入默认凭证                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 调用插件进程                                                              │
│    ModelInstance.invoke_llm(...)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 默认模型查询流程

```
用户请求: { "model_type": "llm" } （未指定具体模型）
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 查询默认模型配置                                                          │
│    SELECT * FROM ai.plugin_default_models                                   │
│    WHERE tenant_id = ? AND model_type = 'llm' AND is_valid = true          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2a. 有默认配置                                                               │
│     标准模型 → 返回 (plugin_id, model_name)                                  │
│     自定义模型 → 返回 (plugin_id, custom_model_name)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2b. 无默认配置                                                               │
│     _get_first_provider_first_model() → 返回第一个可用模型                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 6.3 自定义模型配置流程

```
用户配置自定义模型（私有部署）
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 创建凭证                                                                  │
│    POST /ai/console/v1/plugins/openai-api-compatible/credentials            │
│    { "name": "私有部署", "credentials": { "api_key": "sk-xxx" } }            │
│    → 返回 credential_id                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 设置默认模型                                                              │
│    DefaultModelService.set_default_model(                                    │
│        model_type = "llm",                                                   │
│        plugin_id = "openai-api-compatible",                                  │
│        credential_id = "cred-123",                                           │
│        custom_base_url = "https://my-api.example.com/v1",                    │
│        custom_model_name = "my-custom-model",                                │
│    )                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. 测试策略

### 7.1 单元测试

| 测试文件 | 测试内容 |
|---------|---------|
| `test_plugin_default_model.py` | 模型 CRUD、唯一约束、字段验证 |
| `test_provider_manager.py` | get_configurations、get_default_provider_model_name |
| `test_plugin_default_model_service.py` | 服务层 CRUD、upsert 逻辑 |
| `test_provider_configuration.py` | 简化后的凭证验证方法 |

### 7.2 集成测试

| 测试文件 | 测试内容 |
|---------|---------|
| `test_plugin_model_flow.py` | 完整流程：插件安装 → 配置凭证 → 设置默认模型 → 对话 |
| `test_custom_model_flow.py` | 自定义模型配置和使用流程 |

### 7.3 测试用例清单

```python
class TestPluginDefaultModel:
    def test_create_standard_model_default(self):
        """创建标准模型默认配置"""
        
    def test_create_custom_model_default(self):
        """创建自定义模型默认配置"""
        
    def test_unique_constraint_tenant_model_type(self):
        """唯一约束：每个租户每种类型只能有一个默认"""
        
    def test_upsert_on_conflict(self):
        """冲突时更新（upsert）"""
        
    def test_soft_delete(self):
        """软删除：is_valid = false"""

class TestProviderManager:
    def test_get_configurations_without_deprecated_calls(self):
        """get_configurations 不调用废弃方法"""
        
    def test_get_default_provider_model_name_from_db(self):
        """从数据库获取默认模型"""
        
    def test_get_default_provider_model_name_fallback(self):
        """无默认配置时返回第一个可用模型"""
        
    def test_no_todo_comments(self):
        """代码中无 TODO 注释"""
```

---

## 8. 迁移策略

### 8.1 数据库迁移

```python
# 003_add_plugin_default_models.py

def upgrade():
    # 创建 plugin_default_models 表
    op.create_table(
        "plugin_default_models",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("model_type", sa.String(32), nullable=False),
        sa.Column("plugin_id", sa.String(128), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=True),
        sa.Column("credential_id", sa.String(36), nullable=True),
        sa.Column("custom_base_url", sa.String(512), nullable=True),
        sa.Column("custom_model_name", sa.String(255), nullable=True),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column("created_by", sa.String(36), nullable=True),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.UniqueConstraint("tenant_id", "model_type", name="uq_plugin_default_models_tenant_type"),
        schema="ai",
    )
    
    # 创建索引
    op.create_index("ix_plugin_default_models_plugin_id", "plugin_default_models", ["plugin_id"], schema="ai")
    op.create_index("ix_plugin_default_models_credential_id", "plugin_default_models", ["credential_id"], schema="ai")

def downgrade():
    op.drop_index("ix_plugin_default_models_credential_id", schema="ai")
    op.drop_index("ix_plugin_default_models_plugin_id", schema="ai")
    op.drop_table("plugin_default_models", schema="ai")
```

### 8.2 现有数据处理

如果有现有数据需要迁移，提供迁移脚本：

```sql
-- 从废弃的 model_tenant_default 表迁移（如果存在）
INSERT INTO ai.plugin_default_models (id, tenant_id, model_type, plugin_id, model_name, is_valid, created_at)
SELECT 
    uuid_generate_v4(),
    tenant_id,
    model_type,
    plugin_id,
    model_name,
    true,
    NOW()
FROM ai.model_tenant_default
WHERE is_valid = true
ON CONFLICT (tenant_id, model_type) DO NOTHING;
```

---

## 9. 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| **新增** | `src/ai/models/plugin_default_model.py` | 默认模型数据模型 |
| **新增** | `src/ai/schemas/plugin_default_model.py` | 默认模型 Schema（DTO） |
| **新增** | `src/ai/services/plugin_default_model_service.py` | 默认模型服务 |
| **重写** | `src/ai/components/model/internal/provider_manager.py` | 移除所有废弃方法和 TODO |
| **重构** | `src/ai/components/model/internal/provider_configuration.py` | 移除凭证管理方法 |
| **重构** | `src/ai/components/model/services/management_service.py` | 重构 DefaultModelService |
| **修改** | `src/ai/models/__init__.py` | 导出新模型 |
| **新增** | `src/ai/migrations/versions/003_add_plugin_default_models.py` | 迁移文件 |
| **新增** | `tests/ai/unit/models/test_plugin_default_model.py` | 模型测试 |
| **重写** | `tests/ai/unit/components/model/test_provider_manager.py` | ProviderManager 测试 |
| **新增** | `tests/ai/unit/services/test_plugin_default_model_service.py` | 服务测试 |
| **更新** | `src/ai/components/model/MIGRATION.md` | 迁移文档 |

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 删除废弃方法影响现有调用 | 编译错误或运行时异常 | CodeGraph 检查所有调用点，确保无外部调用 |
| 数据迁移失败 | 数据丢失 | 提供回滚脚本，迁移前备份 |
| 默认模型查询性能 | 高频调用影响性能 | 添加 Redis 缓存，与 get_configurations 共用缓存策略 |
| 自定义模型凭证泄露 | 安全风险 | 凭证加密存储，日志脱敏 |

---

## 11. 验收标准

| 标准 | 验证方式 |
|------|---------|
| ProviderManager 无废弃方法 | 代码审查 |
| ProviderManager 无 TODO 注释 | `grep -r "TODO" provider_manager.py` 无结果 |
| 默认模型功能可用 | 集成测试通过 |
| 自定义模型功能可用 | 集成测试通过 |
| 所有测试通过 | `pytest tests/ai/ -v` |
| 测试覆盖率 > 80% | `pytest --cov=ai.components.model` |

---

## 12. 参考资料

- [2026-06-30-plugin-model-integration-design.md](./2026-06-30-plugin-model-integration-design.md) - 插件系统与模型配置整合设计
- [2026-06-30-plugin-model-simplification.md](../plans/2026-06-30-plugin-model-simplification.md) - 实现计划
- [MIGRATION.md](../../server/python/src/ai/components/model/MIGRATION.md) - 模型组件迁移日志
