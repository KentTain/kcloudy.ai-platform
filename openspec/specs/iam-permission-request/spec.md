# 权限申请审批规范

## Purpose

定义 IAM 模块的权限申请与审批能力，支持用户提交权限申请、管理员审批，审批通过后通过 inner 接口回调业务模块落地授权，审批结果以站内信通知申请人，并实现工作台查询与多租户隔离。

## Requirements

### Requirement: 权限申请审批

权限申请审批 SHALL 支持提交权限申请、审批通过后回调业务模块 inner 接口落地授权、审批拒绝、审批结果通知申请人、工作台查询与多租户隔离。

#### 场景：提交权限申请

- **Given** 用户 U1 不持有资源 R1 的权限，且资源 R1 所属模块支持权限申请
- **When** 用户 U1 调用 `submit_permission_request(type, resource_id, reason)`，type 为 library_join / knowledge_base_join / library_resource / library_role / knowledge_base_role 中的一种
- **Then** 系统创建一条权限申请记录，状态为 pending，记录申请人、申请类型、资源 ID、申请原因和创建时间；同时触发审批流程，通知审批人

#### 场景：审批通过后回调业务模块 inner 接口落地授权

- **Given** 存在一条状态为 pending 的权限申请 PR1，类型为 knowledge_base_join，资源为知识库 KB1
- **When** 审批人调用 `approve_request(PR1.id)`
- **Then** 权限申请状态更新为 approved；系统回调知识库模块的 inner 接口（如 `kb_inner.grant_access`）落地授权，将用户 U1 加入知识库 KB1 的成员列表；授权生效后触发审计日志记录

#### 场景：审批拒绝后不创建授权

- **Given** 存在一条状态为 pending 的权限申请 PR1
- **When** 审批人调用 `reject_request(PR1.id, reject_reason="不符合申请条件")`
- **Then** 权限申请状态更新为 rejected，记录拒绝原因；系统不调用任何业务模块的授权接口，不创建任何授权记录

#### 场景：审批结果通知申请人

- **Given** 用户 U1 提交的权限申请 PR1已被审批人处理
- **When** 审批操作完成（通过或拒绝）
- **Then** 系统向申请人 U1 发送站内信通知，内容包含申请类型、资源名称、审批结果（通过/拒绝）及拒绝原因（若拒绝）

#### 场景：工作台查询我的申请/待我审批

- **Given** 用户 U1 提交了 3 条权限申请，且 U1 作为审批人有 2 条待审批申请
- **When** 用户 U1 调用 `list_my_requests(page, page_size)` 和 `list_pending_approvals(page, page_size)`
- **Then** `list_my_requests` 返回 U1 提交的 3 条申请记录，按创建时间倒序排列；`list_pending_approvals` 返回待 U1 审批的 2 条申请记录，按创建时间倒序排列；均支持分页

#### 场景：多租户隔离

- **Given** 租户 T1 的用户 U1 提交权限申请 PR1，租户 T2 的用户 U2 提交权限申请 PR2
- **When** 租户 T1 的审批人查询待审批列表
- **Then** 仅返回 T1 下的权限申请 PR1，不可见 T2 下的 PR2；审批通过后回调仅影响本租户内的授权，不跨租户创建授权记录

