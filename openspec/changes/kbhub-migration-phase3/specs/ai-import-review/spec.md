# 入库审核

## 场景

### 提交入库申请

- **Given** 用户对源文件具备 `submit_to_kb` 权限，且具备目标知识库提交角色
- **When** 提交入库申请（源文件ID、目标知识库ID、标签等）
- **Then** 创建 import_requests + import_request_items，状态为 pending

### 入库申请通知审核员

- **Given** 入库申请已创建
- **When** 系统处理申请
- **Then** 通过 iam 站内信通知知识库审核员（permission_request_pending）

### 审核通过

- **Given** 审核员具备 `review_import` 权限，申请状态为 pending
- **When** 审核通过
- **Then** 生成知识库文档引用（knowledge_base_documents），申请状态为 approved，通知申请人

### 审核拒绝

- **Given** 审核员具备 `review_import` 权限，申请状态为 pending
- **When** 审核拒绝
- **Then** 申请状态为 rejected，不创建文档引用，通知申请人

### 审核员权限校验

- **Given** 审核员通过站内信打开审核详情
- **When** 执行审批操作
- **Then** 后端重新校验 `review_import` 权限和申请状态，消息可见≠可操作

### 源文件权限不放大

- **Given** 审核员无源文件目录浏览权限
- **When** 处理审核
- **Then** 审核员可在审核上下文审阅本次申请材料，但不获得源文件目录浏览或下载权限

### 多租户隔离

- **Given** 不同租户的入库申请
- **When** 查询申请
- **Then** 仅返回当前租户数据
