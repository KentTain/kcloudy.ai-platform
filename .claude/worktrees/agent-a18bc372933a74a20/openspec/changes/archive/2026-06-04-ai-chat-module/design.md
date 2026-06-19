## 上下文

### 当前状态

**后端**
- 接口：`POST /chat-messages`，使用自定义 SSE 格式
- 流式处理：`agent.astream_events(version="v2")` 手动处理事件
- 格式：`data: {"event":"message","data":{"content":"..."}}`
- 无前端调用者，可安全改造

**前端**
- 技术栈：Vue 3 + shadcn-vue
- 框架模块系统：`web/vue/src/framework/module/`
- 现有模块：demo、iam、tenant
- 无 AI 对话功能

### 约束

- 复用现有 Agent 层（`AlonChatModel`、`AgentFactory`）
- 复用现有会话持久化（`Conversation`、`Message` 模型）
- 前端必须支持模型选择
- 采用 Vercel AI SDK 标准协议

## 目标 / 非目标

**目标：**

1. 前端快速落地 ChatGPT 风格对话功能
2. 后端输出 AI SDK 标准格式 SSE 流
3. 支持用户选择不同模型/提供商
4. 保持架构扩展性（工具调用、多模态）

**非目标：**

1. 不改造 LangChain Agent 核心逻辑
2. 不新增数据库表结构
3. 阶段一不实现工具调用可视化（阶段二）
4. 不支持多模态图片上传（阶段三）

## 决策

### 1. 前端技术栈组合

**选择**：`ai` + `@ai-sdk/vue` + `ai-elements-vue`（CLI 安装）

**理由**：
- `ai`：核心协议解析，必须依赖
- `@ai-sdk/vue`：Vue 专用 hooks（`useChat`），必须依赖
- `ai-elements-vue`：现成对话组件，基于 shadcn-vue，与项目技术栈匹配

**替代方案**：
- 完全自研组件：开发周期长，不满足"快速落地"目标
- Chat SDK（`npm install chat`）：绑定 Next.js，不适用于 Vue

**组件位置**：`web/vue/src/components/ai-elements/`（全局）
- 理由：遵循 shadcn-vue 惯例，便于跨模块复用

### 2. 后端改造层次

**选择**：阶段一直接修改 `run_llm_task()`，阶段二引入 `UIMessageChunkCallbackHandler`

**理由**：
- 阶段一：改动集中在一处，调试简单，快速验证前后端联调
- 阶段二：职责分离，扩展性更好，支持工具调用等高级特性

**替代方案**：
- 新增适配层（需求文档方案 A）：多一层抽象，阶段一不必要
- 前端适配（Transport 层）：后端保持原格式，违背"后端完全适配"决策

### 3. SSE 格式

**选择**：完全采用 AI SDK `UIMessageChunk` 标准

`
data: {"type":"start","messageId":"msg-xxx"}

data: {"type":"text-start","id":"text-1"}
data: {"type":"text-delta","id":"text-1","delta":"你好"}
data: {"type":"text-delta","id":"text-1","delta":"世界"}
data: {"type":"text-end","id":"text-1"}

data: {"type":"finish","finishReason":"stop","usage":{...}}
data: [DONE]
`

**理由**：
- 与 AI SDK 生态完全兼容
- 前端无需任何适配代码
- 便于未来集成 LangGraph、MCP 等

### 4. 请求格式

**选择**：新增 `AIChatRequest` Schema，接收 AI SDK 标准格式

`json
{
  "id": "conversation-uuid",
  "messages": [{"id":"msg-1","role":"user","parts":[{"type":"text","text":"你好"}]}],
  "trigger": "submit-message",
  "messageId": "msg-2",
  "body": {
    "model": {"provider":"openai","name":"gpt-4","completionParams":{}}
  }
}
`

**理由**：
- 与 `useChat` 发送的格式完全匹配
- `body.model` 支持模型选择功能

### 5. 分阶段实施

**阶段一（MVP）**：最小可行产品
- 前端：基础对话页面
- 后端：修改 SSE 格式，直接处理事件
- 验证：发消息 → 收到流式响应

**阶段二（技术债清理）**：引入 Callback Handler
- 后端：`UIMessageChunkCallbackHandler`
- 前端：工具调用可视化

**阶段三（完整体验）**：高级特性
- 会话管理（列表/切换/历史）
- 模型选择器
- 联网搜索可视化
- 图片上传

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| ai-elements-vue API 不稳定 | 源码复制到项目，锁定版本 |
| 阶段一代码不够优雅 | 阶段二重构，明确技术债 |
| 模型选择需要后端支持动态列表 | 阶段三实现，先用静态配置 |
| AlonChatModel 跳过空 content chunk | Callback Handler 阶段注意处理 |
| AI SDK 版本迭代 | 锁定版本，跟踪更新日志 |

## 开放问题

（无 - 探索阶段已明确所有关键决策）
