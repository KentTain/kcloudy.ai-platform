# Alon 项目源文件映射

本文档记录 `migrate-chat-messages-api` 变更对应的 Alon 项目源文件路径，供实现时参考。

## 源项目路径

```
ALON_ROOT=D:\Project\ai\Alon\packages\platform
```

## 文件映射表

### 1. 控制器迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/controllers/v1/chat/llm.py` | `{ALON_ROOT}/src/alon/controllers/portal/v1/generate/llm.py` |

### 2. Schema 迁移

| 目标路径 | Alon 源路径 |
|----------|-------------|
| `src/ai/schemas/completion.py` | `{ALON_ROOT}/src/alon/schemas/completion.py` |

### 3. 响应模型参考

| 目标路径 | Alon 源路径 |
|----------|-------------|
| 参考响应格式 | `{ALON_ROOT}/src/alon/schemas/portal/app.py` |

## 导入路径替换规则

迁移时需要批量替换导入路径：

| Alon 导入路径 | 目标导入路径 |
|---------------|--------------|
| `from alon.controllers.` | `from ai.controllers.` |
| `from alon.schemas.completion` | `from ai.schemas.completion` |
| `from alon.components.model.services.llm_service` | `from ai.components.model.services.llm_service` |
| `from alon.models.conversation` | `from ai.models.conversation` |
| `from alon.configs.settings` | `from framework.configs.settings` |
| `from alon.common.ctx` | `from framework.common.ctx` |

## 关键依赖适配

### LangChain 集成

```python
# Alon 使用 Agno
from extended.agno.models.alon import Alon
from extended.agno.agent import Agent

# 改为使用 LangChain
from ai.extended.langchain.models.alon_chat import AlonChatModel
from ai.extended.langchain.agents.agent_factory import AgentFactory
```

### 流式响应

```python
# Alon 使用
from fastapi.responses import StreamingResponse

# 保持一致，但使用自定义 SSE 生成器
async def sse_generator():
    async for event in agent.astream_events(...):
        yield f"data: {json.dumps(event)}\n\n"

return StreamingResponse(
    sse_generator(),
    media_type="text/event-stream",
)
```

### 会话管理

```python
# Alon 使用
from alon.models.conversation import Conversation, Message

# 改为使用新路径
from ai.models.conversation import Conversation
from ai.models.message import Message
```

### 任务管控

```python
# Alon 使用
from alon.listeners.services.pubsub.memory_task import stop_task_by_id

# 改为使用新路径
from ai.services.memory_task.helpers import stop_task_by_id
```

## 核心实现参考

### 控制器结构

```python
from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse

from ai.schemas.completion import LLMChatCompletion
from ai.extended.langchain.models.alon_chat import AlonChatModel
from ai.extended.langchain.agents.agent_factory import AgentFactory
from ai.models.conversation import Conversation
from ai.models.message import Message
from ai.services.memory_task.helpers import stop_task_by_id

router = APIRouter(prefix="/chat-messages", tags=["LLM对话"])

APP_ID: str = "00000000-0000-0000-0000-000000000001"
APP_NAME = "通用智能体"

@router.post("")
async def chat_messages(
    chat_completion: LLMChatCompletion = Body(...),
    tenant_id: str = Depends(DependTenant),
    user_id: str = Depends(DependAuth),
) -> StreamingResponse:
    """LLM 对话接口"""
    # 1. 创建/恢复会话
    # 2. 创建模型和 Agent
    # 3. 执行对话并流式返回
    ...

@router.post("/{conversation_id}/stop")
async def stop_chat_messages(
    conversation_id: str,
    tenant_id: str = Depends(DependTenant),
) -> dict:
    """停止对话"""
    # 1. 验证会话
    # 2. 停止任务
    # 3. 更新状态
    ...
```

### SSE 生成器示例

```python
import json
from typing import AsyncIterator

async def sse_generator(
    agent,
    query: str,
    conversation_id: str,
    task_id: str,
) -> AsyncIterator[str]:
    """SSE 事件生成器"""
    full_content = ""
    prompt_tokens = 0
    completion_tokens = 0

    try:
        async for event in agent.astream_events(
            {"input": query},
            version="v2",
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                content = chunk.content
                full_content += content
                yield f"data: {json.dumps({'event': 'message', 'data': {'content': content}})}\n\n"

            elif event["event"] == "on_tool_start":
                tool_name = event["data"].get("name")
                if tool_name and "search" in tool_name.lower():
                    # 提取搜索关键词
                    yield f"data: {json.dumps({'event': 'search_keywords', 'data': {'keywords': []}})}\n\n"

            elif event["event"] == "on_chain_end":
                # 完成
                yield f"data: {json.dumps({'event': 'finish', 'data': {'prompt_tokens': prompt_tokens, 'completion_tokens': completion_tokens}})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'event': 'error', 'data': {'code': 'MODEL_ERROR', 'message': str(e)}})}\n\n"
```

## 迁移优先级

### 第一优先级（核心功能，必须迁移）

1. `schemas/completion.py` - 请求/响应 Schema
2. `controllers/v1/chat/llm.py` - 控制器核心逻辑

### 第二优先级（路由注册）

1. `ai/module.py` - 路由注册更新

### 第三优先级（配置和文档）

1. `framework/configs/settings.py` - 应用配置
2. 模块文档更新

## 文件数量统计

| 类别 | 文件数 |
|------|--------|
| 必须迁移/新建 | 2 |
| 路由注册 | 1 |
| 配置更新 | 1 |
| 测试文件 | 8 |
| 文档 | 1 |
| **总计** | **13** |

## 注意事项

1. **认证依赖**：使用 `framework/common/ctx.py` 提供的 `get_tenant_id()` 和 `get_user_id()`
2. **SSE 格式**：保持与 Alon 平台兼容，便于前端复用
3. **错误处理**：所有异常必须转换为 SSE error 事件，不能抛出 HTTP 错误
4. **资源清理**：使用 `try/finally` 确保流式响应正确关闭
