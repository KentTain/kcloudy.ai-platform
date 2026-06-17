"""
缓存键生成工具

用于生成 LLM 调用的缓存键,确保相同的输入和参数产生相同的缓存键。
"""

import hashlib
import json


def _llm_string(params: dict) -> str:
    """
    将 LLM 参数转换为字符串表示

    注意:新版本的缓存不包含 n 参数(生成数量),这样可以避免为相同的提示创建新的缓存键。

    Args:
        params: LLM 参数字典

    Returns
    -------
        参数的字符串表示
    """
    # 如果参数中有 max_tokens 但没有 n,则将 n 设为 None
    # 这样可以避免为相同的提示创建新的缓存键
    if "max_tokens" in params and "n" not in params:
        params["n"] = None
    return str(sorted((k, v) for k, v in params.items()))


def _hash(_input: str) -> str:
    """
    使用确定性的哈希方法

    Args:
        _input: 要哈希的字符串

    Returns
    -------
        MD5 哈希值的十六进制表示
    """
    return hashlib.md5(_input.encode()).hexdigest()


def create_hash_key(
    operation: str, prompt: str, parameters: dict, history: list[dict] | None
) -> str:
    """
    根据提示词,模型和设置计算缓存键

    Args:
        operation: 操作类型(如 'chat', 'completion' 等)
        prompt: 传递给语言模型的提示词
        parameters: 语言模型的参数设置
        history: 对话历史记录(可选)

    Returns
    -------
        缓存键字符串,格式为 "{operation}-{hash}"
    """
    llm_string = _llm_string(parameters)
    history_string = _hash(json.dumps(history, ensure_ascii=False)) if history else None
    hash_string = (
        _hash(prompt + llm_string + history_string)
        if history_string
        else _hash(prompt + llm_string)
    )
    return f"{operation}-{hash_string}"
