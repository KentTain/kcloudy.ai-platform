# 对话接口对比分析：Hermes vs AI Platform（修正版）

> **修订说明**：初版方案存在两处关键误判，本版予以修正：
> 1. **误判 AI SDK 协议**：初版提出自定义 `StreamEvent`（MessageChunk/ToolCallChunk 等）替换流式协议。经核实，本项目前后端已完整采用 AI SDK UIMessage data stream protocol，自定义事件会破坏协议导致前端无法解析。本版改为"对外协议不变，仅增强后端内部能力"。
> 2. **误判工具循环缺失**：初版认为本项目"完全缺失工具循环"。经核实，`AgentFactory.create_executor()` 基于 LangChain `create_agent` 已自带工具循环，`UIMessageChunkCallbackHandler` 已将工具事件转换为 `tool-call`/`tool-result`。真正的问题是 `llm.py` 调用时未传入 `tools`，以及工具/技能的加载机制是静态一次性的，不支持运行时动态管理。

---

## 一、核心结论

| 维度 | 初版判断 | 修正后判断 |
|------|---------|-----------|
| 流式协议 | 需自定义 StreamEvent | **已用 AI SDK UIMessageChunk，不应改动** |
| 工具循环 | 完全缺失 | **已具备（LangChain create_agent），只是没喂工具** |
| 思考过程 | 未实现 | **已实现（thinking-* 事件 + 前端重组）** |
| 工具调用 UI | 需新建 | **已有（ToolCallItem 等组件）** |
| 会话持久化 | 强制 DB | 已有，符合本项目定位 |
| 工具供给 | - | **真正缺失：无工具加载机制** |
| 动态技能管理 | - | **真正缺失：无 skill_manage 类工具** |

**改造重心从"重建对话引擎"收缩为"补齐工具供给 + 动态技能管理"两块。**

---

## 二、本项目已有能力清单（纠正误判）

### 2.1 AI SDK UIMessageChunk 协议（前后端完整）

**后端输出**（`server/python/src/ai/controllers/v1/chat/llm.py` `_sse_generator`）：

```
data: {"type":"start","messageId":"..."}
data: {"type":"text-start","id":"..."}
data: {"type":"text-delta","id":"...","delta":"..."}
data: {"type":"text-end","id":"..."}
data: {"type":"thinking-start","id":"...","stepType":"..."}
data: {"type":"thinking-delta","id":"...","delta":"..."}
data: {"type":"thinking-end","id":"..."}
data: {"type":"tool-call","toolCallId":"...","toolName":"...","args":{...}}
data: {"type":"tool-result","toolCallId":"...","result":"..."}
data: {"type":"finish","finishReason":"stop","usage":{...}}
data: [DONE]
```

**事件类型定义**（`server/python/src/ai/controllers/v1/chat/event_types.py`）：

```python
class EventType(str, Enum):
    START = "start"
    TEXT_START = "text-start"
    TEXT_DELTA = "text-delta"
    TEXT_END = "text-end"
    TOOL_CALL = "tool-call"
    TOOL_RESULT = "tool-result"
    FINISH = "finish"
    ERROR = "error"
    THINKING_START = "thinking-start"
    THINKING_DELTA = "thinking-delta"
    THINKING_END = "thinking-end"
    SOURCE_URL = "source-url"
    SOURCE_DOCUMENT = "source-document"
    FILE_UPLOAD_START = "file-upload-start"
    FILE_UPLOAD_END = "file-upload-end"
    DATA = "data"
    WARNING = "warning"
```

**前端消费**（`web/vue/src/ai/composables/useChat.ts`）：

```typescript
import { Chat } from "@ai-sdk/vue";
import { DefaultChatTransport, type UIMessage as AiUIMessage } from "ai";

const transport = new DefaultChatTransport<AiUIMessage>({
  api: "/api/ai/console/v1/chat-messages",
  body: { model: currentModel },
});
const chat = new Chat({ id, transport, messages, onFinish, onError });
```

### 2.2 工具循环（LangChain Agent 自带）

**Agent 工厂**（`server/python/src/extended/langchain/agents/agent_factory.py`）：

```python
class AgentFactory:
    def create_executor(
        self,
        tools: list | None = None,          # ← 工具在此注入
        checkpointer: BaseCheckpointSaver | None = None,
        prompt: str | SystemMessage | None = None,
    ) -> CompiledStateGraph:
        kwargs: dict[str, Any] = {"model": self.model}
        if tools:
            kwargs["tools"] = tools
        return create_agent(**kwargs)        # ← LangChain create_agent 自带工具循环
```

`create_agent` 内部已实现"模型决策 → 工具调用 → 结果回填 → 再决策"的循环，无需自建。

**事件流转**（`llm.py` `run_llm_task`）：

```python
agent = agent_factory.create_executor()      # ← 当前未传 tools
async for event in agent.astream_events(
    {"input": query}, version="v2",
    callbacks=[callback_handler],
):
    ...
```

### 2.3 工具事件转换（Callback Handler）

**`server/python/src/extended/langchain/callbacks/ui_message_chunk_callback.py`**：

| LangChain 事件 | AI SDK 输出 |
|---------------|------------|
| `on_llm_new_token` | `text-delta` |
| `on_tool_start` | `tool-call`（`toolCallId`=run_id, `toolName`, `args`） |
| `on_tool_end` | `tool-result` |
| `on_tool_error` | `tool-result`（错误） |
| `on_chain_start` | `thinking-start` |
| `on_chain_end` | `thinking-end` |

### 2.4 工具调用 UI（已存在）

- `web/vue/src/ai/components/ToolCallItem.vue` - 工具调用项
- `web/vue/src/components/ai-elements/tool/Tool.vue` - 工具容器
- `web/vue/src/components/ai-elements/tool/ToolInput.vue` - 参数展示
- `web/vue/src/components/ai-elements/tool/ToolOutput.vue` - 结果展示
- `web/vue/src/components/ai-elements/tool/ToolStatusBadge.vue` - 状态徽章（`input-streaming`/`input-available`/`output-available`/`output-error` 等）

### 2.5 其他已有能力

| 能力 | 实现位置 |
|------|---------|
| 会话创建/恢复 | `conversation_service.get_or_create` |
| 消息持久化 | `chat_service.create_messages` / `update_assistant_message` |
| 消息状态机 | `MessageStatus`：PENDING/COMPLETED/STOPPED/ERROR |
| 停止生成 | `POST /{conversation_id}/stop` + `asyncio` 任务取消 |
| 思考过程重组 | `useChat.ts` `processThinkingEvents` |
| 会话命名 | `chat_service.update_conversation_name` |
| 多模态消息部分 | `UIMessagePart` 类型体系（text/thinking/tool-call/tool-result/source-*/file/data） |

---

## 三、真正的差距分析

### 3.1 工具供给机制缺失（核心差距）

**现状**：`llm.py` 中 `agent_factory.create_executor()` **未传入 tools**，导致 agent 无工具可用。

```python
# llm.py 当前代码
agent_factory = AgentFactory(model)
agent = agent_factory.create_executor()   # ← 无 tools 参数
```

**缺失环节**：
- 无工具注册表（Tool Registry）
- 无按租户/应用/插件配置加载工具的机制
- 无工具与 `plugin_installations`（租户已安装插件）的关联
- 工具集在 agent 创建时静态绑定，不支持运行时变更

**Hermes 对应能力**：
- `enabled_toolsets` / `disabled_toolsets` 配置驱动工具集
- 工具按 toolset 分组管理（`get_toolset_for_tool`）
- 工具元数据注册（`model_tools.py`）

### 3.2 动态技能管理缺失（核心差距）

**现状**：本项目无"技能"概念，工具（若有）只能在 agent 创建时静态注入，对话过程中无法增删改。

**Hermes 对应能力**：

| 文件 | 职责 |
|------|------|
| `tools/skill_manager_tool.py` | `skill_manage` 工具，支持 `create/update/delete/patch` 技能 |
| `agent/skill_bundles.py` | 技能打包加载 |
| `agent/skill_preprocessing.py` | 技能预处理 |
| `agent/skill_commands.py` | 技能命令注册 |

`skill_manage` 工具签名（Hermes）：

```python
def skill_manage(
    action: str,            # create / update / delete / patch
    name: str,
    content: str = None,
    category: str = None,
    file_path: str = None,
    file_content: str = None,
    old_string: str = None,
    new_string: str = None,
    replace_all: bool = False,
    absorbed_into: str = None,
) -> str
```

**关键差异**：Hermes 的技能是**模型可自主管理**的运行时资源，本项目的工具是**开发者预置**的静态资源。

### 3.3 次要差距（非阻塞）

| 差距 | Hermes | 本项目 | 优先级 |
|------|--------|--------|--------|
| Steering（对话引导） | `agent.steer()` | 无 | P2 |
| 对话压缩 | `conversation_compression.py` | 无 | P2 |
| 消息分支 | `branchGroupId` | 无 | P3 |
| 多平台适配 | BasePlatformAdapter | 不需要 | - |
| 迭代预算 | `iteration_budget` | 无显式限制 | P2 |

---

## 四、修正后的改造方案

### 4.1 总体原则

```
对外协议：AI SDK UIMessageChunk 不变
改造焦点：后端工具供给 + 动态技能管理
前端改动：最小化（主要复用现有组件）
```

### 4.2 Phase 1：工具供给机制（P0）

**目标**：让 agent 有工具可用，工具按租户配置加载。

#### 4.2.1 工具注册表

**新增**：`server/python/src/ai/tools/registry.py`

```python
class ToolRegistry:
    """工具注册表 - 管理工具的注册、查询、加载"""

    _tools: dict[str, ToolDescriptor] = {}

    @classmethod
    def register(cls, name: str, tool: BaseTool, *, category: str = "builtin"):
        """注册工具"""

    @classmethod
    def get_tools(cls, names: list[str]) -> list[BaseTool]:
        """按名称批量获取工具"""

    @classmethod
    def list_available(cls, tenant_id: str, app_id: str) -> list[ToolDescriptor]:
        """列出租户可用工具（含插件提供的工具）"""
```

#### 4.2.2 工具加载器

**新增**：`server/python/src/ai/tools/loader.py`

```python
class ToolLoader:
    """按租户上下文加载工具集"""

    async def load_for_context(
        self,
        session: AsyncSession,
        tenant_id: str,
        app_id: str,
    ) -> list[BaseTool]:
        """
        加载租户可用工具：
        1. 内置工具（搜索、计算等）
        2. 已安装插件提供的工具（关联 plugin_installations）
        3. 动态技能转换的工具（Phase 2）
        """
```

#### 4.2.3 接入对话流程

**修改**：`server/python/src/ai/controllers/v1/chat/llm.py`

```python
# 加载工具
tool_loader = ToolLoader()
tools = await tool_loader.load_for_context(
    session=session,
    tenant_id=tenant_id,
    app_id=DEFAULT_APP_ID,
)

# 注入 agent
agent = agent_factory.create_executor(tools=tools)   # ← 传入 tools
```

> **注意**：`UIMessageChunkCallbackHandler` 已能处理工具事件，无需改动。前端 `ToolCallItem` 已能渲染，无需改动。

### 4.3 Phase 2：动态技能管理（P1）

**目标**：支持模型在对话中动态创建、更新、删除技能，并将技能动态注入工具集。

#### 4.3.1 技能模型

**新增**：`server/python/src/ai/models/skill.py`

```python
class Skill(BaseModel, ActiveRecordMixin, TenantMixin):
    """技能模型"""
    __tablename__ = "skills"

    app_id: Mapped[str] = mapped_column(StringUUID, index=True)
    name: Mapped[str] = mapped_column(String(100))
    category: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 是否为对话中动态创建
    is_dynamic: Mapped[bool] = mapped_column(Boolean, default=False)
```

#### 4.3.2 技能管理工具

**新增**：`server/python/src/ai/tools/skill_manage_tool.py`

参照 Hermes `skill_manage`，实现 `create/update/delete/patch` 四个 action，作为 LangChain `BaseTool` 注册到 `ToolRegistry`。

```python
class SkillManageTool(BaseTool):
    name = "skill_manage"
    description = "管理技能：创建、更新、删除、修改"

    async def _arun(self, action: str, name: str, **kwargs) -> str:
        if action == "create":
            return await self._create_skill(...)
        elif action == "update":
            return await self._update_skill(...)
        # ...
```

#### 4.3.3 技能动态注入

技能创建后，下次 agent 调用时由 `ToolLoader` 加载为工具。对于需要即时生效的场景，可在技能创建后通过事件通知刷新工具缓存。

#### 4.3.4 技能预处理（可选）

参照 Hermes `skill_preprocessing.py`，对技能内容做模板渲染、命令提取等预处理，转换为可执行工具。

### 4.4 Phase 3：高级特性（P2/P3，可选）

| 特性 | 实现思路 | 优先级 |
|------|---------|--------|
| 迭代预算 | 包装 `create_agent` 限制最大工具调用轮次 | P2 |
| 对话压缩 | 长对话时调用摘要模型压缩历史 | P2 |
| Steering | 通过前端注入 + `tool-result` 追加引导文本 | P2 |
| 消息分支 | 扩展 `Message` 模型增加 `branch_group_id` | P3 |

---

## 五、工作量估算（修正后）

### 5.1 后端

| 任务 | 文件数 | 预估工时 | 优先级 |
|------|-------|---------|--------|
| 工具注册表 | 1 | 6h | P0 |
| 工具加载器 | 1 | 10h | P0 |
| llm.py 接入工具 | 1 | 4h | P0 |
| 内置工具实现（搜索等） | 2 | 12h | P0 |
| 技能模型 + 迁移 | 2 | 6h | P1 |
| skill_manage 工具 | 1 | 12h | P1 |
| 技能动态注入 | 1 | 8h | P1 |
| 迭代预算 | 1 | 4h | P2 |
| 对话压缩 | 2 | 12h | P2 |
| **小计** | **12** | **74h** | |

### 5.2 前端

| 任务 | 文件数 | 预估工时 | 优先级 |
|------|-------|---------|--------|
| 工具调用 UI 适配（复用现有） | 1 | 4h | P0 |
| 技能管理界面（可选） | 2 | 12h | P1 |
| **小计** | **3** | **16h** | |

### 5.3 测试与文档

| 任务 | 预估工时 |
|------|---------|
| 单元测试 | 16h |
| 集成测试 | 12h |
| 文档更新 | 4h |
| **小计** | **32h** |

### 5.4 总计

| 阶段 | 工时 | 周期 |
|------|------|------|
| Phase 1 (P0) 工具供给 | 48h | 1.5 周 |
| Phase 2 (P1) 动态技能 | 50h | 1.5 周 |
| Phase 3 (P2) 高级特性 | 24h | 1 周 |
| **总计** | **122h** | **4 周** |

> 对比初版估算的 196h，修正后缩减约 38%，主要源于删除了不必要的协议重建和已有能力重写。

---

## 六、风险与注意事项

### 6.1 协议兼容性红线

**任何改造不得破坏 AI SDK UIMessageChunk 协议**。具体约束：

- 后端必须继续输出 `EventType` 枚举定义的标准事件
- 不得引入 `MessageChunk`/`ToolCallChunk` 等自定义事件类型
- 工具调用必须通过 `tool-call` / `tool-result` 事件传递
- `UIMessageChunkCallbackHandler` 的事件映射逻辑保持稳定

### 6.2 工具加载性能

- 工具加载应缓存（按 tenant_id + app_id），避免每次请求查库
- 插件工具加载涉及 `plugin_installations`，需注意租户隔离
- 动态技能转工具的预处理结果应缓存

### 6.3 技能安全

- `skill_manage` 工具需权限控制（避免模型随意删除关键技能）
- 动态创建的技能内容需校验（防止注入）
- 参照 Hermes 的 `_validate_name` / `_validate_category` / `_validate_frontmatter` 校验逻辑

### 6.4 LangChain 版本兼容

- `create_agent` / `astream_events(version="v2")` 依赖 LangChain 版本
- 工具循环行为受 LangChain 版本影响，升级需回归测试

---

## 七、实施建议

### 7.1 分阶段交付

```
Week 1: Phase 1 工具供给
├── 工具注册表 + 加载器
├── 内置工具实现
├── llm.py 接入
└── 端到端验证（模型能调用工具）

Week 2-3: Phase 2 动态技能
├── 技能模型 + 迁移
├── skill_manage 工具
├── 技能动态注入
└── 端到端验证（模型能管理技能）

Week 4: Phase 3 高级特性（按需）
├── 迭代预算
├── 对话压缩
└── Steering
```

### 7.2 验收标准

| 阶段 | 验收项 |
|------|--------|
| Phase 1 | 模型能调用内置工具，前端 `ToolCallItem` 正确渲染工具调用与结果 |
| Phase 2 | 模型能通过 `skill_manage` 创建技能，新技能在后续对话中可作为工具调用 |
| Phase 3 | 迭代预算生效；长对话能自动压缩；Steering 能影响模型决策 |

### 7.3 质量保证

- 工具加载与技能管理需单元测试覆盖
- 端到端测试验证 AI SDK 协议未被破坏
- 工具调用链路需集成测试（模型决策 → 工具执行 → 结果回填 → 再决策）

---

## 八、总结

本项目对话接口的实际情况远比初版判断的成熟：

1. **协议层**：AI SDK UIMessageChunk 前后端完整，无需改动
2. **引擎层**：LangChain `create_agent` 已提供工具循环，无需自建
3. **展示层**：工具调用 UI、思考过程、流式渲染均已具备

真正需要补齐的是**工具供给**和**动态技能管理**两块后端能力：

- **Phase 1**（1.5 周）：让 agent 有工具可用，打通"租户配置 → 工具加载 → agent 注入"链路
- **Phase 2**（1.5 周）：引入 `skill_manage` 类工具，支持模型在对话中动态管理技能
- **Phase 3**（1 周，可选）：迭代预算、对话压缩等高级特性

改造完成后，本项目将具备与 Hermes 相当的工具调用与技能管理能力，同时保持 AI SDK 协议的兼容性，前端几乎无需改动。
