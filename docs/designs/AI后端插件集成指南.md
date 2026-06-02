# 插件与 AI 框架集成指南

## 1. 集成架构概览

Alon 插件系统通过适配层与 Agno AI 框架集成，使插件工具能够被 Agent 和工作流节点调用。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AI 框架集成架构                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            应用层                                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     │
│   │   AgentNode     │     │   ToolNode      │     │  其他工作流节点  │     │
│   │  (智能体节点)    │     │   (工具节点)     │     │                 │     │
│   └────────┬────────┘     └────────┬────────┘     └─────────────────┘     │
│            │                       │                                       │
│            │  _create_tools()      │  invoke()                             │
│            ▼                       ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                        ToolManager                                   │  │
│   │  • create_tool_instance() → 创建工具实例                             │  │
│   │  • call_tool_function() → 执行工具调用                               │  │
│   │  • _prepare_tool_parameters() → 准备参数                             │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                        ToolFactory                                   │  │
│   │  create_tool(provider_type) → 根据类型创建工具                       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│            ┌───────────────────────┼───────────────────────┐               │
│            ▼                       ▼                       ▼               │
│   ┌───────────────┐     ┌───────────────┐     ┌───────────────┐           │
│   │  PluginTools  │     │  CustomTools  │     │   MCPTools    │           │
│   │  (插件工具)   │     │  (自定义工具)  │     │  (MCP工具)    │           │
│   │   BaseTool    │     │   BaseTool    │     │   BaseTool    │           │
│   └───────┬───────┘     └───────────────┘     └───────────────┘           │
│           │                                                                 │
│           ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                        ToolClient                                    │  │
│   │  • fetch_tool_providers() → 获取插件工具列表                         │  │
│   │  • invoke() → 调用插件工具                                           │  │
│   │  • validate_provider_credentials() → 验证凭证                        │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                   TenantPluginManager                                │  │
│   │  • invoke_plugin_stream() → 流式调用插件                             │  │
│   │  • start_plugin() → 懒启动插件                                       │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ JSON over stdin/stdout
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           插件子进程                                         │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                      Tool / ToolProvider                             │  │
│   │  • _invoke() → 执行工具逻辑                                          │  │
│   │  • _validate_credentials() → 验证凭证                                │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2. 核心组件

### 2.1 BaseTool (Agno 工具基类)

**位置**: `extended/agno/tools/base.py`

所有工具类型继承自 Agno 的 `Toolkit` 类，适配 Alon 工作流运行时：

```python
class BaseTool(Toolkit, ABC):
    """工具基类，定义所有工具类的公共接口"""
    
    def __init__(
        self,
        node_data: ToolNodeData,      # 工具节点配置
        state: GraphRuntimeState,     # 工作流运行状态
        runtime: "Runtime[GraphContext]",  # 运行时上下文
        function_name: str | None = None,
    ):
        self.node_data = node_data
        self.state = state
        self.runtime = runtime
        self.tenant_id = runtime.context.tenant_id
        self.function_info: FunctionInfo | None = None
        self.parameters: dict[str, Any] = {}
    
    @classmethod
    @abstractmethod
    def get_provider_type(cls) -> ToolType:
        """返回工具类型标识"""
        pass
    
    @abstractmethod
    async def load_function_info(self) -> FunctionInfo:
        """加载工具元信息（名称、描述、参数）"""
        pass
    
    @abstractmethod
    async def invoke(self, parameters: dict[str, Any]) -> ToolResponse:
        """执行工具调用"""
        pass
    
    async def initialize(self):
        """初始化工具（加载元信息、注册到 Toolkit）"""
        self.function_info = await self.load_function_info()
        # 将工具函数注册到 Toolkit
        self.register(self._tool_function)
    
    def _tool_function(self, **kwargs) -> str:
        """Agno 调用的入口函数"""
        return asyncio.run_event_loop(self._async_invoke(kwargs))
```

### 2.2 PluginTools (插件工具实现)

**位置**: `extended/agno/tools/impl/plugin.py`

```python
class PluginTools(BaseTool):
    """插件工具 - 连接 Agno 与插件系统"""
    
    def __init__(self, node_data, state, runtime, function_name=None):
        # 解析插件提供者标识: "langgenius/github/github"
        self.plugin_provider = f"{node_data.provider_id}/{node_data.provider_name}"
        self._tool_client = ToolClient()  # 插件客户端
        self._credentials: dict | None = None
        super().__init__(node_data, state, runtime, function_name)
    
    @classmethod
    @override
    def get_provider_type(cls) -> ToolType:
        return ToolType.PLUGIN
    
    @override
    async def load_function_info(self) -> FunctionInfo:
        """从插件加载工具元信息"""
        # 1. 获取插件提供者信息
        provider_entity = await self._tool_client.fetch_tool_provider(
            tenant_id=self.tenant_id,
            provider=self.plugin_provider,
        )
        
        # 2. 提取工具参数定义
        return await self._load_plugin_tool(provider_entity, self.node_data.tool_name)
    
    @override
    async def invoke(self, parameters: dict[str, Any]) -> ToolResponse:
        """执行插件工具调用"""
        return await self._call_tool_function(parameters)
    
    async def _call_tool_function(self, parameters: dict) -> ToolResponse:
        """调用插件工具"""
        credentials = await self._get_credentials()
        
        # 流式调用插件
        chunks = []
        async for chunk in self._tool_client.invoke(
            tenant_id=self.tenant_id,
            user_id=self.runtime.context.user_id,
            tool_provider=self.plugin_provider,
            tool_name=self.node_data.tool_name,
            credentials=credentials,
            tool_parameters=parameters,
        ):
            chunks.append(chunk)
        
        # 聚合结果
        return self._aggregate_response(chunks)
```

### 2.3 ToolFactory (工具工厂)

**位置**: `extended/agno/tools/factory.py`

```python
class ToolFactory:
    """根据 provider_type 创建对应的工具实例"""
    
    @staticmethod
    def create_tool(
        node_data: ToolNodeData,
        state: GraphRuntimeState,
        runtime: "Runtime[GraphContext]",
        function_name: str | None = None,
    ) -> BaseTool:
        provider_type = node_data.provider_type
        
        # 从注册表获取工具类
        tool_class = tool_registry.get_tool(ToolType(provider_type))
        
        return tool_class(
            node_data=node_data,
            state=state,
            runtime=runtime,
            function_name=function_name,
        )
```

### 2.4 ToolRegistry (工具注册表)

**位置**: `extended/agno/tools/registry.py`

```python
class ToolRegistry:
    """工具类型注册表"""
    
    def __init__(self):
        self._tools = {}
    
    def register(self, tool: type[BaseTool]):
        provider_type = tool.get_provider_type().value
        self._tools[provider_type] = tool
    
    def get_tool(self, provider_type: ToolType) -> type[BaseTool]:
        return self._tools[provider_type.value]


# 全局注册表实例
tool_registry = ToolRegistry()

# 注册所有工具类型
tool_registry.register(PluginTools)    # 插件工具
tool_registry.register(CustomTools)    # 自定义工具
tool_registry.register(MCPTools)       # MCP 工具
tool_registry.register(WorkflowTools)  # 工作流工具
tool_registry.register(GraphSearchTools)  # 图谱搜索工具
```

## 3. Agent 集成

### 3.1 AgentNode 创建工具

**位置**: `alon/components/workflow/nodes/agent/agent_node.py`

```python
class AgentNode(BaseNode):
    """智能体节点 - 使用 Agno Agent 执行任务"""
    
    async def astream(self, execution_id, execution_index):
        from agno.agent.agent import Agent
        from extended.agno.models.alon.alon import Alon
        
        # 1. 创建模型实例
        alon_model = Alon(
            id=self.node_data.model.name,
            tenant_id=self.runtime.context.tenant_id,
            user=self.runtime.context.user_id,
            provider=self.node_data.model.provider,
            parameters=self.node_data.model.completion_params,
        )
        
        # 2. 动态创建工具列表
        tools = await self._create_tools(variable_pool)
        
        # 3. 创建 Agent
        agent = Agent(
            model=alon_model,
            instructions=instructions,
            tools=tools,                    # 传入插件工具
            tool_call_limit=self.node_data.tool_call_limit,
            stream_events=True,
            session_id=session_id,
            user_id=user_id,
        )
        
        # 4. 运行 Agent
        async for event in agent.arun(query_message):
            # 处理流式事件
            yield self._convert_event(event)
    
    async def _create_tools(self, variable_pool: VariablePool) -> list:
        """根据配置动态创建工具实例"""
        tools = []
        
        for tool_selector in self.node_data.tools:
            if not tool_selector.enabled:
                continue
            
            # 创建工具管理器
            tool_manager = ToolManager(
                state=self.state,
                runtime=self.runtime,
                node_data=tool_selector.to_tool_node_data(),
            )
            
            # 创建工具实例
            tool_instance = await tool_manager.create_tool_instance(
                variable_pool=variable_pool,
                function_name=f"tool_{i}",
            )
            
            tools.append(tool_instance)
        
        return tools
```

### 3.2 Agent 使用插件工具示例

```python
# 用户在工作流编辑器中配置 Agent 节点
agent_node = AgentNode(
    node_data=AgentNodeData(
        model={"name": "qwen-turbo", "provider": "tongyi"},
        instructions="你是一个助手，使用可用工具回答问题",
        tools=[
            # 插件工具配置
            {
                "provider_type": "plugin",
                "provider_id": "langgenius/github",
                "provider_name": "github",
                "tool_name": "github_repository_readme",
                "enabled": True,
            },
            {
                "provider_type": "plugin", 
                "provider_id": "langgenius/web_search",
                "provider_name": "web_search",
                "tool_name": "search",
                "enabled": True,
            }
        ],
        tool_call_limit=5,
    )
)

# Agent 运行时自动调用插件
# 用户问题: "帮我查看 higress-group/plugin-server 项目的 README"
# 
# Agent 决策:
# 1. 识别需要使用 github_repository_readme 工具
# 2. 调用 PluginTools.invoke({"owner": "higress-group", "repo": "plugin-server"})
# 3. PluginTools → ToolClient → TenantPluginManager → 插件子进程
# 4. 返回 README 内容给 Agent
# 5. Agent 基于内容回答用户
```

## 4. ToolNode (独立工具节点)

**位置**: `alon/components/workflow/nodes/tool/tool_node.py`

工作流中的独立工具调用节点：

```python
class ToolNode(BaseNode):
    """工具节点 - 直接调用工具"""
    
    async def astream(self, execution_id, execution_index):
        # 创建工具管理器
        tool_manager = ToolManager(
            state=self.state,
            runtime=self.runtime,
            node_data=self.node_data,
        )
        
        # 创建工具实例
        tool_instance = await tool_manager.create_tool_instance(
            variable_pool=self.state.variable_pool
        )
        
        # 执行工具调用
        result = await tool_instance.invoke(tool_instance.parameters)
        
        # 返回结果
        yield NodeRunResult(
            status=WorkflowNodeExecutionStatus.SUCCEEDED,
            outputs={"result": result.text},
        )
```

## 5. ToolClient (插件客户端)

**位置**: `alon/components/plugin/client/tool_client.py`

```python
class ToolClient(BasePluginClient):
    """工具客户端 - 提供插件工具调用接口"""
    
    async def fetch_tool_providers(
        self, tenant_id: str
    ) -> list[PluginToolProviderEntity]:
        """获取租户已安装的所有插件工具提供者"""
        plugin_manager = await self._get_plugin_manager(tenant_id)
        
        providers = []
        for plugin_name, plugin_info in plugin_manager.plugins.items():
            for config in plugin_info.config.tools_configuration or []:
                providers.append(
                    PluginToolProviderEntity(
                        provider=config.identity.name,
                        plugin_id=plugin_name,
                        declaration=ToolProviderEntityWithPlugin(...),
                    )
                )
        return providers
    
    async def invoke(
        self,
        tenant_id: str,
        user_id: str,
        tool_provider: str,
        tool_name: str,
        credentials: dict[str, Any],
        tool_parameters: dict[str, Any],
    ) -> AsyncGenerator[ToolInvokeMessage, None]:
        """调用插件工具（流式返回）"""
        
        # 解析提供者标识
        provider_id = GenericProviderID(tool_provider)
        plugin_id = f"{provider_id.organization}/{provider_id.plugin_name}"
        
        # 获取插件管理器
        plugin_manager = await self._get_plugin_manager(tenant_id)
        
        # 构建调用请求
        invoke_request = {
            "action": "invoke_tool",
            "provider": provider_id.provider_name,
            "tool": tool_name,
            "credentials": credentials,
            "tool_parameters": tool_parameters,
        }
        
        # 流式调用插件
        async for chunk in plugin_manager.invoke_plugin_stream(
            plugin_id, invoke_request, timeout=60
        ):
            yield ToolInvokeMessage(**chunk)
```

## 6. 单元测试示例

### 6.1 ToolClient 测试

**位置**: `tests/unit/components/plugin/test_tool_client.py`

```python
import pytest
from alon.components.plugin.client.tool_client import ToolClient
from alon_plugin.sdk.entities.tool import ToolInvokeMessage


class TestToolClient:
    """ToolClient 单元测试"""
    
    @pytest.fixture
    def tool_client(self) -> ToolClient:
        return ToolClient()
    
    @pytest.fixture
    def tenant_id(self) -> str:
        return "00000000000000000000000000000000"
    
    @pytest.fixture
    def github_provider(self) -> str:
        return "langgenius/github/github"
    
    @pytest.mark.asyncio
    async def test_fetch_tool_providers(self, tool_client, tenant_id):
        """测试获取工具提供者列表"""
        providers = await tool_client.fetch_tool_providers(tenant_id)
        
        assert isinstance(providers, list)
        assert len(providers) > 0
        
        github_provider = next(
            (p for p in providers if p.provider == "github"), 
            None
        )
        assert github_provider is not None
    
    @pytest.mark.asyncio
    async def test_invoke(self, tool_client, tenant_id, github_provider):
        """测试调用插件工具"""
        credentials = {"access_tokens": "valid_token", "api_version": "2022-11-28"}
        tool_parameters = {"owner": "higress-group", "repo": "plugin-server"}
        
        chunks = []
        output_content = ""
        
        async for chunk in tool_client.invoke(
            tenant_id=tenant_id,
            user_id="test_user",
            tool_provider=github_provider,
            tool_name="github_repository_readme",
            credentials=credentials,
            tool_parameters=tool_parameters,
        ):
            chunks.append(chunk)
            if chunk.type == ToolInvokeMessage.MessageType.TEXT:
                output_content += chunk.message.text
        
        assert len(chunks) > 0
        assert "higress" in output_content.lower()
    
    @pytest.mark.asyncio
    async def test_validate_provider_credentials(
        self, tool_client, tenant_id, github_provider
    ):
        """测试凭证验证"""
        valid_credentials = {"access_tokens": "valid_token"}
        invalid_credentials = {"access_tokens": "invalid_token"}
        
        # 有效凭证
        result = await tool_client.validate_provider_credentials(
            tenant_id=tenant_id,
            user_id="test_user",
            provider=github_provider,
            credentials=valid_credentials,
        )
        assert result is True
        
        # 无效凭证
        result = await tool_client.validate_provider_credentials(
            tenant_id=tenant_id,
            user_id="test_user", 
            provider=github_provider,
            credentials=invalid_credentials,
        )
        assert result is False
```

### 6.2 ModelClient 测试

**位置**: `tests/unit/components/plugin/test_model_client.py`

```python
class TestModelClient:
    """ModelClient 单元测试 - 测试模型插件"""
    
    @pytest.fixture
    def model_client(self):
        return ModelClient()
    
    @pytest.mark.asyncio
    async def test_fetch_model_providers(self, model_client, tenant_id):
        """测试获取模型提供者列表"""
        providers = await model_client.fetch_model_providers(tenant_id)
        
        assert isinstance(providers, list)
        
        # 查找通义千问模型提供者
        tongyi_provider = next(
            (p for p in providers if p.plugin_id == "langgenius/tongyi"),
            None
        )
        assert tongyi_provider is not None
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(
        os.getenv("DASHSCOPE_API_KEY") is None,
        reason="DASHSCOPE_API_KEY 未设置"
    )
    async def test_validate_model_credentials(
        self, model_client, tenant_id, user_id, credentials
    ):
        """测试验证模型凭证"""
        result = await model_client.validate_model_credentials(
            tenant_id=tenant_id,
            user_id=user_id,
            plugin_id="langgenius/tongyi",
            provider="tongyi",
            model_type=ModelType.LLM,
            model="qwen-turbo",
            credentials=credentials,
        )
        assert result is True
```

### 6.3 Agno Agent 工具集成测试

**位置**: `tests/studies/agno/test_agno_1.py`

```python
from agno.agent import Agent
from agno.tools import Toolkit


class CalculatorToolkit(Toolkit):
    """自定义计算器工具集"""
    
    def __init__(self):
        super().__init__(name="calculator")
        self.register(self.add)
        self.register(self.multiply)
    
    def add(self, a: float, b: float) -> str:
        """计算两个数的和"""
        return str(a + b)
    
    def multiply(self, a: float, b: float) -> str:
        """计算两个数的乘积"""
        return str(a * b)


@pytest.mark.asyncio
async def test_agent_with_toolkit():
    """测试 Agent 使用工具"""
    
    agent = Agent(
        model=make_model(),
        role="数学计算助手",
        instructions="使用计算工具回答问题",
        tools=[CalculatorToolkit()],
        debug_mode=True,
    )
    
    await agent.aprint_response("计算 13.7 + 28.3 的结果", markdown=True)


@pytest.mark.asyncio
async def test_streaming():
    """测试 Agent 流式输出"""
    
    agent = Agent(
        model=make_model(),
        instructions="故事创作助手",
        stream=True,
        stream_events=True,
    )
    
    collected_content = ""
    
    async for event in agent.arun("写一个三行小故事"):
        if event.event == RunEvent.run_content:
            collected_content += event.content
        elif event.event == RunEvent.run_completed:
            print(f"Token 使用: {event.metrics.input_tokens}/{event.metrics.output_tokens}")
    
    assert collected_content
```

## 7. 数据流完整示例

### 7.1 Agent 调用插件工具的完整流程

```
用户问题: "查看 GitHub 仓库 higress-group/plugin-server 的 README"

┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. Agent 分析问题，决定调用 github_repository_readme 工具                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. Agno 调用 PluginTools._tool_function(owner="higress-group",              │
│                                         repo="plugin-server")               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. PluginTools.invoke() → ToolClient.invoke()                               │
│    • tenant_id: "xxx"                                                       │
│    • tool_provider: "langgenius/github/github"                              │
│    • tool_name: "github_repository_readme"                                  │
│    • credentials: {"access_tokens": "xxx"}                                  │
│    • tool_parameters: {"owner": "higress-group", "repo": "plugin-server"}   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. TenantPluginManager.invoke_plugin_stream()                               │
│    • 检查插件是否运行，懒启动                                                │
│    • 构建 JSON 请求消息                                                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ JSON over stdin
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. 插件子进程 - GithubPlugin                                                │
│    {                                                                        │
│      "session_id": "xxx",                                                   │
│      "event": "request",                                                    │
│      "data": {                                                              │
│        "action": "invoke_tool",                                             │
│        "provider": "github",                                                │
│        "tool": "github_repository_readme",                                  │
│        "tool_parameters": {"owner": "higress-group", "repo": "plugin-server"}│
│      }                                                                      │
│    }                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 调用 GitHub API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. 插件返回结果 (流式)                                                       │
│    {"event": "message", "type": "text", "message": {"text": "# Plugin..."}} │
│    {"event": "message", "type": "text", "message": {"text": "Server..."}}   │
│    {"event": "end"}                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ JSON over stdout
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 7. ToolClient 聚合结果 → ToolResponse                                        │
│    ToolResponse(                                                            │
│        success=True,                                                        │
│        text="# Plugin Server\n\nA high-performance...",                    │
│    )                                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 8. Agent 收到工具结果，生成最终回答                                          │
│    "根据查询结果，plugin-server 是一个高性能插件服务器项目..."               │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 8. 凭证管理

### 8.1 凭证获取流程

```python
class PluginTools(BaseTool):
    
    async def _get_credentials(self) -> dict[str, Any]:
        """获取插件凭证"""
        
        # 1. 检查是否需要授权
        if not self.need_authorization:
            return {}
        
        # 2. 检查节点是否指定了凭证
        node_config = self.node_data.config or {}
        chosen_credential = node_config.get("plugin_credential")
        
        if chosen_credential:
            # 使用指定的扩展凭证
            cred_id = chosen_credential.get("credential_id")
            record = await PluginCredential.one_by_id(session, cred_id)
            
            # 解密凭证
            return tool_store_service.decrypt_credentials(
                installation.tenant_id,
                record.credentials,
                credentials_schema,
            )
        
        # 3. 使用默认凭证 (from PluginInstallation.runtime_config)
        installation = await self._get_plugin_installation()
        return installation.runtime_config.get("credentials", {})
```

### 8.2 多凭证支持

```
┌─────────────────────────────────────────────────────────────────┐
│                      凭证层次结构                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PluginInstallation                                             │
│  ├── runtime_config.credentials  ← 默认凭证                     │
│  │                                                              │
│  PluginCredential (扩展凭证表)                                  │
│  ├── credential_1 (scope=global) ← 全局凭证 1                   │
│  ├── credential_2 (scope=global) ← 全局凭证 2                   │
│  └── credential_3 (scope=personal) ← 个人凭证 (预留)            │
│                                                                 │
│  节点配置选择:                                                  │
│  {                                                              │
│    "plugin_credential": {                                       │
│      "scope": "global",                                         │
│      "credential_id": "credential_2"                            │
│    }                                                            │
│  }                                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 9. 工具类型对比

| 类型 | 实现类 | 来源 | 特点 |
|------|--------|------|------|
| **PLUGIN** | `PluginTools` | 插件 ZIP 包 | 动态加载，支持多租户隔离 |
| **CUSTOM** | `CustomTools` | 数据库定义 | 用户自定义 HTTP/API 工具 |
| **MCP** | `MCPTools` | MCP 服务器 | Model Context Protocol 工具 |
| **WORKFLOW** | `WorkflowTools` | 工作流应用 | 工作流作为工具调用 |
| **GRAPH_SEARCH** | `GraphSearchTools` | GraphRAG | 图谱搜索工具 |

## 10. 最佳实践

### 10.1 工具开发

```python
# 插件工具开发最佳实践
class MyTool(Tool):
    """自定义工具"""
    
    def _invoke(
        self, 
        query: str,                    # 明确的参数定义
        options: dict | None = None    # 可选参数
    ) -> ToolInvokeMessage:
        """工具描述 - 清晰说明功能和返回值"""
        
        try:
            # 1. 参数验证
            if not query:
                return self.create_text_message("错误: query 参数不能为空")
            
            # 2. 执行核心逻辑
            result = self._execute(query, options or {})
            
            # 3. 返回结构化结果
            return self.create_json_message(result)
            
        except Exception as e:
            # 4. 错误处理
            return self.create_text_message(f"执行失败: {str(e)}")
```

### 10.2 Agent 配置

```python
# Agent 工具配置最佳实践
agent_config = {
    "model": {"name": "qwen-turbo", "provider": "tongyi"},
    "instructions": """
        你是一个智能助手。
        
        工具使用规则:
        1. 优先使用插件工具获取实时数据
        2. 对于代码相关的问题，使用代码执行工具
        3. 如果工具返回错误，尝试其他方式或告知用户
    """,
    "tools": [
        # 工具列表 - 按优先级排序
        {"provider_type": "plugin", "tool_name": "web_search", "enabled": True},
        {"provider_type": "plugin", "tool_name": "code_execute", "enabled": True},
    ],
    "tool_call_limit": 5,  # 限制工具调用次数，防止无限循环
}
```

### 10.3 测试覆盖

```python
# 测试最佳实践
@pytest.mark.asyncio
class TestPluginIntegration:
    """插件集成测试"""
    
    async def test_tool_invoke_success(self):
        """正常调用测试"""
        pass
    
    async def test_tool_invoke_invalid_credentials(self):
        """无效凭证测试"""
        pass
    
    async def test_tool_invoke_timeout(self):
        """超时测试"""
        pass
    
    async def test_tool_invoke_concurrent(self):
        """并发调用测试"""
        pass
```

## 11. 运行测试

```bash
# 运行插件工具客户端测试
uv run pytest packages/platform/tests/unit/components/plugin/test_tool_client.py -v

# 运行模型客户端测试
uv run pytest packages/platform/tests/unit/components/plugin/test_model_client.py -v

# 运行 Agno 集成示例
uv run pytest packages/platform/tests/studies/agno/test_agno_1.py -v -s

# 运行工作流工具测试
uv run pytest packages/platform/tests/components/workflow/tools/ -v

# 运行所有插件相关测试
uv run pytest packages/platform/tests/unit/components/plugin/ -v
```
