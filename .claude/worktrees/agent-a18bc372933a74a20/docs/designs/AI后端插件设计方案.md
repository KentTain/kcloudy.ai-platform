# Alon 插件系统设计方案

## 1. 概述

Alon 插件系统是一个企业级动态插件框架，支持多租户隔离、多插件类型、安全的沙箱执行环境。插件以独立子进程运行，通过 JSON over stdin/stdout 协议与主进程通信，实现了业务逻辑的可插拔扩展。

## 2. 核心架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Alon 主进程                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PluginManagementService                          │   │
│  │                     (服务层门面)                                     │   │
│  │  • install_plugin()  • start_plugin()  • stop_plugin()             │   │
│  │  • uninstall_plugin()  • invoke_plugin_stream()                    │   │
│  │  • 凭证管理 (create/update/delete credential)                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    PluginManagerFactory                             │   │
│  │                     (工厂单例)                                       │   │
│  │  • get_manager(tenant_id) → TenantPluginManager                    │   │
│  │  • 多租户管理器缓存                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│          ┌─────────────────────────┼─────────────────────────┐             │
│          ▼                         ▼                         ▼             │
│  ┌───────────────┐        ┌───────────────┐        ┌───────────────┐      │
│  │TenantManager  │        │TenantManager  │        │TenantManager  │      │
│  │  (tenant_1)   │        │  (tenant_2)   │        │  (tenant_N)   │      │
│  └───────┬───────┘        └───────┬───────┘        └───────┬───────┘      │
│          │                        │                        │               │
│          ▼                        ▼                        ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      TenantPluginManager                            │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │   │
│  │  │  plugins    │  │  running_   │  │  session_   │  │  security │  │   │
│  │  │  (注册表)   │  │  plugins    │  │  manager    │  │  manager  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │   │
│  │  │ performance │  │   warmup    │  │  runtime    │                 │   │
│  │  │  _monitor   │  │  _manager   │  │  _factory   │                 │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                 │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ JSON over stdin/stdout
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           插件子进程 (隔离运行)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                          Plugin (SDK)                               │   │
│  │                      继承 IOServer + Router                         │   │
│  │  • 加载 manifest.yaml                                               │   │
│  │  • 注册工具/模型/端点/智能体策略                                     │   │
│  │  • 处理请求路由分发                                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  ┌─────────────┐ │
│  │    Tool       │  │    Model      │  │   Endpoint    │  │    Agent    │ │
│  │  Provider     │  │   Provider    │  │   Handler     │  │  Strategy   │ │
│  └───────────────┘  └───────────────┘  └───────────────┘  └─────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. 三层架构

### 3.1 引擎层 (Engine)

**位置**: `alon/components/plugin/engine/`

引擎层运行在主进程内，负责插件的全生命周期管理。

| 模块 | 职责 |
|------|------|
| `core/plugin_manager.py` | `TenantPluginManager` - 租户级插件管理器，维护插件注册表和运行实例 |
| `core/runtime/` | 插件运行时抽象，`LocalPluginRuntime` 实现本地子进程模式 |
| `core/communication/` | 通信协议封装，`PluginMessageProtocol` 处理 JSON 消息序列化 |
| `core/security/` | 安全管理器，权限校验和敏感操作拦截 |
| `core/session/` | 会话管理器，追踪插件调用链路 |
| `core/warmup/` | 预热管理器，启动时预加载高优先级插件 |
| `core/monitoring/` | 性能监控，收集调用次数、耗时、错误率 |
| `api/routes/` | REST API 端点，提供管理接口 |

**核心类 - TenantPluginManager**:

```python
class TenantPluginManager:
    # 插件注册表
    plugins: dict[str, PluginInfo]           # plugin_id -> 元数据
    running_plugins: dict[str, PluginRuntime] # plugin_id -> 运行实例
    
    # 核心方法
    async def install_plugin(plugin_package, request) -> str
    async def start_plugin(plugin_id) -> bool
    async def stop_plugin(plugin_id) -> bool
    async def invoke_plugin_stream(plugin_id, params, timeout) -> AsyncGenerator
    async def get_plugin_asset(plugin_id, asset_path) -> bytes
```

### 3.2 客户端层 (Client)

**位置**: `alon/components/plugin/client/`

客户端层提供对插件的调用接口，供其他组件消费。

| 客户端 | 用途 |
|--------|------|
| `ToolClient` | 工具调用，返回 `ToolInvokeMessage` 流式响应 |
| `ModelClient` | LLM/Embedding/Rerank 模型调用 |

**ToolClient 核心方法**:

```python
class ToolClient(BasePluginClient):
    async def fetch_tool_providers(tenant_id) -> list[PluginToolProviderEntity]
    async def invoke(
        tenant_id, user_id, tool_provider, tool_name,
        credentials, tool_parameters
    ) -> AsyncGenerator[ToolInvokeMessage, None]
    async def validate_provider_credentials(tenant_id, user_id, provider, credentials) -> bool
```

### 3.3 SDK 层

**位置**: `alon_plugin/`

SDK 层供插件开发者使用，定义了插件的标准接口和通信协议。

```
alon_plugin/
├── plugin.py                 # Plugin 主类，入口点
├── sdk/
│   ├── entities/            # 实体定义
│   │   ├── tool.py          # Tool, ToolProvider 基类
│   │   ├── model/           # LLM, Embedding, Rerank 等模型基类
│   │   ├── agent.py         # Agent 策略基类
│   │   └── endpoint.py      # 端点处理器基类
│   └── interfaces/          # 接口定义
│       ├── tool/            # Tool 接口规范
│       └── model/           # Model 接口规范
└── server/
    ├── core/
    │   ├── server/          # IO 服务器 (stdio/tcp)
    │   ├── plugin_executor.py    # 请求执行器
    │   └── plugin_registration.py # 插件注册
    └── invocations/         # 各类调用处理器
```

**Plugin 主类**:

```python
class Plugin(IOServer, Router):
    def __init__(self, config: AlonPluginEnv):
        # 1. 加载 manifest.yaml
        self.registration = PluginRegistration(config)
        
        # 2. 根据安装方式选择通信方式
        if config.INSTALL_METHOD == InstallMethod.Local:
            # stdin/stdout JSON 通信
            reader, writer = self._launch_local_stream(config)
        elif config.INSTALL_METHOD == InstallMethod.Remote:
            # TCP 远程连接
            reader, writer = self._launch_remote_stream(config)
        
        # 3. 初始化执行器
        self.plugin_executer = PluginExecutor(config, self.registration)
```

## 4. 插件类型

| 类型 | 枚举值 | 用途 | 实现基类 |
|------|--------|------|----------|
| **Tool** | `tool` | 工具插件，提供可调用的工具方法 | `Tool`, `ToolProvider` |
| **Model** | `model` | AI 模型插件 (LLM/Embedding/Rerank) | `LargeLanguageModel`, `TextEmbeddingModel`, `RerankModel` |
| **Agent** | `agent` | AI 代理插件，自定义智能体策略 | `AgentStrategy` |
| **OAuth** | `oauth` | OAuth 认证插件 | `OAuthProvider` |
| **Endpoint** | `endpoint` | 端点插件，提供自定义 HTTP 端点 | `EndpointHandler` |

## 5. 插件生命周期

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           插件生命周期状态机                               │
└───────────────────────────────────────────────────────────────────────────┘

                         ┌─────────────┐
                         │   上传ZIP   │
                         └──────┬──────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. 安装阶段 (install_plugin)                                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │  解析 ZIP   │───▶│  校验签名   │───▶│  安全扫描   │───▶│  上传 OSS   │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│                                                                    │        │
│                                                                    ▼        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │ 写入数据库  │◀───│ 创建 .venv  │◀───│ 安装依赖    │◀───│ 解压文件    │ │
│  │(INACTIVE)   │    └─────────────┘    └─────────────┘    └─────────────┘ │
│  └─────────────┘                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                │ auto_start=True 或手动启动
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. 启动阶段 (start_plugin) - 懒启动                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │ 检查缓存    │───▶│prepare()    │───▶│ fork 子进程 │───▶│ 等待心跳    │ │
│  │ (.prepared) │    │ 环境准备    │    │ 执行 main.py│    │ 确认可用    │ │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘ │
│                                                                    │        │
│                                                                    ▼        │
│                         ┌─────────────────────────────────────────────┐  │
│                         │  状态: ACTIVE                               │  │
│                         │  更新: port, process_id, last_started_at   │  │
│                         └─────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                │ 运行中
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. 运行阶段 (invoke_plugin_stream)                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   主进程                              插件子进程                            │
│   ────────                            ────────                              │
│       │                                   │                                 │
│       │  ─────── JSON Request ───────▶   │                                 │
│       │  {session_id, event, data}       │                                 │
│       │                                   │  执行 Tool/Model                │
│       │  ◀─────── JSON Response ───────  │                                 │
│       │  {event: "message", ...}         │                                 │
│       │                                   │                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                │
                                │ stop_plugin / uninstall_plugin
                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. 停止/卸载阶段                                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐ │
│  │ 终止子进程  │───▶│ 清理内存    │───▶│ 更新状态    │───▶│ 删除目录    │ │
│  │ SIGTERM     │    │ running_    │    │ INACTIVE    │    │ (卸载时)    │ │
│  └─────────────┘    │ plugins     │    └─────────────┘    └─────────────┘ │
│                     └─────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6. 通信协议

### 6.1 消息格式

主进程与插件子进程通过 JSON 消息通信，以换行符 `\n` 分隔消息。

**请求消息 (主进程 → 插件)**:

```json
{
  "session_id": "session_xxx",
  "event": "request",
  "data": {
    "action": "invoke_tool",
    "tool_name": "web_search",
    "tool_parameters": {"query": "..."},
    "credentials": {...}
  },
  "conversation_id": "conv_xxx",
  "message_id": "msg_xxx",
  "app_id": "app_xxx"
}
```

**响应消息 (插件 → 主进程)**:

```json
// 流式消息
{"event": "message", "session_id": "session_xxx", "data": {"text": "部分结果..."}}

// 错误消息
{"event": "error", "session_id": "session_xxx", "data": {"error": "错误信息"}}

// 完成消息
{"event": "end", "session_id": "session_xxx"}

// 心跳消息
{"event": "heartbeat", "timestamp": "2026-06-02T10:00:00Z"}
```

### 6.2 协议类

```python
class PluginInStream(BaseModel):
    session_id: str
    event: PluginInStreamEvent  # request, ping, etc.
    data: dict[str, Any]
    conversation_id: str | None = None
    message_id: str | None = None
    app_id: str | None = None

class PluginMessageProtocol:
    @staticmethod
    def create_request_message(invoke_request, session_id) -> PluginInStream
    
    @staticmethod
    def to_bytes(request: PluginInStream) -> bytes  # JSON + "\n"
    
    @staticmethod
    def parse_message(message_str) -> StreamOutputMessage | dict | None
```

## 7. 数据模型

### 7.1 核心表

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          数据库表结构                                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐     ┌─────────────────────────────┐
│      t_plugin               │     │   t_plugin_installation     │
│  (全局插件元数据)            │     │   (租户安装记录)             │
├─────────────────────────────┤     ├─────────────────────────────┤
│ id (PK)                     │     │ id (PK)                     │
│ plugin_id (索引)            │◀───│ plugin_id (索引)            │
│ plugin_unique_identifier    │     │ tenant_id (索引)            │
│ install_type                │     │ plugin_unique_identifier    │
│ refers (引用计数)           │     │ runtime_type                │
│ manifest_type               │     │ plugin_type                 │
│ remote_declaration          │     │ status (ACTIVE/INACTIVE)    │
│ created_at / updated_at     │     │ auto_start                  │
└─────────────────────────────┘     │ process_id, port            │
                                    │ call_count, error_count     │
                                    │ installed_at, last_started  │
                                    │ plugin_config (JSON)        │
                                    │ install_config (JSON)       │
                                    └─────────────────────────────┘
                                            
┌─────────────────────────────┐     ┌─────────────────────────────┐
│   t_plugin_credentials      │     │  t_plugin_install_task      │
│   (插件凭证)                 │     │  (安装任务)                  │
├─────────────────────────────┤     ├─────────────────────────────┤
│ id (PK)                     │     │ id (PK)                     │
│ plugin_id (索引)            │     │ tenant_id                   │
│ tenant_id                   │     │ status (running/success/    │
│ plugin_type                 │     │        failed)              │
│ scope (GLOBAL/PERSONAL)     │     │ total_plugins               │
│ name                        │     │ completed_plugins           │
│ provider_name               │     │ plugins (JSON 状态列表)     │
│ credentials (加密 JSON)     │     └─────────────────────────────┘
└─────────────────────────────┘
```

### 7.2 PluginInstallation 关键字段

```python
class PluginInstallation(BaseModel, TenantMixin, ActiveRecordMixin):
    plugin_id: str                    # author/plugin_name
    plugin_type: PluginType           # tool, model, agent, oauth, endpoint
    runtime_type: RuntimeType         # local, remote, container
    status: PluginStatus              # ACTIVE, INACTIVE
    
    # 生命周期时间戳
    installed_at: datetime
    last_started_at: datetime
    last_stopped_at: datetime
    last_accessed_at: datetime        # 用于冻结判断
    
    # 运行时信息
    process_id: int                   # 子进程 PID
    port: int                         # 服务端口
    
    # 统计指标
    call_count: int
    error_count: int
    last_error: str
    
    # 配置
    auto_start: bool                  # 服务重启时自动启动
    freeze_threshold_hours: int       # 冻结阈值
    plugin_config: PluginConfig       # 完整插件配置
```

## 8. 安全机制

### 8.1 安全扫描

```python
class SecurityManager:
    """安全管理器"""
    
    # 禁止的模块/函数
    FORBIDDEN_MODULES = {'os.system', 'subprocess', 'eval', 'exec', ...}
    
    # 权限配置
    # 在 manifest.yaml 中声明需要的权限
    # permissions:
    #   - storage:read
    #   - network:external
    #   - file:write
    
    async def scan_plugin_code(self, plugin_dir: Path) -> list[SecurityIssue]
    def validate_permission(self, permission: str) -> bool
```

### 8.2 权限模型

```yaml
# manifest.yaml 示例
resource:
  permission:
    - storage:read      # 读取存储
    - storage:write     # 写入存储
    - network:internal  # 内部网络访问
    - network:external  # 外部网络访问
```

### 8.3 凭证加密

```python
# 凭证存储前加密
encrypted = tool_store_service.encrypt_credentials(
    tenant_id, credentials, credentials_schema
)

# 凭证读取时解密并脱敏
decrypted = tool_store_service.decrypt_credentials(
    tenant_id, record.credentials, credentials_schema
)
masked = tool_store_service.mask_credentials(decrypted, credentials_schema)
```

## 9. 性能优化

### 9.1 懒启动

插件不在服务启动时全部拉起，而是在首次调用时按需启动：

```python
async def invoke_plugin_stream(self, plugin_id, params, timeout):
    # 检查是否已运行
    if plugin_id not in self.running_plugins:
        # 懒启动
        await self.start_plugin(plugin_id)
    
    runtime = self.running_plugins[plugin_id]
    async for chunk in runtime.invoke_stream(params, timeout):
        yield chunk
```

### 9.2 预热机制

启动时预热高优先级插件，减少首次调用延迟：

```python
class PluginWarmupManager:
    async def startup_warmup(self) -> WarmupResult:
        """启动时预热 auto_start=True 的插件"""
        warmup_candidates = [
            p for p in self.plugins.values()
            if p.auto_start and p.status == PluginStatus.ACTIVE
        ]
        # 按优先级排序，并发预热
```

### 9.3 缓存策略

```python
class TenantPluginManager:
    # 插件准备状态缓存
    _plugin_ready_cache: dict[str, float]  # TTL 60s
    
    # 插件启动锁，防止并发启动同一插件
    _plugin_start_locks: dict[str, asyncio.Lock]
```

## 10. 使用场景

### 10.1 工具插件 (Tool)

**场景**: 扩展 AI Agent 的工具能力

```python
# 插件开发者实现
class WebSearchTool(Tool):
    name = "web_search"
    description = "搜索互联网获取信息"
    
    def _invoke(self, query: str, credentials: dict) -> ToolInvokeMessage:
        api_key = credentials["api_key"]
        results = self._search(query, api_key)
        return self.create_text_message(results)

# 主进程调用
async for msg in tool_client.invoke(
    tenant_id, user_id, 
    tool_provider="alon/web_search/search",
    tool_name="web_search",
    credentials={"api_key": "xxx"},
    tool_parameters={"query": "天气"}
):
    print(msg)
```

### 10.2 模型插件 (Model)

**场景**: 接入第三方 LLM/Embedding 服务

```python
# 插件开发者实现
class TongyiLLM(LargeLanguageModel):
    def _invoke(self, model: str, credentials: dict, 
                prompt_messages: list[PromptMessage], 
                model_parameters: dict) -> LLMResult:
        # 调用通义千问 API
        return self._call_tongyi_api(model, credentials, prompt_messages)

# 主进程通过 model_manager 调用
llm_service = model_manager.get_llm_service(tenant_id, "tongyi/qwen")
result = await llm_service.invoke(messages, model_parameters)
```

### 10.3 端点插件 (Endpoint)

**场景**: 提供自定义 HTTP 端点

```yaml
# manifest.yaml
endpoints:
  - path: "/custom/webhook"
    method: "POST"
    handler: "WebhookHandler"
```

```python
class WebhookHandler(EndpointHandler):
    async def handle(self, request: Request) -> Response:
        # 处理 webhook 请求
        return JSONResponse({"status": "ok"})
```

### 10.4 智能体策略插件 (Agent)

**场景**: 自定义 Agent 行为策略

```python
class CustomAgentStrategy(AgentStrategy):
    name = "react_agent"
    
    async def run(self, query: str, tools: list[Tool], 
                  conversation: Conversation) -> AsyncGenerator:
        # 实现 ReAct 循环
        while not self._should_stop(query):
            thought = await self._think(query, conversation)
            action = await self._decide_action(thought, tools)
            observation = await self._execute_action(action)
            yield self._create_message(observation)
```

## 11. API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/admin/v1/plugin` | GET | 获取插件列表 |
| `/admin/v1/plugin` | POST | 安装插件 (上传 ZIP) |
| `/admin/v1/plugin/{plugin_id}` | GET | 获取插件详情 |
| `/admin/v1/plugin/{plugin_id}/start` | POST | 启动插件 |
| `/admin/v1/plugin/{plugin_id}/stop` | POST | 停止插件 |
| `/admin/v1/plugin/{plugin_id}/upgrade` | POST | 升级插件 |
| `/admin/v1/plugin/{plugin_id}` | DELETE | 卸载插件 |
| `/admin/v1/plugin/{plugin_id}/credentials` | GET | 获取凭证列表 |
| `/admin/v1/plugin/{plugin_id}/credentials` | POST | 创建凭证 |
| `/admin/v1/plugin/{plugin_id}/credentials/{cred_id}` | PUT | 更新凭证 |
| `/admin/v1/plugin/{plugin_id}/credentials/{cred_id}` | DELETE | 删除凭证 |

## 12. CLI 管理

```bash
# 安装插件
uv run python manage.py plugin install /path/to/plugin.zip --auto-start

# 启动插件
uv run python manage.py plugin start alon/tongyi

# 停止插件
uv run python manage.py plugin stop alon/tongyi

# 查看插件状态
uv run python manage.py plugin status

# 健康检查
uv run python manage.py plugin health alon/tongyi

# 调试调用
uv run python manage.py plugin invoke alon/tongyi \
    --tool web_search \
    --params '{"query": "test"}'
```

## 13. 插件开发示例

### 13.1 manifest.yaml

```yaml
version: "1.0"
author: alon
name: web_search
label:
  en_US: Web Search
  zh_Hans: 网页搜索
description:
  en_US: Search the web for information
  zh_Hans: 搜索互联网获取信息
icon: search.svg
resource:
  memory: 256
  permission:
    - network:external
tools:
  - identity:
      name: search
      author: alon
      label:
        zh_Hans: 搜索
    description:
      zh_Hans: 搜索互联网
    parameters:
      - name: query
        type: string
        required: true
        label:
          zh_Hans: 查询词
    credentials_schema:
      - name: api_key
        type: string
        required: true
        label:
          zh_Hans: API密钥
```

### 13.2 main.py

```python
from alon_plugin import Plugin, Tool, ToolProvider, ToolInvokeMessage

class SearchTool(Tool):
    """网页搜索工具"""
    
    def _invoke(self, query: str, credentials: dict) -> ToolInvokeMessage:
        api_key = credentials["api_key"]
        
        # 调用搜索 API
        results = self._search(query, api_key)
        
        # 返回结果
        return self.create_text_message(
            text=json.dumps(results, ensure_ascii=False)
        )
    
    def _search(self, query: str, api_key: str) -> list:
        # 实现搜索逻辑
        pass

class SearchProvider(ToolProvider):
    """工具提供者"""
    
    def _validate_credentials(self, credentials: dict) -> bool:
        # 验证 API Key
        return self._test_api_key(credentials["api_key"])

if __name__ == "__main__":
    # 启动插件
    plugin = Plugin()
    plugin.run()
```

## 14. 总结

Alon 插件系统设计特点：

1. **多租户隔离**: 每个租户拥有独立的 `TenantPluginManager`，插件数据按租户隔离存储
2. **进程隔离**: 插件以独立子进程运行，故障不影响主进程稳定性
3. **安全沙箱**: 代码扫描 + 权限控制 + 凭证加密三重安全机制
4. **懒启动优化**: 按需启动，减少资源占用；支持预热机制降低首调延迟
5. **统一协议**: JSON over stdin/stdout，语言无关，便于扩展
6. **多类型支持**: Tool/Model/Agent/OAuth/Endpoint 五种插件类型覆盖常见扩展场景
7. **完整生命周期**: 安装 → 预处理 → 启动 → 运行 → 停止 → 卸载，状态可追踪
