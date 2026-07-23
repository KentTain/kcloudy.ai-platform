# 工具库

## 场景

### Swagger 导入

- **Given** 用户具备 `ai:tool:import` 权限
- **When** 提交 Swagger URL 或定义内容
- **Then** 校验 OpenAPI（openapi-spec-validator）→ 解析 $ref（prance）→ 创建 Tool/ToolAuth/ToolFunction/ToolParameter → 记录 ToolImportRecord

### MCP 导入

- **Given** 用户具备 `ai:tool:import` 权限
- **When** 提交 MCP Server 连接配置（SSE/Streamable HTTP）
- **Then** 通过官方 SDK 调用 tools/list → 创建 Tool/ToolAuth/ToolFunction/ToolParameter → 记录 ToolImportRecord

### 工具 code 唯一

- **Given** 同一租户内已有 code="user-center" 的工具
- **When** 再次导入 code="user-center" 的工具
- **Then** 拒绝导入，返回 code 冲突错误

### 重导入保留 Tool/ToolAuth

- **Given** 工具已存在
- **When** 触发重导入
- **Then** 保留 Tool 和 ToolAuth，删除 ToolFunction/ToolParameter 后重新创建，恢复人工维护字段（ai_description/example/sort/enabled）

### 重导入失败回滚

- **Given** 重导入过程中来源校验或解析失败
- **When** 失败发生
- **Then** 保留原 Function/Parameter，新增失败 ToolImportRecord

### 工具逻辑删除

- **Given** 工具已发布
- **When** 删除工具
- **Then** 逻辑删除（deleted_at），相同 code 可重新导入

### Connection Test

- **Given** 用户是超管，工具未删除
- **When** 触发连接测试
- **Then** Runtime 按 protocol 分发（HttpExecutor/McpExecutor），返回成功/失败+耗时

### Function Test

- **Given** 用户是超管，工具和函数未删除
- **When** 触发函数测试（传入 arguments）
- **Then** Runtime 执行函数，返回请求摘要（脱敏）+响应+耗时

### 敏感信息脱敏

- **Given** 工具认证配置含 token/api_key/password
- **When** 查询工具详情/列表/测试响应
- **Then** 认证配置中敏感值替换为 `******`

### 多租户隔离

- **Given** 不同租户的工具数据
- **When** 查询工具
- **Then** 仅返回当前租户数据
