# 审计日志统一写入辅助规范

## Purpose

定义 framework 提供的审计日志统一写入辅助接口，将业务模块的操作记录写入 iam.audit_logs 表，支持必填字段校验、多租户隔离与变更前后快照记录，确保跨模块审计一致。

## Requirements

### Requirement: 审计日志统一写入辅助

审计写入辅助 SHALL 提供统一审计写入接口将记录写入 iam.audit_logs，支持必填字段校验、多租户隔离与变更前后快照记录。

#### 场景：业务模块调用写入辅助，数据写入 iam.audit_logs

- **Given** 业务模块（如知识库模块）完成了一次资源删除操作
- **When** 业务模块调用审计写入辅助 `write_audit(entry)`，entry 包含 business_domain="knowledge_base"、operation_type="delete"、resource_type="document"、resource_id="doc-001"、operator_by="user-123"
- **Then** 写入辅助将 entry 写入 `iam.audit_logs` 表，记录包含传入的所有字段及自动填充的 timestamp、request_id 等系统字段

#### 场景：必填字段校验

- **Given** 业务模块准备调用审计写入辅助
- **When** 调用 `write_audit(entry)`，entry 缺少 business_domain、operation_type、resource_type 或 operator_by 中的任意一个
- **Then** 写入辅助拒绝写入并抛出校验异常，异常信息明确指出缺失的必填字段名称，`iam.audit_logs` 表无新增记录

#### 场景：多租户隔离

- **Given** 当前请求上下文中租户标识为 T1
- **When** 业务模块调用 `write_audit(entry)`，entry 未显式传入 tenant_id
- **Then** 写入辅助自动从请求上下文注入 tenant_id=T1，写入 `iam.audit_logs` 的记录 tenant_id 为 T1，确保不同租户的审计日志隔离存储

#### 场景：before_data/after_data 正确记录变更

- **Given** 业务模块对资源 R 执行更新操作，更新前数据为 `{name: "旧名称", status: "draft"}`，更新后数据为 `{name: "新名称", status: "published"}`
- **When** 业务模块调用 `write_audit(entry)`，entry.before_data 为更新前快照，entry.after_data 为更新后快照
- **Then** `iam.audit_logs` 中该条记录的 before_data 准确记录 `{name: "旧名称", status: "draft"}`，after_data 准确记录 `{name: "新名称", status: "published"}`

