# 整体集成验收

## 场景

### document→ai 文档引用链路端到端

- **Given** 文档库中有文件，用户对文件有 `submit_to_kb` 权限
- **When** 提交入库 → 审核通过 → 查看知识库文档列表 → 发起问答
- **Then** 文档出现在知识库文档列表，问答可检索到该文档片段

### 三层权限端到端验证

- **Given** 用户有 IAM 功能权限但无文档库资源权限
- **When** 访问文档库详情页
- **Then** 菜单可见（第1层通过），但资源不可访问（第2层拒绝），Policy未命中（第3层无影响）

### 权限申请审批落地

- **Given** 用户提交 library_join 权限申请
- **When** 文档库管理员审批通过
- **Then** iam 通过 inner 接口回调 document，创建 library_members 记录，用户获得文档库成员身份

### 审计日志跨模块一致

- **Given** 在 document 模块执行文件上传，在 ai 模块执行知识库问答
- **When** 查询 iam 审计日志
- **Then** 两个模块的操作均出现在 iam.audit_logs，business_domain 分别为 document 和 ai

### 站内信跳转回源校验

- **Given** 用户收到入库审核站内信
- **When** 点击站内信跳转到审核详情
- **Then** 后端重新校验 `review_import` 权限和申请状态；无权限时拒绝操作

### 知识库不放大源文档权限

- **Given** 用户是知识库成员但对源文件无 view 权限
- **When** 发起知识库问答
- **Then** 该源文件片段不进入检索上下文和 LLM prompt

### 企业 Policy 跨模块生效

- **Given** 企业 Policy 设置某密级文档禁止问答
- **When** 用户在知识库问答
- **Then** Policy 拒绝优先，该文档片段不进入检索结果
