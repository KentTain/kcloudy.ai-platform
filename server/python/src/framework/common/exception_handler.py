"""
全局异常处理器

将自定义异常转换为统一的 API 响应格式。
"""

from fastapi import Request
from fastapi.exceptions import HTTPException

from framework.common.exceptions import AppException
from framework.common.response import ApiResponse


async def http_exception_handler(request: Request, exc: HTTPException) -> ApiResponse:
    """
    处理 HTTP 异常

    Args:
        request: 请求对象
        exc: HTTP 异常实例

    Returns:
        ApiResponse: 错误响应
    """
    return ApiResponse.fail(code=exc.status_code, msg=str(exc.detail))


async def app_exception_handler(request: Request, exc: AppException) -> ApiResponse:
    """
    处理应用异常

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        ApiResponse: 错误响应
    """
    return ApiResponse.fail(code=exc.code, msg=exc.message, data=exc.data)


async def generic_exception_handler(request: Request, exc: Exception) -> ApiResponse:
    """
    处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        ApiResponse: 错误响应
    """
    # 在生产环境中，不应该暴露详细错误信息
    import traceback

    traceback.print_exc()

    return ApiResponse.internal_error()


def register_exception_handlers(app):
    """
    注册异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException):
        return await http_exception_handler(request, exc)

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        return await app_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return ApiResponse.validation_error(
            msg="请求参数验证失败", data=exc.errors()
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        return await generic_exception_handler(request, exc)
