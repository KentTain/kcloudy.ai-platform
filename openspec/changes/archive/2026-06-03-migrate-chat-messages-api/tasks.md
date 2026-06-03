# LLM 对话接口迁移任务清单

## 1. Schema 定义

- [x] 1.1 创建 `ai/schemas/__init__.py`
- [x] 1.2 创建 `ai/schemas/completion.py`
- [x] 1.3 定义 `ModelConfig` Schema（name、provider、completion_params）
- [x] 1.4 定义 `SearchConfig` Schema（enabled、source）
- [x] 1.5 定义 `FileItem` Schema（type、url、name）
- [x] 1.6 定义 `LLMChatCompletion` 请求 Schema
- [x] 1.7 定义 SSE 事件 Schema（SSEMessageEvent、SSEFinishEvent、SSEErrorEvent、SSESearchEvent）

## 2. 控制器基础设施

- [x] 2.1 创建 `ai/controllers/__init__.py`
- [x] 2.2 创建 `ai/controllers/v1/__init__.py`
- [x] 2.3 创建 `ai/controllers/v1/chat/__init__.py`

## 3. 对话接口实现

- [x] 3.1 创建 `ai/controllers/v1/chat/llm.py`
- [x] 3.2 定义路由器（prefix="/chat-messages"，tags=["LLM对话"]）
- [x] 3.3 实现 `chat_messages()` 方法签名
- [x] 3.4 实现会话创建逻辑（无 conversation_id 时创建新会话）
- [x] 3.5 实现会话恢复逻辑（验证 conversation_id 和租户归属）
- [x] 3.6 创建 AlonChatModel 实例
- [x] 3.7 创建 LangGraph Agent 或 AgentExecutor
- [x] 3.8 实现 SSE 生成器函数
- [x] 3.9 处理 `on_chat_model_stream` 事件生成 message 事件
- [x] 3.10 处理 `on_tool_start` 事件生成 search_keywords 事件
- [x] 3.11 处理对话完成生成 finish 事件
- [x] 3.12 实现错误处理和 error 事件生成
- [x] 3.13 实现消息保存逻辑（保存用户问题和助手回复）
- [x] 3.14 实现 token 统计记录

## 4. 任务停止接口实现

- [x] 4.1 实现 `stop_chat_messages()` 方法签名
- [x] 4.2 验证会话存在和租户归属
- [x] 4.3 获取活跃任务 ID
- [x] 4.4 调用 `stop_task_by_id()` 发送停止信号
- [x] 4.5 更新消息状态为 `stopped`
- [x] 4.6 返回停止成功响应

## 5. 路由注册

- [x] 5.1 更新 `ai/module.py` 添加路由注册
- [x] 5.2 配置路由前缀为 `/api/v1`
- [x] 5.3 配置认证依赖（DependAuth）

## 6. 配置集成

- [x] 6.1 在 `framework/configs/settings.py` 添加应用配置
- [x] 6.2 添加 `default_app_id` 和 `default_app_name` 配置
- [x] 6.3 验证配置读取正确

## 7. 测试

- [x] 7.1 编写 Schema 校验测试
- [x] 7.2 编写会话创建测试
- [x] 7.3 编写会话恢复测试
- [x] 7.4 编写流式响应测试
- [x] 7.5 编写 SSE 事件格式测试
- [x] 7.6 编写任务停止测试
- [x] 7.7 编写错误处理测试
- [x] 7.8 编写多租户隔离测试

## 8. 集成验证

- [x] 8.1 启动服务验证路由注册
- [x] 8.2 使用 curl 测试流式对话接口
- [x] 8.3 测试完整对话流程
- [x] 8.4 测试任务停止流程
- [x] 8.5 验证数据库记录正确

## 9. 文档与收尾

- [x] 9.1 更新 `ai/CLAUDE.md` 模块文档
- [x] 9.2 编写 API 使用示例
- [x] 9.3 代码审查和清理
- [x] 9.4 运行完整测试套件验证

## 依赖说明

本变更依赖以下变更完成后方可实施：

- `migrate-model-component`：提供 `LLMService`
- `migrate-langchain-bridge`：提供 `AlonChatModel` 和 `AgentFactory`
- `migrate-conversation-persistence`：提供 `Conversation`、`Message` 和 `memory_task`
