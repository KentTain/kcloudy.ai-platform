"""
异常处理器
"""

from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.requests import Request
from fastapi.responses import ORJSONResponse
from loguru import logger
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from demo.common.exceptions import (
    BadRequestError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)

_logger = logger.bind(name=__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """注册异常处理器"""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return ORJSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "msg": exc.detail},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        return ORJSONResponse(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "code": HTTP_422_UNPROCESSABLE_ENTITY,
                "msg": "请求参数错误",
                "details": str(exc),
            },
        )

    @app.exception_handler(UnauthorizedError)
    async def unauthorized_exception_handler(request: Request, exc: UnauthorizedError):
        return ORJSONResponse(
            status_code=HTTP_401_UNAUTHORIZED,
            content={"code": HTTP_401_UNAUTHORIZED, "msg": exc.message},
        )

    @app.exception_handler(ForbiddenError)
    async def forbidden_exception_handler(request: Request, exc: ForbiddenError):
        return ORJSONResponse(
            status_code=HTTP_403_FORBIDDEN,
            content={"code": HTTP_403_FORBIDDEN, "msg": exc.message},
        )

    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return ORJSONResponse(
            status_code=HTTP_404_NOT_FOUND,
            content={"code": HTTP_404_NOT_FOUND, "msg": exc.message},
        )

    @app.exception_handler(BadRequestError)
    async def bad_request_exception_handler(request: Request, exc: BadRequestError):
        return ORJSONResponse(
            status_code=HTTP_400_BAD_REQUEST,
            content={
                "code": HTTP_400_BAD_REQUEST,
                "msg": exc.message,
                "data": exc.data,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        _logger.exception(f"Unhandled exception: {exc}")
        return ORJSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={"code": HTTP_500_INTERNAL_SERVER_ERROR, "msg": "服务器内部错误"},
        )
