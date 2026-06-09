"""
资源配置密码加密工具单元测试
"""

import pytest
from unittest.mock import patch, MagicMock

from framework.utils.resource_crypto import (
    encrypt_password,
    decrypt_password,
    mask_password,
    is_encrypted,
)


class TestEncryptPassword:
    """encrypt_password 函数测试"""

    def test_encrypts_plain_password(self):
        """加密明文密码"""
        with patch("framework.utils.resource_crypto.encrypt") as mock_encrypt:
            mock_encrypt.return_value = "nonce:ciphertext"

            result = encrypt_password("my_secret_password")

        mock_encrypt.assert_called_once_with("my_secret_password")
        assert result == "nonce:ciphertext"

    def test_returns_empty_for_empty_password(self):
        """空密码返回空字符串"""
        result = encrypt_password("")
        assert result == ""

    def test_propagates_crypto_error(self):
        """加密失败时抛出 CryptoError"""
        from framework.utils.crypto import CryptoError

        with patch("framework.utils.resource_crypto.encrypt") as mock_encrypt:
            mock_encrypt.side_effect = CryptoError("加密失败")

            with pytest.raises(CryptoError):
                encrypt_password("password")


class TestDecryptPassword:
    """decrypt_password 函数测试"""

    def test_decrypts_cipher(self):
        """解密密文"""
        with patch("framework.utils.resource_crypto.decrypt") as mock_decrypt:
            mock_decrypt.return_value = "my_secret_password"

            result = decrypt_password("nonce:ciphertext")

        mock_decrypt.assert_called_once_with("nonce:ciphertext")
        assert result == "my_secret_password"

    def test_returns_empty_for_empty_cipher(self):
        """空密文返回空字符串"""
        result = decrypt_password("")
        assert result == ""

    def test_propagates_crypto_error(self):
        """解密失败时抛出 CryptoError"""
        from framework.utils.crypto import CryptoError

        with patch("framework.utils.resource_crypto.decrypt") as mock_decrypt:
            mock_decrypt.side_effect = CryptoError("解密失败")

            with pytest.raises(CryptoError):
                decrypt_password("invalid_cipher")


class TestMaskPassword:
    """mask_password 函数测试"""

    def test_masks_non_empty_password(self):
        """非空密码返回星号"""
        result = mask_password("any_encrypted_value")
        assert result == "******"

    def test_masks_none_password(self):
        """None 返回空字符串"""
        result = mask_password(None)
        assert result == ""

    def test_masks_empty_password(self):
        """空字符串返回空字符串"""
        result = mask_password("")
        assert result == ""

    def test_always_returns_same_mask(self):
        """总是返回相同的脱敏值"""
        result1 = mask_password("encrypted1")
        result2 = mask_password("encrypted2")
        result3 = mask_password("short")

        assert result1 == result2 == result3 == "******"


class TestIsEncrypted:
    """is_encrypted 函数测试"""

    def test_returns_true_for_valid_format(self):
        """有效加密格式返回 True"""
        # 模拟 nonce:ciphertext 格式
        nonce = "a" * 24  # 12 字节 = 24 个十六进制字符
        ciphertext = "b" * 32
        encrypted = f"{nonce}:{ciphertext}"

        assert is_encrypted(encrypted) is True

    def test_returns_false_for_plain_text(self):
        """明文返回 False"""
        assert is_encrypted("plain_password") is False

    def test_returns_false_for_missing_colon(self):
        """缺少冒号返回 False"""
        assert is_encrypted("abcdef123456") is False

    def test_returns_false_for_invalid_hex(self):
        """非十六进制字符返回 False"""
        assert is_encrypted("ghij:klmn") is False

    def test_returns_false_for_empty_string(self):
        """空字符串返回 False"""
        assert is_encrypted("") is False

    def test_returns_false_for_none(self):
        """None 返回 False"""
        assert is_encrypted(None) is False

    def test_returns_false_for_too_many_parts(self):
        """多于两部分返回 False"""
        assert is_encrypted("a:b:c") is False
