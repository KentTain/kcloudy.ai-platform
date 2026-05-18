"""
字典工具函数
"""

from copy import deepcopy


def deep_merge_dict(x: dict, y: dict) -> dict:
    """深度合并两个字典"""
    z = deepcopy(x)
    z.update(y)
    for k, v in z.items():
        if k in x and k in y:
            if isinstance(x[k], dict) and isinstance(y[k], dict):
                z[k] = deep_merge_dict(x[k], y[k])
    return z
