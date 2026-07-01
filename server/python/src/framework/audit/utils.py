"""
审计日志工具函数

提供审计日志相关的工具函数。
"""

from sqlalchemy.ext.asyncio import AsyncSession


def extract_session(args: tuple, kwargs: dict) -> AsyncSession | None:
    """
    从方法参数中提取数据库 Session

    Args:
        args: 位置参数
        kwargs: 关键字参数

    Returns:
        AsyncSession 或 None
    """
    if "session" in kwargs:
        return kwargs["session"]

    for arg in args:
        if isinstance(arg, AsyncSession):
            return arg

    return None


async def get_model_before_data(
    args: tuple,
    kwargs: dict,
    model_class: type,
    id_param: str = "id",
) -> dict | None:
    """
    获取模型操作前的数据

    Args:
        args: 方法位置参数
        kwargs: 方法关键字参数
        model_class: 模型类
        id_param: ID 参数名

    Returns:
        模型数据字典，如果未找到返回 None
    """
    session = extract_session(args, kwargs)
    if not session:
        return None

    model_id = kwargs.get(id_param)
    if not model_id:
        return None

    model = await session.get(model_class, model_id)
    if not model:
        return None

    return model.to_dict() if hasattr(model, "to_dict") else None
