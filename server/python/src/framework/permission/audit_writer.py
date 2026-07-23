"""
审计日志统一写入辅助

延迟导入 iam.models.AuditLog 避免循环依赖（framework 禁止直接依赖业务模块）。
使用 framework.common.ctx 获取当前请求上下文（租户ID、用户ID、权限编码）。
"""

from datetime import datetime, timezone

from framework.common.ctx import get_tenant_id, get_user_id, get_permission_code


async def write_audit(
    *,
    session,
    business_domain: str,
    operation_type: str,
    resource_type: str,
    resource_name: str,
    resource_id: str | None = None,
    business_domain_id: str | None = None,
    before_data: dict | None = None,
    after_data: dict | None = None,
    detail: dict | None = None,
) -> None:
    """
    写入审计日志。

    延迟导入 iam.models.AuditLog，在函数内 import 以避免 framework -> iam 循环依赖。

    Args:
        session: 数据库会话（AsyncSession）
        business_domain: 业务域（模块名称），必填
        operation_type: 操作类型，必填
        resource_type: 资源类型，必填
        resource_name: 主操作对象名称，必填
        resource_id: 主操作对象ID
        business_domain_id: 业务域ID
        before_data: 操作前数据
        after_data: 操作后数据
        detail: 操作详情

    Raises:
        ValueError: 缺少必填字段
    """
    # 校验必填字段
    if not business_domain:
        raise ValueError("business_domain 不能为空")
    if not operation_type:
        raise ValueError("operation_type 不能为空")
    if not resource_type:
        raise ValueError("resource_type 不能为空")

    # 延迟导入：避免 framework -> iam 循环依赖
    from iam.models.audit_log import AuditLog

    # 从请求上下文获取租户、用户、权限编码
    tenant_id = get_tenant_id() or ""
    operator_by = get_user_id() or ""
    permission_code = get_permission_code()

    audit_log = AuditLog(
        tenant_id=tenant_id,
        business_domain=business_domain,
        business_domain_id=business_domain_id,
        permission_code=permission_code,
        operator_by=operator_by,
        operator_name=operator_by,  # 使用 user_id 作为默认 operator_name
        operated_at=datetime.now(timezone.utc),
        operation_type=operation_type,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        before_data=before_data,
        after_data=after_data,
        detail=detail,
    )

    session.add(audit_log)
