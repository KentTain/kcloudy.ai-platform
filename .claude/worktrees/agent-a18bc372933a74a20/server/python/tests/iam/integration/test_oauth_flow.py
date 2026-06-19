"""
OAuth 流程集成测试

测试第三方登录流程。
"""

import pytest


@pytest.mark.integration
class TestOAuthFlow:
    """OAuth 流程测试"""

    @pytest.mark.asyncio
    async def test_oauth_authorize_url_generation(self):
        """
        场景：生成授权链接
        WHEN: 请求微信授权链接
        THEN: 返回有效 URL 和 state
        """
        # TODO: 实现测试
        pass

    @pytest.mark.asyncio
    async def test_oauth_callback_new_user(self):
        """
        场景：OAuth 回调 - 新用户
        WHEN: 新用户通过 OAuth 登录
        THEN: 自动创建用户并标记 profile_completed = FALSE
        """
        # TODO: 实现测试
        pass

    @pytest.mark.asyncio
    async def test_oauth_callback_existing_user(self):
        """
        场景：OAuth 回调 - 已有用户
        WHEN: 已绑定 OAuth 的用户登录
        THEN: 直接登录成功
        """
        # TODO: 实现测试
        pass

    @pytest.mark.asyncio
    async def test_oauth_complete_profile(self):
        """
        场景：OAuth 用户补全信息
        WHEN: OAuth 用户设置密码
        THEN: profile_completed = TRUE
        """
        # TODO: 实现测试
        pass
