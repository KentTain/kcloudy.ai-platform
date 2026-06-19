"""提供第三方扩展安全相关功能。"""

from typing import override

from fastapi.exceptions import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer as RawHTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request
from starlette.status import HTTP_403_FORBIDDEN


class HTTPBearer(RawHTTPBearer):
    """封装HTTPBearer逻辑。"""

    @override
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        """
        实现 __call__ 协议方法。

        Args:
            request (Request): request 参数。

        Returns:
            处理结果。
        """
        authorization = request.headers.get("Authorization")
        if authorization:
            scheme, credentials = get_authorization_scheme_param(authorization)
            if not (scheme and credentials):
                if self.auto_error:
                    raise HTTPException(
                        status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                    )
                else:
                    return None
            if scheme.lower() != "bearer":
                if self.auto_error:
                    raise HTTPException(
                        status_code=HTTP_403_FORBIDDEN,
                        detail="Invalid authentication credentials",
                    )
                else:
                    return None
            return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
        return None
