# Model 组件迁移提案

## 为什么

项目已完成 Plugin SDK 和 Plugin 组件迁移，但缺少统一模型调用门面层。LLM 对话接口需要通过 `LLMService` 统一调用各种模型 Provider，实现模型凭证管理、缓存策略、流式响应等核心能力。

此变更是迁移 `/portal/v1/chat-messages` 接口的关键前置依赖。

## 变更内容

从 Alon 平台迁移 Model 组件，提供统一的 LLM 调用抽象：

- 新增 `LLMService`：统一模型调用门面，支持 invoke/stream 两种模式
- 新增 `ModelInstanceFactory`：根据 Provider 配置创建模型实例
- 新增 `ModelProviderFactory`：解析 Provider ID，获取 Provider 配置
- 新增模型凭证管理：从数据库读取并缓存模型 API 凭证
- 新增基础模型类型定义：`LargeLanguageModel` 基类实现

**不包含**：Embedding 服务、Rerank 服务（本接口未使用，后续按需迁移）。

## 功能 (Capabilities)

### 新增功能

- `llm-service`: LLM 统一调用服务，提供 invoke/stream 方法，支持流式响应、凭证缓存、多 Provider 切换
- `model-provider`: 模型 Provider 管理，包括 Provider 工厂、配置解析、凭证存储
- `model-instance`: 模型实例管理，封装与 Plugin 组件的通信细节

### 修改功能

无（全新功能模块）。

## 影响

### 代码结构

```
ai/components/model/
├── services/
│   ├── llm_service.py           # LLMService 核心
│   └── management_service.py    # 模型清单管理
├── internal/
│   ├── model_instance_factory.py
│   ├── model_provider_factory.py
│   ├── provider_configuration.py
│   └── provider_manager.py
├── model_providers/
│   └── __base__/
│       └── large_language_model.py
├── entities/                    # 模型配置实体
├── errors/                      # 模型调用异常
├── schema/                      # 模型 Schema 定义
└── callbacks/                   # 回调机制
```

### 依赖组件

| 组件 | 用途 | 状态 |
|------|------|------|
| `ai_plugin/sdk/` | PromptMessage、LLMResult 实体 | ✅ 已迁移 |
| `ai/components/plugin/client/` | ModelClient.invoke_llm | ✅ 已迁移 |
| `framework/cache/` | 凭证缓存 | ✅ 可用 |
| `framework/database/` | 凭证存储 | ✅ 可用 |

### API 端点

此变更不直接暴露 API 端点，为后续 `/chat-messages` 接口提供底层能力。

### 兼容性

- 无破坏性变更
- 新增模块，不影响现有功能
