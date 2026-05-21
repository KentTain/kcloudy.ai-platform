"""
数据初始化模块

每个业务模块的种子脚本放在此目录下，支持幂等执行和 dry-run 预览。

模块注册方式：
    在 SEED_MODULES 字典中注册模块名和对应的种子函数。

示例：
    SEED_MODULES = {
        "tenant": tenant_seed.run,
        "user": user_seed.run,
    }
"""

from typing import Callable, Coroutine

# 种子模块注册表
# 格式: {"模块名": 异步种子函数}
# 种子函数签名: async def run(*, dry_run: bool = False) -> int
SEED_MODULES: dict[str, Callable[[bool], Coroutine[None, None, int]]] = {}

# 延迟导入并注册模块
def _register_modules() -> None:
    """注册所有种子模块"""
    global SEED_MODULES

    try:
        from demo.seeds import tenant_seed

        SEED_MODULES["tenant"] = tenant_seed.run
    except ImportError:
        pass

    try:
        from demo.seeds import admin_seed

        SEED_MODULES["admin"] = admin_seed.run
    except ImportError:
        pass


# 模块加载时注册
_register_modules()

__all__ = ["SEED_MODULES"]
