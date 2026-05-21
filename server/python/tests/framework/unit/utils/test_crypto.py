"""
crypto 模块单元测试

测试 BCrypt 密码哈希和验证功能
"""

import pytest


class TestHashPassword:
    """密码哈希测试"""

    def test_hash_password_success(self):
        """
        场景：正常密码哈希
        WHEN: 输入有效密码
        THEN: 返回 BCrypt 哈希值
        """
        from framework.utils.crypto import hash_password

        password = "MySecureP@ss123"
        result = hash_password(password)

        # BCrypt 哈希值以 $2b$ 开头，长度为 60
        assert result.startswith("$2b$")
        assert len(result) == 60

    def test_hash_password_different_salt(self):
        """
        场景：相同密码生成不同哈希值
        WHEN: 对同一密码哈希两次
        THEN: 返回不同的哈希值（盐值不同）
        """
        from framework.utils.crypto import hash_password

        password = "MySecureP@ss123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # 相同密码应产生不同哈希（BCrypt 自带随机盐）
        assert hash1 != hash2

    def test_hash_password_empty(self):
        """
        场景：空密码
        WHEN: 输入空字符串
        THEN: 抛出 ValueError
        """
        from framework.utils.crypto import hash_password

        with pytest.raises(ValueError, match="密码不能为空"):
            hash_password("")


class TestVerifyPassword:
    """密码验证测试"""

    def test_verify_password_success(self):
        """
        场景：密码验证成功
        WHEN: 输入正确密码和哈希值
        THEN: 返回 True
        """
        from framework.utils.crypto import hash_password, verify_password

        password = "MySecureP@ss123"
        hash_value = hash_password(password)

        result = verify_password(password, hash_value)
        assert result is True

    def test_verify_password_wrong_password(self):
        """
        场景：密码验证失败
        WHEN: 输入错误密码
        THEN: 返回 False
        """
        from framework.utils.crypto import hash_password, verify_password

        password = "MySecureP@ss123"
        hash_value = hash_password(password)

        result = verify_password("WrongPassword", hash_value)
        assert result is False

    def test_verify_password_empty_password(self):
        """
        场景：空密码验证
        WHEN: 输入空密码
        THEN: 返回 False
        """
        from framework.utils.crypto import hash_password, verify_password

        password = "MySecureP@ss123"
        hash_value = hash_password(password)

        result = verify_password("", hash_value)
        assert result is False

    def test_verify_password_invalid_hash(self):
        """
        场景：无效哈希值
        WHEN: 哈希值格式错误
        THEN: 返回 False
        """
        from framework.utils.crypto import verify_password

        result = verify_password("password", "invalid_hash")
        assert result is False


class TestPasswordStrength:
    """密码强度校验测试"""

    def test_validate_password_strength_valid(self):
        """
        场景：密码强度有效
        WHEN: 密码符合强度要求（8-32位，含字母和数字）
        THEN: 验证通过
        """
        from framework.utils.crypto import validate_password_strength

        result = validate_password_strength("Password123")
        assert result is True

    def test_validate_password_strength_too_short(self):
        """
        场景：密码太短
        WHEN: 密码长度小于 8 位
        THEN: 抛出 ValueError
        """
        from framework.utils.crypto import validate_password_strength

        with pytest.raises(ValueError, match="密码长度需 8-32 位"):
            validate_password_strength("Pass1")

    def test_validate_password_strength_too_long(self):
        """
        场景：密码太长
        WHEN: 密码长度超过 32 位
        THEN: 抛出 ValueError
        """
        from framework.utils.crypto import validate_password_strength

        long_password = "A" * 33 + "1"
        with pytest.raises(ValueError, match="密码长度需 8-32 位"):
            validate_password_strength(long_password)

    def test_validate_password_strength_no_letter(self):
        """
        场景：密码不含字母
        WHEN: 密码只含数字
        THEN: 抛出 ValueError
        """
        from framework.utils.crypto import validate_password_strength

        with pytest.raises(ValueError, match="密码必须包含字母和数字"):
            validate_password_strength("12345678")

    def test_validate_password_strength_no_digit(self):
        """
        场景：密码不含数字
        WHEN: 密码只含字母
        THEN: 抛出 ValueError
        """
        from framework.utils.crypto import validate_password_strength

        with pytest.raises(ValueError, match="密码必须包含字母和数字"):
            validate_password_strength("Password")
