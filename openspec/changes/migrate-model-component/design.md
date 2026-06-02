# Model 组件技术设计

## 上下文

### 背景

项目已完成 Plugin SDK 和 Plugin 组件迁移，具备与模型插件通信的能力。但上层缺少统一模型调用门面，控制器需要直接操作 Plugin 客户端，无法实现：
- 凭证缓存和复用
- 多 Provider 统一抽象
- 流式响应的标准化处理

### 当前状态

```
已有组件：
├── ai_plugin/sdk/              # 实体定义（PromptMessage, LLMResult）
├── ai/components/plugin/       # 插件通信
│   ├── client/model_client.py  # ModelClient.invoke_llm()
│   └── engine/                 # 插件进程管理
├── framework/cache/            # Redis 缓存
└── framework/database/         # PostgreSQL 存储

缺失组件：
└── ai/components/model/        # 统一模型门面 ← 本次迁移
```

### 约束

1. 必须复用 `framework/cache/` 做凭证缓存
2. 必须复用 `ai_plugin/sdk/entities/` 实体类型
3. 必须对接 `ai/components/plugin/client/model_client.py`
4. 遵循三层架构：Service → Internal → Model Providers

## 目标 / 非目标

**目标：**

1. 提供 `LLMService` 统一调用门面，支持 invoke/stream 模式
2. 实现模型凭证的数据库存储 + Redis 缓存双层架构
3. 封装 Provider ID 解析逻辑，支持 `<plugin_id>/<provider_type>` 格式
4. 实现流式响应的标准处理（LLMResultChunk → AsyncIterator）

**非目标：**

1. Embedding 服务和 Rerank 服务（本接口未使用）
2. 模型插件的安装/卸载管理（已在 Plugin 组件中）
3. 模型计费和配额管理（超出本次范围）

## 决策

### 决策 1：凭证缓存架构

**选择**：双层缓存（Redis + 内存）

**理由**：
- 模型凭证调用频繁，每次对话都需要查询
- Redis 缓存支持跨进程共享，适合多 Worker 场景
- 内存缓存作为二级缓存，减少 Redis 网络开销

**替代方案**：
- 仅内存缓存：多 Worker 无法共享，导致重复查询
- 仅 Redis 缓存：每次调用都需要网络请求，延迟增加

```
请求流程：
LLMService → 内存缓存 → Redis 缓存 → 数据库
              ↑ 命中返回    ↑ 命中返回   ↑ 查询并回填
```

### 决策 2：Provider ID 格式

**选择**：`<plugin_id>/<provider_type>` 格式

**理由**：
- 与 Alon 平台保持一致，降低迁移成本
- 支持同一插件提供多种 Provider 类型（如 openai、azure-openai）
- 解析逻辑简单，字符串分割即可

**示例**：
- `plugin-001/openai` → 插件 ID: `plugin-001`, Provider 类型: `openai`
- `plugin-002/anthropic` → 插件 ID: `plugin-002`, Provider 类型: `anthropic`

### 决策 3：流式响应处理

**选择**：直接透传 `LLMResultChunk` 流

**理由**：
- `ModelClient.invoke_llm()` 已返回 `AsyncIterator[LLMResultChunk]`
- 上层 LangChain 桥接负责转换为 `ChatGenerationChunk`
- 保持各层职责清晰，避免重复转换

**数据流**：
```
Plugin 子进程
    ↓ stdout JSON
ModelClient.invoke_llm()
    ↓ AsyncIterator[LLMResultChunk]
LLMService.stream()
    ↓ AsyncIterator[LLMResultChunk]
AlonChatModel._astream()
    ↓ AsyncIterator[ChatGenerationChunk]
```

### 决策 4：模块归属

**选择**：放置于 `ai/components/model/`

**理由**：
- 与 `ai/components/plugin/` 平级，符合组件化架构
- `ai/` 作为 AI 能力模块的顶级目录
- 后续可扩展 `ai/components/embedding/` 等

## 风险 / 权衡

### 风险 1：凭证缓存一致性

**风险**：数据库凭证更新后，缓存未及时失效

**缓解措施**：
- 设置合理的 TTL（建议 5 分钟）
- 凭证更新接口主动清除缓存
- 调用失败时清除缓存并重试

### 风险 2：插件进程不可用

**风险**：模型插件进程崩溃或未启动

**缓解措施**：
- `LLMService` 捕获 `PluginError` 并转换为 `ModelInvocationError`
- 上层可捕获异常并提示用户检查插件状态
- 后续可增加健康检查和自动重启机制

### 风险 3：流式响应中断

**风险**：网络中断导致流式响应不完整

**缓解措施**：
- 确保 `finally` 块发送结束信号
- 记录完整的 usage 统计用于计费
- 支持客户端通过 message_id 重试

## 迁移计划

### 阶段 1：基础设施（约 2-3 小时）

1. 创建目录结构 `ai/components/model/`
2. 迁移 `entities/` 模型配置实体
3. 迁移 `errors/` 异常定义
4. 迁移 `schema/` Schema 定义

### 阶段 2：Provider 管理（约 3-4 小时）

1. 迁移 `internal/provider_configuration.py`
2. 迁移 `internal/provider_manager.py`
3. 迁移 `internal/model_provider_factory.py`
4. 适配 `framework/cache/` 缓存组件

### 阶段 3：模型实例（约 2-3 小时）

1. 迁移 `internal/model_instance_factory.py`
2. 迁移 `model_providers/__base__/large_language_model.py`
3. 对接 `ai/components/plugin/client/model_client.py`

### 阶段 4：LLM 服务（约 2-3 小时）

1. 迁移 `services/llm_service.py`
2. 迁移 `services/management_service.py`
3. 编写单元测试验证流式调用

### 回滚策略

- 新增模块，不修改现有代码，可直接删除回滚
- 数据库迁移使用 Alembic，支持 `downgrade`
