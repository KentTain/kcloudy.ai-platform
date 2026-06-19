"""
文件工具函数
"""

import os
import hashlib
from pathlib import Path
from typing import BinaryIO


def get_file_extension(filename: str) -> str:
    """
    获取文件扩展名

    Args:
        filename: 文件名

    Returns:
        str: 扩展名（不含点号）
    """
    if not filename:
        return ""

    _, ext = os.path.splitext(filename)
    return ext.lstrip(".").lower()


def get_file_size(file_path: str | Path) -> int:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        int: 文件大小
    """
    return os.path.getsize(file_path)


def get_file_md5(file_path: str | Path) -> str:
    """
    计算文件的 MD5 哈希值

    Args:
        file_path: 文件路径

    Returns:
        str: MD5 哈希值
    """
    hash_md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def get_file_md5_from_stream(stream: BinaryIO) -> str:
    """
    计算文件流的 MD5 哈希值

    Args:
        stream: 文件流

    Returns:
        str: MD5 哈希值
    """
    hash_md5 = hashlib.md5()

    for chunk in iter(lambda: stream.read(4096), b""):
        hash_md5.update(chunk)

    # 重置流位置
    stream.seek(0)

    return hash_md5.hexdigest()


def ensure_dir(dir_path: str | Path) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        dir_path: 目录路径

    Returns:
        Path: 目录路径对象
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def delete_file(file_path: str | Path) -> bool:
    """
    删除文件

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否成功
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False


def read_file_content(file_path: str | Path, encoding: str = "utf-8") -> str:
    """
    读取文件内容

    Args:
        file_path: 文件路径
        encoding: 编码

    Returns:
        str: 文件内容
    """
    with open(file_path, encoding=encoding) as f:
        return f.read()


def write_file_content(
    file_path: str | Path,
    content: str,
    encoding: str = "utf-8"
) -> None:
    """
    写入文件内容

    Args:
        file_path: 文件路径
        content: 内容
        encoding: 编码
    """
    path = Path(file_path)
    ensure_dir(path.parent)

    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def human_readable_size(size: int) -> str:
    """
    将字节数转换为人类可读格式

    Args:
        size: 字节数

    Returns:
        str: 可读格式，如 "1.5 MB"
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
        size /= 1024

    return f"{size:.1f} PB"


def get_content_type(filename: str) -> str:
    """
    根据文件扩展名获取 Content-Type

    Args:
        filename: 文件名

    Returns:
        str: Content-Type
    """
    import mimetypes

    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"
