"""
异常类定义

提供统一的异常类层次结构。
"""

from typing import Any


class AppException(RuntimeError):
    """应用异常基类"""

    def __init__(self, message: str = "应用错误", code: int = 500, data: Any | None = None):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(self.message)


class UnauthorizedError(AppException):
    """未授权异常"""

    def __init__(self, message: str = "未授权"):
        super().__init__(message=message, code=401)


class ForbiddenError(AppException):
    """禁止访问异常"""

    def __init__(self, message: str = "禁止访问"):
        super().__init__(message=message, code=403)


class NotFoundError(AppException):
    """未找到异常"""

    def __init__(self, message: str = "未找到数据"):
        super().__init__(message=message, code=404)


class BadRequestError(AppException):
    """请求错误异常"""

    def __init__(self, message: str = "请求错误", data: Any | None = None):
        super().__init__(message=message, code=400, data=data)


class ServiceUnavailableError(AppException):
    """服务不可用异常"""

    def __init__(self, message: str = "服务暂时不可用"):
        super().__init__(message=message, code=503)


class RequestEntityTooLargeError(AppException):
    """请求实体过大异常"""

    def __init__(self, message: str = "请求实体过大"):
        super().__init__(message=message, code=413)


class ClientClosedRequestError(AppException):
    """客户端关闭请求异常"""

    def __init__(self, message: str = "客户端已关闭请求"):
        super().__init__(message=message, code=499)


class UnsupportedMediaTypeError(AppException):
    """不支持的媒体类型异常"""

    def __init__(self, message: str = "不支持的媒体类型"):
        super().__init__(message=message, code=415)


class ValidationError(AppException):
    """验证错误异常"""

    def __init__(self, message: str = "数据验证失败", data: Any | None = None):
        super().__init__(message=message, code=422, data=data)


class ConflictError(AppException):
    """冲突异常"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(message=message, code=409)
