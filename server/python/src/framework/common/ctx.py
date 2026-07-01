"""请求上下文管理

提供请求级别的上下文存储，支持存储当前用户、租户等信息。
"""

from contextvars import ContextVar
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

# 使用 contextvars 实现协程安全的上下文
_context_var: ContextVar["Context | None"] = ContextVar("app_context", default=None)


@dataclass
class Context:
    """请求上下文"""

    # 用户信息
    user_id: str | None = None
    user_name: str | None = None
    session_id: str | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)

    # 租户信息
    tenant_id: str | None = None
    tenant_name: str | None = None
    tenant_code: str | None = None

    # 权限信息
    permission_code: str | None = None
    """当前操作的权限编码"""

    # 其他信息
    workspace_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        """设置额外属性"""
        self.extra[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取额外属性"""
        return self.extra.get(key, default)

    def copy(self) -> "Context":
        """创建上下文副本"""
        return Context(
            user_id=self.user_id,
            user_name=self.user_name,
            session_id=self.session_id,
            roles=list(self.roles),
            permissions=list(self.permissions),
            tenant_id=self.tenant_id,
            tenant_name=self.tenant_name,
            tenant_code=self.tenant_code,
            permission_code=self.permission_code,
            workspace_id=self.workspace_id,
            extra=deepcopy(self.extra),
        )


def get_context() -> Context:
    """
    获取当前上下文

    Returns:
        Context: 当前上下文，如果不存在则创建新的空上下文
    """
    ctx = _context_var.get()
    if ctx is None:
        ctx = Context()
        _context_var.set(ctx)
    return ctx


def set_context(ctx: Context) -> None:
    """
    设置当前上下文

    Args:
        ctx: 上下文实例
    """
    _context_var.set(ctx)


def _update_context(modifier: callable) -> None:
    """
    更新上下文（创建副本以确保协程隔离）

    Args:
        modifier: 修改上下文的函数
    """
    ctx = get_context()
    new_ctx = ctx.copy()
    modifier(new_ctx)
    _context_var.set(new_ctx)


def clear_context() -> None:
    """清理当前上下文"""
    _context_var.set(None)


def set_user(
    user_id: str,
    user_name: str | None = None,
    tenant_id: str | None = None,
    workspace_id: str | None = None,
    roles: list[str] | None = None,
    permissions: list[str] | None = None,
) -> None:
    """
    设置当前用户信息

    Args:
        user_id: 用户 ID
        user_name: 用户名
        tenant_id: 租户 ID
        workspace_id: 工作空间 ID
        roles: 角色列表
        permissions: 权限列表
    """

    def modifier(ctx: Context) -> None:
        ctx.user_id = user_id
        ctx.user_name = user_name
        ctx.tenant_id = tenant_id
        ctx.workspace_id = workspace_id
        ctx.roles = roles or []
        ctx.permissions = permissions or []

    _update_context(modifier)


def get_user_id() -> str | None:
    """获取当前用户 ID"""
    return get_context().user_id


def get_session_id() -> str | None:
    """获取当前会话 ID"""
    return get_context().session_id


def get_tenant_id() -> str | None:
    """获取当前租户 ID"""
    return get_context().tenant_id


def get_workspace_id() -> str | None:
    """获取当前工作空间 ID"""
    return get_context().workspace_id


def set_permission_code(code: str) -> None:
    """
    设置当前权限编码

    Args:
        code: 权限编码，如 "iam:user:create"
    """

    def modifier(ctx: Context) -> None:
        ctx.permission_code = code

    _update_context(modifier)


def get_permission_code() -> str | None:
    """获取当前权限编码"""
    return get_context().permission_code
