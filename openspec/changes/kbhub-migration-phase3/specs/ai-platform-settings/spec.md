# 平台设置

## 场景

### 获取平台设置

- **Given** 用户已登录
- **When** 请求平台设置
- **Then** 返回切片参数（chunk_size/overlap）和六类模型配置

### 保存平台设置

- **Given** 用户是企业管理员
- **When** 保存平台设置（切片参数 + 模型配置）
- **Then** 保存到 ai.config_items（config_scope=tenant，config_key=kbhub_platform_settings），写入审计日志

### 切片参数校验

- **Given** 最大重合长度 >= 切片最大长度
- **When** 保存平台设置
- **Then** 拒绝保存，返回校验错误

### 模型配置使用模型选择组件

- **Given** 保存平台设置
- **When** 选择 LLM/Vision/Video 模型
- **Then** 保留或补齐 completion_params；Audio/Embedding/Rerank 不保存 completion_params

### 保存后影响范围

- **Given** 平台设置已保存
- **When** 后续新建文档切片或索引任务
- **Then** 新任务使用新配置；已有任务和历史快照不自动改写

### 多租户隔离

- **Given** 不同租户的平台设置
- **When** 查询/保存
- **Then** 仅操作当前租户数据
