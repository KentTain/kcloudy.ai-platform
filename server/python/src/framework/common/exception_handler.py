"""
全局异常处理器

将自定义异常转换为统一的 API 响应格式。
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from framework.common.exceptions import AppException
from framework.common.responses import error_response


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """
    处理应用异常

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        JSONResponse: JSON 响应
    """
    return JSONResponse(
        status_code=exc.code,
        content=error_response(
            message=exc.message,
            code=exc.code,
            data=exc.data
        )
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    处理未捕获的异常

    Args:
        request: 请求对象
        exc: 异常实例

    Returns:
        JSONResponse: JSON 响应
    """
    # 在生产环境中，不应该暴露详细错误信息
    import traceback
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content=error_response(
            message="服务器内部错误",
            code=500
        )
    )


def register_exception_handlers(app):
    """
    注册异常处理器到 FastAPI 应用

    Args:
        app: FastAPI 应用实例
    """
    from fastapi.exceptions import RequestValidationError

    @app.exception_handler(AppException)
    async def handle_app_exception(request: Request, exc: AppException):
        return await app_exception_handler(request, exc)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content=error_response(
                message="请求参数验证失败",
                code=422,
                data=exc.errors()
            )
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception):
        return await generic_exception_handler(request, exc)
