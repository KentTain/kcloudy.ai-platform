"""
位置辅助工具

迁移自 Alon: src/alon/components/model/internal/helper/position_helper.py

用于管理模型提供者和工具的排序位置
"""

from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from ai.components.model.internal.configs import model_config
from ai.components.model.internal.helper.yaml_utils import load_yaml_file


def get_position_map(
    folder_path: str, *, file_name: str = "_position.yaml"
) -> dict[str, int]:
    """
    从 YAML 文件中获取名称到索引的映射

    Args:
        folder_path: 文件夹路径
        file_name: YAML 文件名，默认为 '_position.yaml'

    Returns:
        以名称为键，索引为值的字典
    """
    import os

    position_file_path = os.path.join(folder_path, file_name)
    yaml_content = load_yaml_file(file_path=position_file_path, default_value=[])

    # 过滤掉空字符串和非字符串类型的项目
    positions = [
        item.strip()
        for item in yaml_content
        if item and isinstance(item, str) and item.strip()
    ]
    return {name: index for index, name in enumerate(positions)}


def get_tool_position_map(
    folder_path: str, file_name: str = "_position.yaml"
) -> dict[str, int]:
    """
    获取工具的位置映射

    从 YAML 文件中获取工具名称到索引的映射，并应用置顶配置

    Args:
        folder_path: 文件夹路径
        file_name: YAML 文件名，默认为 '_position.yaml'

    Returns:
        以工具名称为键，索引为值的字典
    """
    position_map = get_position_map(folder_path, file_name=file_name)
    return pin_position_map(
        position_map,
        pin_list=model_config.POSITION_TOOL_PINS_LIST,  # 工具置顶列表配置
    )


def get_provider_position_map(
    folder_path: str, file_name: str = "_position.yaml"
) -> dict[str, int]:
    """
    获取提供者的位置映射

    从 YAML 文件中获取提供者名称到索引的映射，并应用置顶配置

    Args:
        folder_path: 文件夹路径
        file_name: YAML 文件名，默认为 '_position.yaml'

    Returns:
        以提供者名称为键，索引为值的字典
    """
    position_map = get_position_map(folder_path, file_name=file_name)
    return pin_position_map(
        position_map,
        pin_list=model_config.POSITION_PROVIDER_PINS_LIST,  # 提供者置顶列表配置
    )


def pin_position_map(
    original_position_map: dict[str, int], pin_list: list[str]
) -> dict[str, int]:
    """
    将置顶列表中的项目置于位置映射的开头

    整体逻辑：排除 > 包含 > 置顶

    Args:
        original_position_map: 要排序和过滤的原始位置映射
        pin_list: 需要置顶的项目列表

    Returns:
        排序后的位置映射
    """
    # 按原始位置映射的索引对键进行排序
    positions = sorted(
        original_position_map.keys(), key=lambda x: original_position_map[x]
    )

    # 首先添加置顶项目到位置映射
    position_map = {name: idx for idx, name in enumerate(pin_list)}

    # 然后添加剩余的位置到位置映射
    start_idx = len(position_map)
    for name in positions:
        if name not in position_map:
            position_map[name] = start_idx
            start_idx += 1

    return position_map


def is_filtered(
    include_set: set[str],
    exclude_set: set[str],
    data: Any,
    name_func: Callable[[Any], str],
) -> bool:
    """
    检查对象是否应该被过滤掉

    整体逻辑：排除 > 包含 > 置顶

    Args:
        include_set: 要包含的名称集合
        exclude_set: 要排除的名称集合
        data: 要过滤的数据
        name_func: 获取对象名称的函数

    Returns:
        如果对象应该被过滤掉返回 True，否则返回 False
    """
    if not data:
        return False
    if not include_set and not exclude_set:
        return False

    name = name_func(data)

    # 排除集合优先级最高
    if name in exclude_set:
        return True
    # 只有在包含集合不为空时才进行过滤
    if include_set and name not in include_set:
        return True
    return False


def sort_by_position_map(
    position_map: dict[str, int],
    data: list[Any],
    name_func: Callable[[Any], str],
) -> list[Any]:
    """
    根据位置映射对对象进行排序

    如果对象的名称不在位置映射中，它将被放在末尾

    Args:
        position_map: 包含位置信息的映射，格式为 {name: index}
        data: 要排序的数据列表
        name_func: 获取对象名称的函数

    Returns:
        排序后的对象列表
    """
    if not position_map or not data:
        return data

    # 使用 float("inf") 确保未在 position_map 中找到的项目排在最后
    return sorted(data, key=lambda x: position_map.get(name_func(x), float("inf")))


def sort_to_dict_by_position_map(
    position_map: dict[str, int],
    data: list[Any],
    name_func: Callable[[Any], str],
) -> OrderedDict[str, Any]:
    """
    根据位置映射将对象排序为有序字典

    如果对象的名称不在位置映射中，它将被放在末尾

    Args:
        position_map: 包含位置信息的映射，格式为 {name: index}
        data: 要排序的数据列表
        name_func: 获取对象名称的函数

    Returns:
        包含排序后的名称和对象对的有序字典
    """
    sorted_items = sort_by_position_map(position_map, data, name_func)
    return OrderedDict([(name_func(item), item) for item in sorted_items])
