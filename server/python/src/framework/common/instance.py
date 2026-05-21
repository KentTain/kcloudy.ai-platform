"""
实例全局常量管理
"""

_instance_id: str | None = None


def get_instance_id() -> str:
    """获取当前实例ID"""
    global _instance_id
    if _instance_id is None:
        raise RuntimeError("实例ID未初始化")
    return _instance_id


def set_instance_id() -> None:
    """设置实例ID"""
    from nanoid import generate

    global _instance_id
    if _instance_id is not None:
        return
    _instance_id = generate()
