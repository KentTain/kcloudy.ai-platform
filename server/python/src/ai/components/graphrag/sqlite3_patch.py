"""
SQLite3 模块补丁

当 Python 编译时未正确构建 _sqlite3 模块时，使用 pysqlite3 作为替代方案。
此补丁在导入时自动应用，对应用代码透明。

使用场景：
- 手动编译 Python 时未检测到 SQLite 开发库
- 基础镜像缺少 SQLite 运行时库
"""

import sys

# 尝试检测 _sqlite3 是否可用
try:
    import _sqlite3  # noqa: F401  # type: ignore
except ImportError:
    # _sqlite3 不可用，尝试使用 pysqlite3 替代
    try:
        import pysqlite3

        # 将 pysqlite3 注册为 sqlite3 模块
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        # pysqlite3 也未安装，保持原样（后续使用时会报错）
        pass
