# Agent 工厂规范

## 新增需求

### 需求:系统提供 Agent 创建工厂

系统必须提供 `AgentFactory` 类，简化 LangChain Agent 和 LangGraph 的创建流程。

#### 场景:创建 AgentFactory 实例

- **当** 使用 `AlonChatModel` 实例创建 `AgentFactory`
- **那么** 工厂必须绑定到该模型实例

---

### 需求:系统支持创建 AgentExecutor

系统必须实现 `create_executor()` 方法，创建 LangChain AgentExecutor。

#### 场景:创建简单 AgentExecutor

- **当** 调用 `factory.create_executor(tools=[search_tool])`
- **那么** 系统必须返回配置正确的 `AgentExecutor` 实例

#### 场景:创建带 Memory 的 AgentExecutor

- **当** 调用 `factory.create_executor(tools=[...], memory=memory)`
- **那么** 返回的 `AgentExecutor` 必须配置指定的 Memory

#### 场景:使用 AgentExecutor 调用

- **当** 调用 `executor.invoke({"input": "你好"})`
- **那么** 系统必须返回包含 `output` 字段的字典

---

### 需求:系统支持创建 LangGraph

系统必须实现 `create_graph()` 方法，创建 LangGraph 工作流。

#### 场景:创建简单 LangGraph

- **当** 调用 `factory.create_graph(tools=[search_tool])`
- **那么** 系统必须返回编译好的 LangGraph `CompiledGraph` 实例

#### 场景:创建带 Checkpointer 的 LangGraph

- **当** 调用 `factory.create_graph(tools=[...], checkpointer=checkpointer)`
- **那么** 返回的 LangGraph 必须配置持久化检查点

#### 场景:使用 LangGraph 流式调用

- **当** 调用 `graph.astream_events({"messages": [...]}, version="v2")`
- **那么** 系统必须返回标准的事件流

---

### 需求:系统支持自定义 Prompt

Agent 工厂必须支持自定义 Prompt 模板。

#### 场景:使用自定义 Prompt

- **当** 调用 `factory.create_executor(tools=[...], prompt=custom_prompt)`
- **那么** 系统必须使用自定义 Prompt 创建 Agent

#### 场景:默认 Prompt

- **当** 未指定 Prompt 参数
- **那么** 系统必须使用默认的对话 Prompt 模板

---

### 需求:系统支持配置选项

Agent 工厂必须支持常见的配置选项。

#### 场景:配置 verbose 模式

- **当** 调用 `factory.create_executor(tools=[...], verbose=True)`
- **那么** AgentExecutor 必须启用详细日志输出

#### 场景:配置错误处理

- **当** 调用 `factory.create_executor(tools=[...], handle_parsing_errors=True)`
- **那么** Agent 必须在解析错误时继续执行而非失败
