# 插件系统与模型配置整合设计规格

## 1. 概述

### 1.1 背景

AI 模块的模型管理功能从 Alon 项目迁移时，保留了 `model_providers` 和 `model_configs` 两张表的设计。但实际实现中：

1. **模型定义完全来自插件 manifest**：插件的 `models_configuration` 已包含完整的模型提供者定义、支持的模型类型、凭证架构等信息
2. **数据库表从未使用**：`provider_manager.py` 中有大量 `# TODO: 需要数据库模型支持` 注释，所有相关方法都返回空数据
3. **凭证存储分散**：用户配置的 API Key 存储在 `plugin_credentials` 表，但对话接口没有直接关联

### 1.2 问题

| 问题 | 影响 |
|------|------|
| 冗余的数据库表 | `model_providers`、`model_configs` 占用空间但从未使用 |
| 数据流断裂 | 用户配置了凭证，但对话接口不知道如何使用 |
| TODO 遗留 | 迁移时遗留大量 TODO 注释，代码不完整 |
| 用户体验差 | 用户不知道在哪里配置 API Key，配置后也不知道如何使用 |

### 1.3 目标

1. **删除未使用的表**：清理 `model_providers` 和 `model_configs`
2. **打通数据流**：对话接口通过 `plugin_id` 关联到 `plugin_credentials`
3. **简化配置流程**：用户安装插件 → 配置 API Key → 直接使用

### 1.4 范围

| 包含 | 不包含 |
|------|--------|
| 删除未使用的模型表 | 插件安装流程改造 |
| 添加 `is_default` 字段 | 前端配置页面改造 |
| 改造凭证获取逻辑 | 插件 manifest 格式变更 |
| 清理 TODO 注释 | 新增 API 接口 |

---

## 2. 当前架构分析

### 2.1 现有数据模型

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          当前表结构（简化前）                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  tenant schema                                                              │
│  ┌───────────────────────┐     ┌───────────────────────┐                   │
│  │ plugin_definitions    │     │ plugin_installations  │                   │
│  │ (插件定义)             │     │ (安装记录)             │                   │
│  │ - declaration (JSONB) │     │ - tenant_id           │                   │
│  │   包含 models_config  │     │ - plugin_id           │                   │
│  └───────────────────────┘     └───────────────────────┘                   │
│                                                                             │
│  ai schema                                                                  │
│  ┌───────────────────────┐     ┌───────────────────────┐                   │
│  │ model_providers       │     │ model_configs         │ ❌ 未使用         │
│  │ (模型提供商)           │ ❌  │ (模型配置)             │                   │
│  │ - 从未使用            │     │ - 从未使用            │                   │
│  └───────────────────────┘     └───────────────────────┘                   │
│                                                                             │
│  ┌───────────────────────┐     ┌───────────────────────┐                   │
│  │ plugin_credentials    │     │ plugin_configs        │                   │
│  │ (凭证存储)             │ ✅  │ (插件配置)             │ ⚠️ 职责不清      │
│  │ - credentials (加密)  │     │ - plugin_config       │                   │
│  └───────────────────────┘     └───────────────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 插件 manifest 中的模型定义

```yaml
# 插件 manifest.yaml 示例
plugins:
  models:
    - models/openai.yaml  # 指向模型配置文件

# models/openai.yaml 示例
identity:
  name: openai
  label: OpenAI
supported_model_types:
  - llm
  - text-embedding
provider_credential_schema:
  credential_form_schemas:
    - variable: api_key
      type: secret-input
      label:
        en_US: API Key
      required: true
models:
  - name: gpt-4
    model_type: llm
    label:
      en_US: GPT-4
  - name: gpt-3.5-turbo
    model_type: llm
```

### 2.3 对话接口当前流程

```python
# server/python/src/ai/controllers/v1/chat/llm.py

@router.post("")
async def chat_messages(chat_request: AIChatRequest):
    # 创建 AlonChatModel
    model = AlonChatModel(
        model=chat_request.body.model.name,
        provider=chat_request.body.model.provider,  # "alon/tongyi/openai"
        tenant_id=tenant_id,
    )
    
    # 调用 LLM
    async for chunk in llm_service.stream(
        prompt_messages=...,
        model=model,
        provider=provider,
    ):
        yield chunk
```

**问题**：`llm_service.stream()` 内部如何获取凭证？目前流程断裂。

---

## 3. 目标架构设计

### 3.1 简化后的表结构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          目标表结构（简化后）                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  tenant schema (不变)                                                        │
│  ┌───────────────────────┐     ┌───────────────────────┐                   │
│  │ plugin_definitions    │     │ plugin_installations  │                   │
│  │ (插件定义+模型声明)    │     │ (租户安装记录)         │                   │
│  └───────────────────────┘     └───────────────────────┘                   │
│                                                                             │
│  ai schema (简化)                                                            │
│  ┌───────────────────────┐     ┌───────────────────────┐                   │
│  │ plugin_credentials    │     │ plugin_runtime_states │                   │
│  │ (凭证存储)             │ ✅  │ (运行状态)             │ ✅                │
│  │ + is_default 字段     │     └───────────────────────┘                   │
│  └───────────────────────┘                                                 │
│                                                                             │
│  ────────────────────────────────────────────────────────────────────────  │
│  ❌ 删除: model_providers, model_configs                                    │
│  ⚠️ 评估: plugin_configs (可能合并到 credentials)                           │
│  ────────────────────────────────────────────────────────────────────────  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据流设计

```
用户请求: { "model": { "name": "qwen-turbo", "provider": "alon/tongyi/openai" } }
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
│ 2. 查询插件安装状态                                                          │
│    SELECT * FROM tenant.plugin_installations                                │
│    WHERE tenant_id = ? AND plugin_id = 'alon/tongyi'                        │
│    → 确认插件已安装且状态为 ACTIVE                                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 获取默认凭证                                                              │
│    SELECT * FROM ai.plugin_credentials                                      │
│    WHERE tenant_id = ? AND plugin_id = 'alon/tongyi' AND is_default = true  │
│    → 解密 credentials 获取 api_key                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 调用插件进程                                                              │
│    ModelClient.invoke_llm(                                                  │
│        plugin_id = "alon/tongyi",                                           │
│        provider = "openai",                                                 │
│        model = "qwen-turbo",                                                │
│        credentials = { "api_key": "sk-xxx" }                                │
│    )                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 核心变更

| 变更 | 说明 |
|------|------|
| 删除 `model_providers` 表 | 模型提供商定义来自插件 manifest |
| 删除 `model_configs` 表 | 模型列表来自插件 manifest |
| 添加 `is_default` 字段 | 标记插件的默认凭证 |
| 改造 `ProviderManager` | 从 `plugin_credentials` 获取凭证 |

---

## 4. 数据模型变更

### 4.1 PluginCredential 新增字段

```python
# server/python/src/ai/models/plugin.py

class PluginCredential(BaseModel, ...):
    """插件凭证"""
    
    # 现有字段
    plugin_id: Mapped[str]
    plugin_type: Mapped[str]
    scope: Mapped[str]  # global/personal
    name: Mapped[str]
    credentials: Mapped[dict]  # 加密存储
    is_disabled: Mapped[bool]
    
    # 新增字段
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="是否为默认凭证",
    )
```

### 4.2 删除的模型

```python
# 删除文件
# server/python/src/ai/models/model_provider.py
# server/python/src/ai/models/model_config.py

# 删除类
# - ModelProvider
# - ProviderType (枚举)
# - ModelConfig
# - ModelType (枚举) - 注意：可能有其他地方使用，需检查
```

---

## 5. API 设计

### 5.1 凭证管理 API（已存在，需更新）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/ai/console/v1/plugins/{plugin_id}/credentials` | 创建凭证 |
| GET | `/ai/console/v1/plugins/{plugin_id}/credentials` | 凭证列表 |
| PUT | `/ai/console/v1/plugins/{plugin_id}/credentials/{id}` | 更新凭证 |
| DELETE | `/ai/console/v1/plugins/{plugin_id}/credentials/{id}` | 删除凭证 |
| POST | `/ai/console/v1/plugins/{plugin_id}/credentials/{id}/set-default` | **新增**：设为默认 |

### 5.2 凭证创建时自动设置默认

```python
async def create_credential(self, session, plugin_id, obj_in):
    """创建凭证"""
    # 检查是否为第一个凭证
    existing_count = await PluginCredential.count_by_conditions(
        session,
        conditions=[
            PluginCredential.tenant_id == tenant_id,
            PluginCredential.plugin_id == plugin_id,
        ]
    )
    
    # 第一个凭证自动设为默认
    is_default = existing_count == 0
    
    credential = PluginCredential(
        plugin_id=plugin_id,
        name=obj_in.name,
        credentials=encrypted,
        is_default=is_default,  # 自动设置
    )
```

---

## 6. 迁移策略

### 6.1 数据库迁移

```sql
-- 添加 is_default 字段
ALTER TABLE ai.plugin_credentials 
ADD COLUMN is_default BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX ix_plugin_credentials_is_default 
ON ai.plugin_credentials(is_default);

-- 删除未使用的表
DROP TABLE ai.model_configs;
DROP TABLE ai.model_providers;
```

### 6.2 现有数据处理

如果 `plugin_credentials` 已有数据，需要为每个插件的第一个凭证设置 `is_default = true`：

```sql
-- 设置每个插件的第一个凭证为默认
UPDATE ai.plugin_credentials pc
SET is_default = true
WHERE id = (
    SELECT id FROM ai.plugin_credentials
    WHERE tenant_id = pc.tenant_id
    AND plugin_id = pc.plugin_id
    ORDER BY created_at
    LIMIT 1
);
```

---

## 7. 测试策略

### 7.1 单元测试

| 测试文件 | 测试内容 |
|---------|---------|
| `test_plugin_credential.py` | is_default 字段行为 |
| `test_provider_manager.py` | 凭证获取逻辑 |
| `test_credential_service.py` | 凭证加密解密 |

### 7.2 集成测试

| 测试文件 | 测试内容 |
|---------|---------|
| `test_plugin_model_flow.py` | 完整流程：安装→配置→对话 |

### 7.3 测试用例

```python
class TestPluginCredentialDefault:
    def test_first_credential_auto_default(self):
        """第一个凭证自动设为默认"""
        
    def test_set_default_clears_others(self):
        """设置默认时清除其他凭证的默认标记"""
        
    def test_get_default_credential(self):
        """获取插件的默认凭证"""
        
    def test_no_credential_raises_error(self):
        """未配置凭证时抛出错误"""
```

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 现有数据需要迁移 | 已有凭证需要设置默认值 | 迁移脚本自动处理 |
| ModelType 枚举被其他地方使用 | 删除后导入失败 | 检查并迁移到 ai_plugin.sdk |
| 对话接口调用链改动 | 可能影响现有功能 | 增量改造，保持向后兼容 |

---

## 9. 验收标准

| 标准 | 验证方式 |
|------|---------|
| 用户安装插件后能配置 API Key | 手动测试 |
| 配置 API Key 后能直接对话 | 集成测试 |
| 删除 model_providers 和 model_configs 表 | 数据库验证 |
| 所有 TODO 注释已清理 | 代码审查 |
| 测试覆盖率 > 80% | pytest --cov |

---

## 10. 参考资料

- [MIGRATION.md](../../server/python/src/ai/components/model/MIGRATION.md) - 模型组件迁移日志
- [plugin_protocols.py](../../server/python/src/framework/tenant/plugin_protocols.py) - 插件安装协议
- [provider_manager.py](../../server/python/src/ai/components/model/internal/provider_manager.py) - 当前实现（含 TODO）
