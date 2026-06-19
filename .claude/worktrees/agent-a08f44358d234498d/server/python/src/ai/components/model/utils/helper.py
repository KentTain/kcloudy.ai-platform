import pydantic
from pydantic import BaseModel


def dump_model(model: BaseModel) -> dict:
    """
    将Pydantic模型转换为字典

    兼容不同版本的Pydantic库，优先使用pydantic.model_dump()函数，
    如果不存在则回退到model.model_dump()方法。

    :param model: 要转换的Pydantic模型实例
    :return: 模型的字典表示
    """
    if hasattr(pydantic, "model_dump"):
        # 优先使用pydantic模块级别的model_dump函数（新版本）
        # FIXME: mypy错误，尝试修复而不是使用type: ignore
        return pydantic.model_dump(model)
    else:
        # 回退到模型实例的model_dump方法（旧版本）
        return model.model_dump()
