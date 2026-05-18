"""
环境变量管理
"""

import getopt
import os
import sys
from typing import Any

ENV: Any = None

VALID_ENVS = [
    "local",
    "dev",
    "test",
    "prod",
]


def is_valid_env_candidate_str(candidate: str | None) -> bool:
    """检查环境变量候选字符串是否合法"""
    return candidate in VALID_ENVS


def use_os_env() -> None:
    global ENV
    os_env = os.environ.get("PYTHON_SERVICE_ENV")
    if is_valid_env_candidate_str(os_env):
        ENV = os_env


def use_arg_env() -> None:
    global ENV
    try:
        opts, _args = getopt.getopt(sys.argv[1:], "e:", ["env="])
        for opt, arg in opts:
            if opt in ("-e", "--env"):
                if is_valid_env_candidate_str(arg):
                    ENV = arg
    except getopt.GetoptError:
        pass


def use_default_env() -> None:
    global ENV
    ENV = "local"


use_arg_env()

if ENV is None:
    use_os_env()

if ENV is None:
    use_default_env()


__all__ = ["ENV"]
