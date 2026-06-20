"""
统一 API 响应类

提供统一的 HTTP 响应格式：
{
    "code": 200,          // HTTP status，200=成功，其他=失败
    "msg": "OK",          // 消息
    "data": {...},        // 数据
    ...扩展字段           // total/page/page_size/has_more 等
}
"""

from typing import Any

from extended.fastapi.responses import ORJSONResponse
from starlette.status import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)


class ApiResponse(ORJSONResponse):
    """
    统一 API 响应

    所有接口返回统一格式，code 与 HTTP status 一致：
    - 200: 成功
    - 其他: 失败
    """

    def __init__(
        self,
        code: int = HTTP_200_OK,
        msg: str = "OK",
        data: Any | None = None,
        **kwargs,
    ) -> None:
        """
        初始化实例。

        Args:
            code: HTTP status code
            msg: 响应消息
            data: 响应数据
            **kwargs: 扩展字段（total, page, page_size, has_more 等）
        """
        content: dict[str, Any] = {
            "code": code,
            "msg": msg,
            "data": data,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=code)

    # ─────────────────────────────────────────────────────────────────────────
    # 成功响应工厂方法
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def success(
        cls, data: Any | None = None, msg: str = "OK", **kwargs
    ) -> "ApiResponse":
        """
        成功响应 (200)

        Args:
            data: 响应数据
            msg: 响应消息，默认 "OK"
            **kwargs: 扩展字段

        Returns:
            ApiResponse 实例
        """
        return cls(code=HTTP_200_OK, msg=msg, data=data, **kwargs)

    @classmethod
    def paginated(
        cls,
        data: Any | None = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        msg: str = "OK",
        **kwargs,
    ) -> "ApiResponse":
        """
        分页响应 (200)

        Args:
            data: 数据列表
            total: 总条数
            page: 当前页码
            page_size: 每页条数
            msg: 响应消息，默认 "OK"
            **kwargs: 扩展字段

        Returns:
            ApiResponse 实例
        """
        return cls(
            code=HTTP_200_OK,
            msg=msg,
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            **kwargs,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # 失败响应工厂方法
    # ─────────────────────────────────────────────────────────────────────────

    @classmethod
    def fail(
        cls,
        msg: str,
        code: int = HTTP_400_BAD_REQUEST,
        data: Any | None = None,
        **kwargs,
    ) -> "ApiResponse":
        """
        失败响应

        Args:
            msg: 错误消息
            code: HTTP status code，默认 400
            data: 附加数据
            **kwargs: 扩展字段

        Returns:
            ApiResponse 实例
        """
        return cls(code=code, msg=msg, data=data, **kwargs)

    @classmethod
    def bad_request(cls, msg: str = "请求错误", data: Any | None = None) -> "ApiResponse":
        """请求错误 (400)"""
        return cls.fail(msg=msg, code=HTTP_400_BAD_REQUEST, data=data)

    @classmethod
    def unauthorized(cls, msg: str = "未授权") -> "ApiResponse":
        """未授权 (401)"""
        return cls.fail(msg=msg, code=HTTP_401_UNAUTHORIZED)

    @classmethod
    def forbidden(cls, msg: str = "禁止访问") -> "ApiResponse":
        """禁止访问 (403)"""
        return cls.fail(msg=msg, code=HTTP_403_FORBIDDEN)

    @classmethod
    def not_found(cls, msg: str = "资源不存在") -> "ApiResponse":
        """资源不存在 (404)"""
        return cls.fail(msg=msg, code=HTTP_404_NOT_FOUND)

    @classmethod
    def conflict(cls, msg: str = "资源冲突") -> "ApiResponse":
        """资源冲突 (409)"""
        return cls.fail(msg=msg, code=HTTP_409_CONFLICT)

    @classmethod
    def validation_error(
        cls, msg: str = "数据验证失败", data: Any | None = None
    ) -> "ApiResponse":
        """验证错误 (422)"""
        return cls.fail(msg=msg, code=HTTP_422_UNPROCESSABLE_ENTITY, data=data)

    @classmethod
    def internal_error(cls, msg: str = "服务器内部错误") -> "ApiResponse":
        """服务器错误 (500)"""
        return cls.fail(msg=msg, code=HTTP_500_INTERNAL_SERVER_ERROR)
