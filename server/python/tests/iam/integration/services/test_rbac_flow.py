"""
RBAC 流程集成测试

测试角色、权限控制流程。
"""

import pytest


@pytest.mark.integration
class TestRBACFlow:
    """RBAC 流程测试"""

    @pytest.mark.asyncio
    async def test_role_crud_flow(self):
        """
        场景：角色 CRUD
        WHEN: 创建角色 -> 分配权限 -> 查询 -> 删除
        THEN: 流程正常
        """
        # TODO: 实现测试
        pass

    @pytest.mark.asyncio
    async def test_user_role_assignment(self):
        """
        场景：用户角色分配
        WHEN: 为用户分配角色
        THEN: 用户拥有对应权限
        """
        # TODO: 实现测试
        pass

    @pytest.mark.asyncio
    async def test_permission_check_with_wildcard(self):
        """
        场景：通配符权限检查
        WHEN: 用户拥有 user:* 权限
        THEN: 匹配所有 user: 前缀权限
        """
        # TODO: 实现测试
        pass

    @pytest.mark.asyncio
    async def test_permission_cache_invalidation(self):
        """
        场景：权限缓存失效
        WHEN: 用户角色变更
        THEN: 权限缓存被清除
        """
        # TODO: 实现测试
        pass
