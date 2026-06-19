"""提供图谱检索增强生成工具相关功能。"""

import hashlib

from ai.components.graphrag.webserver.utils.consts import MINIO_BASE_DIR, RAGDATA_DIR


def build_root_path(namespace: str, code: str, filename: str):
    """
    构建build_root_path。

    Args:
        namespace (str): namespace 参数。
        code (str): code 参数。
        filename (str): filename 参数。

    Returns:
        处理结果。
    """
    root_dir = RAGDATA_DIR + "/" + namespace + "/" + code + "/" + md5(filename)
    return root_dir


def build_minio_path_prefix(root_dir: str):
    # root_dir格式是这样的: /data/ragdata/namespace/code/filename, 将后面的namespace/code/filename提取出来
    """
    构建build_minio_path_prefix。

    Args:
        root_dir (str): root_dir 参数。

    Returns:
        处理结果。
    """
    root_dir_list = root_dir.split("/")[-3:]
    path_prefix = "/".join(root_dir_list)
    path_prefix = MINIO_BASE_DIR + "/" + path_prefix
    return path_prefix


def md5(_input: str) -> str:
    """
    处理md5。

    Args:
        _input (str): _input 参数。

    Returns:
        处理结果。
    """
    return hashlib.md5(_input.encode()).hexdigest()
