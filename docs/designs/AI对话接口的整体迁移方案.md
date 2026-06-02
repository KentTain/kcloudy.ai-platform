# LLM 对话接口迁移指南

## 一、迁移目标

将 Alon 平台的 /portal/v1/chat-messages 接口完整迁移至目标项目，实现与大模型的流式对话能力。

## 源项目路径

```
ALON_ROOT=D:\Project\ai\Alon\packages\platform\src
```

## 项目结构

```
{ALON_ROOT}
├── alon/                        # 主后端平台
│   ├── components/              # 核心可插拔组件（详见下方组件架构）
│   ├── controllers/             # API 控制器（admin, console, portal, service_api, inner_api）
│   ├── models/                  # SQLAlchemy 数据库模型
│   ├── schemas/                 # Pydantic 校验模型
│   ├── services/                # 业务逻辑层
│   ├── configs/                 # 配置管理（基于 YAML）
│   ├── middleware/              # 请求/响应中间件
│   ├── common/                  # 通用模块（异常、缓存、上下文、依赖注入等）
│   ├── core/                    # 核心公共模块（路径常量等）
│   ├── listeners/               # MQ消费者（异步任务处理）
│   ├── tasks/                   # APScheduler 定时任务
│   ├── runners/                 # 运行器（开机启动项）
│   ├── toolkits/                # 工具集
│   ├── migrations/              # Alembic 数据库迁移文件
│   └── utils/                   # 工具函数
├── extended/                    # 第三方库的 monkey-patch/扩展
│   ├── advanced_alchemy/       # 数据库配置解耦（Web/Task/Listener 三适配器）
│   ├── agno/                   # Agno 框架扩展（Alon 模型桥接、分块策略、向量库适配）
│   ├── apscheduler/            # 自定义 RedisJobStore（复用平台 Redis 连接管理）
│   ├── fastapi/                # ORJSONResponse 增强、Redis 滑动窗口限流、容错 HTTPBearer
│   ├── langchain_community/    # 自定义文档加载器（PDF/DOCX/PPTX/XLSX/CSV/MD）及 ChatAlon 桥接
│   ├── langgraph/              # 自定义 AsyncPostgresSaver（基于 asyncpg，可配置表前缀）
│   └── python_docx/            # 修复 docx 空目标关系解析崩溃
├── extensions/                  # 扩展应用加载机制
├── alon_plugin/                 # 插件系统 SDK（CLI、SDK、服务端）

```

**接口路径**：POST /portal/v1/apps/llm/chat-messages

**核心能力**：

- 流式对话输出（SSE）
- 会话管理（创建/恢复）
- 记忆管理（跨会话持久化）
- 会话摘要生成
- 联网搜索（可选）
- 任务停止/超时清理

---

## 二、依赖关系总览

### 2.1 迁移顺序（严格按依赖闭包自底向上）

```
步骤 4: 通用基础设施（common/configs/middleware）
    ↓
步骤 9: Plugin SDK（alon_plugin/sdk）
    ↓
步骤 8: Plugin 组件（alon/components/plugin）
    ↓
步骤 7: Model 组件（alon/components/model）
    ↓
步骤 6: Agno 桥接（extended/agno 子集）
    ↓
步骤 5: 后台任务管控（memory_task）
    ↓
步骤 3: Models（ORM）
    ↓
步骤 2: Schemas（请求/响应 DTO）
    ↓
步骤 1: 控制器层（接口本体）
```

### 2.2 外部依赖

| 依赖项 | 版本要求 | 说明 |
|--------|----------|------|
| agno | 2.5.9 | LLM 框架，必须锁定版本 |
| agno[openai] | 2.5.9 | OpenAI 协议支持 |
| PostgreSQL | >= 14 | 会话/记忆持久化 |
| Redis | >= 6 | 任务管控（可选降级） |

---

## 三、详细迁移步骤

---

### 步骤 4：通用基础设施

**依赖状态**：无外部依赖，第一步迁移

#### 必需文件清单

```
alon/
├── common/
│   ├── ctx.py                    # CTX_TENANT_ID, CTX_USER_ID, CTX_TOKEN 等 contextvars
│   ├── dependency.py             # DependAuth, DependTenant 鉴权依赖
│   └── exceptions.py             # BadRequestError, NotFoundError 等统一异常
├── configs/
│   ├── settings.py               # settings 单例入口
│   ├── yaml.py                   # YamlParser 配置加载
│   └── business/                 # 业务配置模块
│       └── workflow.py           # task_cleanup_timeout 等配置
├── core/
│   └── common/
│       └── env.py                # PYTHON_SERVICE_ENV 解析
└── utils/
    ├── json_util.py              # orjson_default
    └── agno_util.py              # extract_usage_from_agent
```

#### 改造要点

1. **contextvars 适配**：确认目标项目的租户/用户上下文机制，可能需要重写 CTX_TENANT_ID / CTX_USER_ID 的初始化方式
2. **配置加载**：若目标项目无 YAML 分层配置，可简化为环境变量 + Pydantic Settings
3. **鉴权依赖**：根据目标项目的认证方式调整 DependAuth / DependTenant

#### 验证方法

```python

#### 测试 contextvars

from alon.common.ctx import CTX_TENANT_ID, CTX_USER_ID
CTX_TENANT_ID.set(\"test-tenant\")
assert CTX_TENANT_ID.get() == \"test-tenant\"

#### 测试 settings

from alon.configs.settings import settings
assert hasattr(settings, \"workflow\")
```

---

### 步骤 9：Plugin SDK（协议与实体定义）

**依赖状态**：依赖步骤 4（common/configs）

#### 必需文件清单

```
alon_plugin/
├── sdk/
│   ├── entities/
│   │   ├── model/
│   │   │   ├── llm.py            # LLMResult, LLMResultChunk, LLMUsage
│   │   │   ├── message.py        # PromptMessage 系列（User/System/Assistant/Tool）
│   │   │   └── model.py          # ModelType 枚举
│   │   └── tool/
│   │       └── tool.py           # ToolCall 实体
│   ├── interfaces/
│   │   └── model.py              # LargeLanguageModel 接口定义
│   └── protocol/
│       └── enums.py              # 通信协议枚举
└── **init**.py
```

#### 改造要点

1. **包名重命名**：若目标项目包名不同，需全局替换 alon_plugin → <newpkg>_plugin
2. **协议实体无需修改**：LLMResult / PromptMessage 等是平台无关的数据结构，可直接复用

#### 验证方法

```python
from alon_plugin.sdk.entities.model.llm import LLMResult, LLMResultChunk
from alon_plugin.sdk.entities.model.message import UserPromptMessage

msg = UserPromptMessage(content=\"test\")
assert msg.role.value == \"user\"
```

---

### 步骤 8：Plugin 组件（模型实际传输层）

**依赖状态**：依赖步骤 4、步骤 9；同时依赖你的数据/缓存/消息组件

#### 必需文件清单

```
alon/components/plugin/
├── client/
│   ├── model_client.py           # 【核心】ModelClient.invoke_llm
│   ├── plugin/
│   │   ├── entities/
│   │   │   └── plugin.py         # ModelProviderID 解析器
│   │   └── plugin_manager.py     # PluginManager 客户端代理
│   └── **init**.py
├── engine/
│   ├── core/
│   │   ├── plugin_manager.py     # 【核心】TenantPluginManager（懒启动+通信）
│   │   └── plugin_process.py     # 插件子进程管理
│   ├── utils/
│   │   └── helpers.py            # 工具函数
│   └── security/                 # 安全扫描（可选，按需搬迁）
└── **init**.py
```

#### 改造要点

1. **数据组件适配**：PluginManager 依赖 Redis（任务状态/进程锁），需适配你的 Redis 连接管理
2. **OSS 适配**：若插件包存储走 OSS，需适配你的对象存储组件
3. **裁剪建议**：
   - 若不需要"安装/卸载插件"能力，可省略 engine/security/、engine/warmup/
   - 最小集：client/model_client.py + engine/core/plugin_manager.py

#### 验证方法

```python
from alon.components.plugin.client.model_client import ModelClient

client = ModelClient()

#### 需要先启动一个模型插件，测试 invoke_llm

#### async for chunk in client.invoke_llm(...)

#### print(chunk)

```

---

### 步骤 7：Model 组件（统一模型门面）

**依赖状态**：依赖步骤 4、步骤 8、步骤 9；同时依赖你的数据/缓存组件

#### 必需文件清单

```
alon/components/model/
├── services/
│   ├── llm_service.py            # 【核心】LLMService.invoke/stream
│   ├── embedding_service.py      # EmbeddingService（可选）
│   ├── rerank_service.py         # RerankService（可选）
│   └── management_service.py     # ModelService（模型清单管理）
├── internal/
│   ├── model_provider_factory.py # 【核心】get_model_type_instance
│   ├── model_instance_factory.py # 【核心】ModelInstance.invoke_llm
│   ├── provider_configuration.py # ProviderConfiguration
│   ├── provider_manager.py       # ProviderManager
│   └── configs/
│       └── alon_config.py        # AlonConfig
├── model_providers/
│   └── **base**/
│       ├── ai_model.py           # AIModel 基类
│       ├── large_language_model.py # 【核心】LargeLanguageModelImpl.invoke
│       ├── text_embedding_model.py
│       └── rerank_model.py
├── entities/                     # 模型配置实体
├── errors/                       # 模型调用异常
├── schema/                       # 模型 Schema 定义
├── schema_validators/            # 参数校验器
├── callbacks/                    # 回调机制
├── utils/                        # 工具函数
└── **init**.py

alon/services/
└── model.py                      # ModelService（DB 侧凭证 CRUD）
```

#### 改造要点

1. **凭证存储适配**：ModelService 查询模型凭证依赖你的数据库模型，需重写 get_model_credentials 等方法
2. **缓存适配**：模型清单/凭证缓存依赖你的缓存组件（biocache 或自定义）
3. **插件桥接确认**：LargeLanguageModelImpl.invoke 内部调用 ModelClient().invoke_llm，确保步骤 8 已正确适配

#### 验证方法

```python
from alon.components.model.services.llm_service import LLMService

llm_service = LLMService(tenant_id=\"test-tenant\")

#### async for chunk in llm_service.stream(prompt_messages=[...], model=\"gpt-4\", provider=\"xxx/openai\")

#### print(chunk)

```

---

### 步骤 6：Agno 桥接（业务执行框架）

**依赖状态**：依赖步骤 4、步骤 7、步骤 9；同时依赖外部库 agno

#### 前置条件

```bash
uv add \"agno[openai]==2.5.9\"
```

**⚠️ 版本必须锁定**：agno 升级可能改变 Model / Agent 接口签名

#### 必需文件清单（仅迁移子集）

```
extended/agno/
├── models/
│   └── alon/
│       ├── alon.py               # 【核心】Alon 类，桥接 agno.Model → LLMService
│       └── **init**.py
├── agent/
│   ├── agent.py                  # 【核心】异步增强 Agent
│   └── **init**.py
├── db/
│   ├── postgres/
│   │   ├── helpers.py            # 【核心】get_db() 返回 AgnoPostgresDb
│   │   └── **init**.py
│   └── **init**.py
├── session/
│   ├── summary.py                # 会话摘要管理（Alon 间接引用）
│   └── **init**.py
└── **init**.py
```

#### 可选目录（本接口未用到）

```
extended/agno/
├── knowledge/                    # 知识库相关，可省略
├── vectordb/                     # 向量库相关，可省略
└── tools/                        # 插件工具桥接，可省略（联网搜索用 agno 自带 BaiduSearchTools）
```

#### 改造要点

1. **import 路径替换**：alon.py 第 18-22 行硬编码了平台路径

```python

#### 原代码

from alon.components.model import get_models
from alon.components.model.services.llm_service import LLMService
from alon.configs.settings import settings

#### 改为你的新路径

from <newpkg>.components.model import get_models
from <newpkg>.components.model.services.llm_service import LLMService
from <newpkg>.configs.settings import settings
```

1. **数据库连接适配**：get_db() 返回的 AgnoPostgresDb 需配置你的 PostgreSQL 连接参数

2. **最小冒烟测试**：完成本步骤后，先测试 Alon 类能否正确调用

#### 验证方法

```python
from extended.agno.models.alon import Alon

model = Alon(
    id=\"gpt-4\",
    tenant_id=\"test-tenant\",
    user=\"test-user\",
    provider=\"<plugin_id>/openai\",
    parameters={\"temperature\": 0.7},
)

#### 测试非流式调用

response = await model.ainvoke(messages=[...], assistant_message=...)
print(response.content)

#### 测试流式调用

async for chunk in model.ainvoke_stream(messages=[...], assistant_message=...):
    print(chunk.content)
```

---

### 步骤 5：后台任务管控（停止 / 超时清理）

**依赖状态**：依赖步骤 4；同时依赖你的消息组件（Redis Pub/Sub）

#### 必需文件清单

```
alon/listeners/services/pubsub/memory_task/
├── **init**.py
├── constants.py                  # TASK_TYPE_GENERATE_LLM, ACTIVE_CLEANUP_TASKS
├── helpers.py                    # stop_task_by_id
├── cleanup.py                    # cleanup_task_after_timeout
└── cancel_asyncio_task.py        # asyncio 任务取消逻辑
```

#### 改造要点

1. **消息组件适配**：
   - 原实现依赖 Redis Pub/Sub 做跨进程任务停止
   - 若目标项目有同类消息组件，适配 stop_task_by_id 的发布/订阅逻辑
   - **降级方案**：若无需跨进程停止，可简化为本地 asyncio 任务管理（仅保留 cancel_asyncio_task.py 逻辑）

2. **配置依赖**：cleanup_task_after_timeout 读取 settings.workflow.task_cleanup_timeout，需确保步骤 4 的配置已迁移

3. **任务类型扩展**：若目标项目有其他任务类型，需在 constants.py 中补充

#### 验证方法

```python
import asyncio
from alon.listeners.services.pubsub.memory_task import cleanup_task_after_timeout

async def test_cleanup():
    task_id = \"test-task-123\"
    # 启动一个长时间任务
    # 调用 cleanup_task_after_timeout 验证超时取消逻辑
    await cleanup_task_after_timeout(task_id, \"llm\", \"LLM任务\", lambda: 10)

asyncio.run(test_cleanup())
```

---

### 步骤 3：Models（ORM）

**依赖状态**：依赖步骤 4、步骤 5

#### 必需文件清单

```
alon/models/
├── core/
│   ├── base.py                   # BaseModel（ORM 基类）
│   ├── engine.py                 # async_session 会话工厂
│   ├── constants.py              # TABLE_PREFIX
│   └── schema.py                 # DEFAULT_SCHEMA
├── mixins/
│   ├── active_record.py          # ActiveRecordMixin（one_by_id, create, update 等）
│   ├── audit.py                  # AuditedTimestampMixin, AuditedOperatorMixin
│   └── tenant.py                 # TenantMixin
├── types/
│   ├── datetime.py               # UTCDateTime
│   ├── enum.py                   # StringEnum
│   └── uuid.py                   # StringUUID
├── enums.py                      # AppMode, ConversationMode, ConversationStatus, MessageStatus
├── conversation.py               # Conversation, Message 模型
└── **init**.py

alon/migrations/
└── versions/
    └── YYYYMMDD_HHMM_create_conversation_tables.py  # 迁移文件（需提取）
```

#### 改造要点

1. **数据库适配**：
   - 确保 sync_session 工厂使用你的数据库连接池
   - 表名前缀 TABLE_PREFIX 可根据目标项目规范调整

2. **迁移脚本**：提取 Conversation / Message 两张表的建表语句，生成新迁移

3. **字段裁剪**：若目标项目不需要全部字段，可按需删减（如 workflow_run_id 等）

#### 验证方法

```python
from alon.models.conversation import Conversation, Message
from alon.models.core.engine import async_session

async def test_models():
    async with async_session() as session:
        conv = await Conversation.create(session, {
            \"app_id\": \"test-app\",
            \"name\": \"测试会话\",
            \"status\": \"normal\",
        })
        await session.commit()
        assert conv.id is not None

import asyncio
asyncio.run(test_models())
```

---

### 步骤 2：Schemas（请求/响应 DTO）

**依赖状态**：依赖步骤 4

#### 必需文件清单

```
alon/schemas/
├── base.py                       # BaseModel, Success, SuccessExtra 基类
├── completion.py                 # LLMChatCompletion, FileItem, ModelConfig, SearchConfig
└── portal/
    └── app.py                    # StopPortalAppChatSuccessRespModel
```

#### 改造要点

1. **字段校验**：FileItem 的  ype 校验当前仅支持 image，若有扩展需求可调整
2. **响应格式**：若目标项目有统一的响应封装，需适配 Success() / SuccessExtra() 的结构

#### 验证方法

```python
from alon.schemas.completion import LLMChatCompletion, ModelConfig

req = LLMChatCompletion(
    model=ModelConfig(name=\"gpt-4\", provider=\"xxx/openai\"),
    query=\"你好\",
)
assert req.query == \"你好\"
```

---

### 步骤 1：控制器层（接口本体）

**依赖状态**：依赖所有前序步骤

#### 必需文件清单

```
alon/controllers/portal/v1/generate/
├── llm.py                        # 【核心】chat_messages, stop_chat_messages
└── **init**.py                   # 路由注册
```

#### 改造要点

1. **路由前缀调整**：原接口挂载在 /portal/v1/apps/llm/chat-messages，根据目标项目路由结构调整

```python

#### 原代码

router = APIRouter(
    prefix=\"/apps/llm\",
    tags=[\"门户-生成\"],
)

# 改为你的路由结构

router = APIRouter(
    prefix=\"/chat\",  # 或其他前缀
    tags=[\"LLM对话\"],
)
```

1. **APP_ID / APP_NAME**：原代码硬编码了固定 ID，若目标项目有多应用场景需参数化

```python
APP_ID: str = \"00000000-0000-0000-0000-000000000001\"
APP_NAME = \"通用智能体\"
```

1. **工具集成**：联网搜索使用了 BaiduSearchTools，若不需要可注释掉

2. **流式响应格式**：SSE 事件格式（EventType 枚举）若需对接前端，确认格式兼容

#### 完整验证

```bash

#### 启动服务

uv run runserver

#### 测试接口

curl -X POST <http://localhost:8000/portal/v1/apps/llm/chat-messages> \\
  -H \"Content-Type: application/json\" \\
  -H \"Authorization: Bearer <token>\" \\
  -d '{
    \"model\": {
      \"name\": \"gpt-4\",
      \"provider\": \"<plugin_id>/openai\",
      \"completion_params\": {\"temperature\": 0.7}
    },
    \"query\": \"你好，介绍一下自己\"
  }'
```

---

## 四、风险点与应对策略

### 4.1 版本锁定风险

| 风险项 | 影响 | 应对 |
|--------|------|------|
| agno 升级 | Model / Agent 接口变更 | 锁定 2.5.9，升级前测试全部用例 |
| SQLAlchemy 升级 | ORM 行为变化 | 锁定当前版本，迁移脚本单独验证 |
| agno 内部依赖冲突 | 安装失败 | 使用 uv lock 锁定完整依赖树 |

### 4.2 数据库兼容风险

| 风险项 | 影响 | 应对 |
|--------|------|------|
| pgvector 扩展未安装 | 向量字段报错 | 本接口未用向量字段，可跳过 |
| PostgreSQL 版本过低 | JSONB/异步驱动问题 | 确保 >= 14 版本 |
| 连接池配置不当 | 高并发超时 | 参考原项目的池化配置 |

### 4.3 插件通信风险

| 风险项 | 影响 | 应对 |
|--------|------|------|
| 插件子进程未启动 | invoke_llm 失败 | 确保插件已安装且处于 running 状态 |
| stdin/stdout 协议不匹配 | JSON 解析错误 | 使用原项目插件包，不自定义协议 |
| Redis 连接断开 | 任务停止信号丢失 | 实现重连机制或降级为本地任务管理 |

### 4.4 性能风险

| 风险项 | 影响 | 应对 |
|--------|------|------|
| 每次对话创建 Agent 实例 | 内存泄漏 | 使用单例池或显式清理 |
| 流式响应未正确关闭 | 连接残留 | 确保 inally 块发送 None 结束信号 |
| 记忆/摘要查询无索引 | 数据库慢查询 | 为 conversation_id / session_id 加索引 |

---

## 五、可选裁剪建议

若目标项目资源有限，可按以下优先级裁剪：

### 必须保留（核心能力）

- 步骤 4（common/configs）
- 步骤 9（Plugin SDK 实体层）
- 步骤 8（Plugin 客户端子集）
- 步骤 7（Model 组件 LLM 部分）
- 步骤 6（Agno 桥接必需子集）
- 步骤 2、步骤 1（Schemas + Controller）

### 可选降级

| 功能 | 原实现 | 降级方案 |
|------|--------|----------|
| 任务停止（跨进程） | Redis Pub/Sub | 本地 asyncio 任务取消 |
| 记忆管理 | AgnoPostgresDb | 禁用记忆功能 |
| 会话摘要 | LLM 生成 | 固定模板或禁用 |
| 联网搜索 | BaiduSearchTools | 注释工具集成代码 |
| 任务超时清理 | 定时器 + Redis | 简化为请求级 timeout |

### 可完全省略

- extended/agno/knowledge/ —— 知识库模块
- extended/agno/vectordb/ —— 向量库模块
- extended/agno/tools/impl/ —— 插件工具（除非后续要用）
- components/plugin/engine/warmup/ —— 插件预热
- components/plugin/engine/security/ —— 插件安全扫描
- components/model/services/embedding_service.py —— Embedding（本接口未用）
- components/model/services/rerank_service.py —— Rerank（本接口未用）

---

## 六、验证清单

迁移完成后，按以下清单逐项验证：

### 6.1 单元验证

- [ ] contextvars 正常工作（tenant_id / user_id）
- [ ] settings 加载成功
- [ ] Plugin SDK 实体序列化/反序列化正确
- [ ] ModelClient 能连接插件子进程
- [ ] LLMService.stream 返回正确数据
- [ ] Alon 模型桥接调用成功
- [ ] Conversation / Message ORM 增删改查正常

### 6.2 集成验证

- [ ] POST /chat-messages 返回 SSE 流
- [ ] 流式内容正确输出
- [ ] 会话 ID 创建/恢复逻辑正常
- [ ] 记忆跨会话保持
- [ ] 会话摘要自动生成
- [ ] 联网搜索工具调用（若启用）
- [ ] 任务停止接口生效
- [ ] 超时自动清理生效

### 6.3 性能验证

- [ ] 单次对话响应时间 < 3s（首 token）
- [ ] 并发 10 请求无阻塞
- [ ] 长对话（100 轮）内存无泄漏
- [ ] 流式响应正确关闭连接

---

## 七、参考资料

### 原项目关键文件

- 控制器：packages/platform/src/alon/controllers/portal/v1/generate/llm.py
- 模型桥接：packages/platform/src/extended/agno/models/alon/alon.py
- LLM 服务：packages/platform/src/alon/components/model/services/llm_service.py
- 插件客户端：packages/platform/src/alon/components/plugin/client/model_client.py

### 外部文档

- agno 官方文档：<https://github.com/agno-agi/agno>
- FastAPI SSE 响应：<https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse>
- SQLAlchemy 异步：<https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html>

---

## 八、更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-06-02 | 初始版本，完整迁移方案 |
