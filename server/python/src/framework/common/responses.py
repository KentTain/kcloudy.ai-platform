"""
统一响应格式

提供标准化的 API 响应格式。
"""

from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一 API 响应格式"""

    code: int = 0
    message: str = "success"
    data: Any | None = None


def success_response(data: Any | None = None, message: str = "success") -> dict:
    """
    创建成功响应

    Args:
        data: 响应数据
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    return ApiResponse(code=0, message=message, data=data).model_dump()


def error_response(
    message: str = "error",
    code: int = 1,
    data: Any | None = None
) -> dict:
    """
    创建错误响应

    Args:
        message: 错误消息
        code: 错误代码
        data: 附加数据

    Returns:
        dict: 响应字典
    """
    return ApiResponse(code=code, message=message, data=data).model_dump()


def paginated_response(
    items: list[Any],
    total: int,
    page: int,
    page_size: int,
    message: str = "success"
) -> dict:
    """
    创建分页响应

    Args:
        items: 数据项列表
        total: 总数量
        page: 当前页码
        page_size: 每页数量
        message: 响应消息

    Returns:
        dict: 响应字典
    """
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

    return success_response(
        data={
            "items": items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            }
        },
        message=message
    )
