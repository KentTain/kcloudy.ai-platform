# 知识库管理

## 场景

### 创建知识库

- **Given** 用户具备 `ai:knowledge_base:write` 权限
- **When** 提交知识库创建请求（名称、描述、图标）
- **Then** 创建知识库记录，创建者为 owner，返回知识库详情

### 知识库列表查询

- **Given** 用户已登录
- **When** 请求知识库列表（分页、关键词筛选）
- **Then** 返回用户有权访问的知识库列表

### 知识库成员管理

- **Given** 用户是知识库 owner 或 admin
- **When** 添加/移除成员、分配角色（owner/admin/manager/reviewer/query_user）
- **Then** 更新 knowledge_base_members，写入审计日志

### 知识库文档引用

- **Given** 文档已通过入库审核
- **When** 生成知识库文档引用
- **Then** 创建 knowledge_base_documents 记录，引用状态为 active

### 检索测试

- **Given** 用户是知识库成员
- **When** 提交检索测试请求（query、知识库范围）
- **Then** 返回检索结果，仅包含用户有权访问的文档片段

### 知识库问答

- **Given** 用户具备知识库 `query` 权限
- **When** 发起问答
- **Then** 仅检索用户有权访问的知识库文档，无权限片段不进入 LLM prompt

### 知识库问答引用源文件权限校验

- **Given** 问答返回引用片段
- **When** 用户点击引用打开源文件
- **Then** 实时回查 document inner 接口校验源文件 preview/download 权限

### 知识库配置

- **Given** 用户是知识库 owner 或 admin
- **When** 修改知识库配置（切片参数、模型覆盖等）
- **Then** 保存配置，写入审计日志

### 多租户隔离

- **Given** 不同租户的知识库数据
- **When** 查询知识库
- **Then** 仅返回当前租户数据，跨租户不可访问
