from collections.abc import Mapping
from typing import Any, Protocol

from werkzeug import Request


class OAuthProviderProtocol(Protocol):
    """
    OAuth提供者协议接口

    定义OAuth认证提供者必须实现的方法
    """

    def oauth_get_authorization_url(self, system_credentials: Mapping[str, Any]) -> str:
        """
        获取授权URL

        Args:
            system_credentials: 系统凭证

        Returns:
            str: 授权URL地址
        """
        ...

    def oauth_get_credentials(
        self,
        system_credentials: Mapping[str, Any],
        request: Request,
    ) -> Mapping[str, Any]:
        """
        获取认证凭证

        Args:
            system_credentials: 系统凭证
            request: HTTP请求对象

        Returns:
            Mapping[str, Any]: 用户凭证信息
        """
        ...
