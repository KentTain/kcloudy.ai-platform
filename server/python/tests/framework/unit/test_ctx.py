"""测试上下文权限编码"""

import pytest
from framework.common.ctx import (
    get_context,
    set_permission_code,
    get_permission_code,
)


def test_set_and_get_permission_code():
    """测试设置和获取权限编码"""
    # 设置权限编码
    set_permission_code("iam:user:create")

    # 获取权限编码
    permission_code = get_permission_code()

    assert permission_code == "iam:user:create"


def test_get_permission_code_default_none():
    """测试默认权限编码为 None"""
    # 清空上下文
    from framework.common.ctx import clear_context
    clear_context()

    # 获取权限编码
    permission_code = get_permission_code()

    assert permission_code is None
