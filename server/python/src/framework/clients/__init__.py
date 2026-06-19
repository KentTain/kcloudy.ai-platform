"""
Framework 模块客户端封装

提供模块间调用的客户端封装，统一调用入口。
"""

from .iam_client import IamClient
from .inner_http_client import InnerHttpClient
from .tenant_client import TenantClient

__all__ = [
    "InnerHttpClient",
    "TenantClient",
    "IamClient",
]
