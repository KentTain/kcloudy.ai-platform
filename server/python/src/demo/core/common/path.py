"""
路径常量
"""

from pathlib import Path

# 从 demo/core/common/path.py 开始计算
# .parent = demo/core/common/
# .parent.parent = demo/core/
# .parent.parent.parent = demo/
# .parent.parent.parent.parent = src/
# .parent.parent.parent.parent.parent = 项目根目录

# 项目源码目录 (src/)
SRC_DIR = Path(__file__).parent.parent.parent.parent

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent.parent.parent.parent

# Workspace 根目录（monorepo 时有用，当前与 ROOT_DIR 相同）
WORKSPACE_ROOT_DIR = ROOT_DIR

# 日志目录 (logs/)
LOGS_DIR = ROOT_DIR / "logs"

# 配置目录 (config/)
CONFIG_FOLDER = ROOT_DIR / "config"
