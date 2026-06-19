"""
租户相关异常
"""


class TenantError(Exception):
    """租户异常基类"""

    def __init__(self, message: str = "租户错误"):
        self.message = message
        super().__init__(self.message)


class TenantNotFoundError(TenantError):
    """租户不存在"""

    def __init__(self, tenant_id: str | None = None):
        msg = f"租户不存在: {tenant_id}" if tenant_id else "租户不存在"
        super().__init__(msg)


class TenantInactiveError(TenantError):
    """租户已停用"""

    def __init__(self, tenant_id: str | None = None):
        msg = f"租户已停用: {tenant_id}" if tenant_id else "租户已停用"
        super().__init__(msg)


class TenantExpiredError(TenantError):
    """租户已过期"""

    def __init__(self, tenant_id: str | None = None):
        msg = f"租户已过期: {tenant_id}" if tenant_id else "租户已过期"
        super().__init__(msg)


class TenantAccessDeniedError(TenantError):
    """无权访问租户"""

    def __init__(self, tenant_id: str | None = None):
        msg = f"无权访问该租户: {tenant_id}" if tenant_id else "无权访问该租户"
        super().__init__(msg)


class TenantNotSetError(TenantError):
    """租户上下文未设置"""

    def __init__(self):
        super().__init__("租户上下文未设置")


class TenantResolveError(TenantError):
    """租户解析失败"""

    def __init__(self, message: str = "无法解析租户标识"):
        super().__init__(message)


class TenantAdminNotFoundError(TenantError):
    """租户管理员不存在"""

    def __init__(self):
        super().__init__("租户管理员不存在")


class TenantAdminAuthError(TenantError):
    """租户管理员认证失败"""

    def __init__(self, message: str = "管理员认证失败"):
        super().__init__(message)
