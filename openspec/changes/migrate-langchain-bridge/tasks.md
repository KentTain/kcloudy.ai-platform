# LangChain 桥接层迁移任务清单

## 1. 基础设施搭建

- [ ] 1.1 创建 `extended/langchain/` 目录结构
- [ ] 1.2 创建 `extended/langchain/__init__.py`
- [ ] 1.3 创建 `extended/langchain/models/__init__.py`
- [ ] 1.4 创建 `extended/langchain/agents/__init__.py`

## 2. 消息适配器实现

- [ ] 2.1 创建 `models/message_adapter.py` 文件
- [ ] 2.2 实现 `to_platform_message()` 单消息转换方法
- [ ] 2.3 实现 `to_platform_messages()` 批量转换方法
- [ ] 2.4 实现 `to_langchain_message()` 反向转换方法
- [ ] 2.5 实现 HumanMessage/AIMessage/SystemMessage 类型映射
- [ ] 2.6 定义 `UnsupportedMessageTypeError` 异常
- [ ] 2.7 编写消息适配器单元测试

## 3. AlonChatModel 实现

- [ ] 3.1 创建 `models/alon_chat.py` 文件
- [ ] 3.2 定义 `AlonChatModel` 类继承 `BaseChatModel`
- [ ] 3.3 定义 Pydantic 字段：model、provider、tenant_id、model_parameters
- [ ] 3.4 实现 `_llm_type` 属性返回 `"alon-chat-model"`
- [ ] 3.5 实现 `_identifying_params` 属性返回模型标识
- [ ] 3.6 实现 `_agenerate()` 非流式调用方法
- [ ] 3.7 实现 `_astream()` 流式调用方法
- [ ] 3.8 实现 `LLMResult` 到 `ChatResult` 的转换
- [ ] 3.9 实现 `LLMResultChunk` 到 `ChatGenerationChunk` 的转换
- [ ] 3.10 实现异常捕获和转换逻辑
- [ ] 3.11 编写 AlonChatModel 单元测试

## 4. Agent 工厂实现

- [ ] 4.1 创建 `agents/agent_factory.py` 文件
- [ ] 4.2 实现 `AgentFactory` 类初始化方法
- [ ] 4.3 实现 `create_executor()` 方法创建 AgentExecutor
- [ ] 4.4 实现 `create_graph()` 方法创建 LangGraph（可选）
- [ ] 4.5 实现默认 Prompt 模板生成
- [ ] 4.6 支持自定义 Prompt 参数
- [ ] 4.7 支持 Memory 配置（ConversationBufferMemory）
- [ ] 4.8 支持 verbose 和 handle_parsing_errors 配置
- [ ] 4.9 编写 Agent 工厂单元测试

## 5. 集成测试

- [ ] 5.1 编写 AlonChatModel 非流式调用集成测试
- [ ] 5.2 编写 AlonChatModel 流式调用集成测试
- [ ] 5.3 编写 AgentExecutor 集成测试
- [ ] 5.4 编写 LangGraph 集成测试（可选）
- [ ] 5.5 编写多租户隔离测试

## 6. 文档与收尾

- [ ] 6.1 创建 `extended/langchain/CLAUDE.md` 模块文档
- [ ] 6.2 创建 `extended/langchain/MIGRATION.md`，记录目录/文件级差异（哪些从 Alon 迁移了、哪些未迁移）
- [ ] 6.3 编写使用示例代码
- [ ] 6.4 代码审查和清理
- [ ] 6.5 运行完整测试套件验证

## 依赖说明

本变更依赖以下变更完成后方可实施：

- `migrate-model-component`：提供 `LLMService` 服务
