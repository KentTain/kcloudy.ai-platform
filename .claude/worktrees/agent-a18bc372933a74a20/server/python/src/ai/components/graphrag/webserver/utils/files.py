"""提供图谱检索增强生成工具相关功能。"""

import os


def get_sorted_subdirs(directory: str):
    """
    获取sorted_subdirs。

    Args:
        directory (str): directory 参数。

    Returns:
        处理结果。
    """
    subdirs = [
        d
        for d in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, d)) and not d.startswith(".")
    ]
    subdirs_sorted = sorted(subdirs, reverse=True)
    return subdirs_sorted


def get_latest_subdir(directory: str):
    # current, we only support date like output folder.
    """
    获取latest_subdir。

    Args:
        directory (str): directory 参数。

    Returns:
        处理结果。
    """
    subdirs = [
        d
        for d in os.listdir(directory)
        if os.path.isdir(os.path.join(directory, d)) and not d.startswith(".")
    ]
    if not subdirs:
        raise ValueError(f"No subdirectories found in {directory}")
    subdirs_sorted = sorted(subdirs, reverse=True)
    return subdirs_sorted[0]
