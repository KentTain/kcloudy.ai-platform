"""
加密工具单元测试
"""

import pytest

from framework.utils.crypto import (
    CryptoError,
    decrypt,
    decrypt_with_tenant_key,
    encrypt,
    encrypt_with_tenant_key,
    generate_tenant_key,
    get_master_key,
)


class TestEncryptDecrypt:
    """加密解密测试"""

    def test_encrypt_decrypt_roundtrip(self):
        """加密后解密应返回原文"""
        plaintext = "my_secret_password"
        encrypted = encrypt(plaintext)
        decrypted = decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_returns_different_ciphertext(self):
        """每次加密应返回不同的密文（因为随机 nonce）"""
        plaintext = "same_password"
        encrypted1 = encrypt(plaintext)
        encrypted2 = encrypt(plaintext)

        assert encrypted1 != encrypted2

    def test_decrypt_invalid_format_raises(self):
        """解密无效格式应抛出异常"""
        with pytest.raises(CryptoError):
            decrypt("invalid_format")

    def test_decrypt_wrong_key_raises(self):
        """使用错误密钥解密应失败"""
        plaintext = "secret"
        encrypted = encrypt(plaintext)

        # 使用错误的密钥
        wrong_key = b"0" * 32
        with pytest.raises(CryptoError):
            decrypt(encrypted, wrong_key)

    def test_encrypt_empty_string(self):
        """加密空字符串返回空"""
        assert encrypt("") == ""

    def test_decrypt_empty_string(self):
        """解密空字符串返回空"""
        assert decrypt("") == ""


class TestTenantKey:
    """租户密钥测试"""

    def test_generate_tenant_key_length(self):
        """生成的租户密钥长度应为 64 个十六进制字符"""
        key = generate_tenant_key()
        assert len(key) == 64

    def test_generate_tenant_key_uniqueness(self):
        """每次生成的租户密钥应不同"""
        key1 = generate_tenant_key()
        key2 = generate_tenant_key()
        assert key1 != key2


class TestTenantKeyEncryptDecrypt:
    """租户密钥加密解密测试"""

    def test_encrypt_with_tenant_key(self):
        """使用租户密钥加密解密"""
        tenant_key = generate_tenant_key()
        plaintext = "database_password"
        encrypted = encrypt_with_tenant_key(plaintext, tenant_key)
        decrypted = decrypt_with_tenant_key(encrypted, tenant_key)

        assert decrypted == plaintext

    def test_encrypt_with_different_tenant_keys(self):
        """不同租户密钥加密的密文不能互相解密"""
        key1 = generate_tenant_key()
        key2 = generate_tenant_key()
        plaintext = "secret"

        encrypted = encrypt_with_tenant_key(plaintext, key1)

        with pytest.raises(CryptoError):
            decrypt_with_tenant_key(encrypted, key2)


class TestMasterKey:
    """主密钥测试"""

    def test_get_master_key_returns_bytes(self):
        """主密钥应返回 32 字节"""
        key = get_master_key()
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_master_key_caching(self):
        """主密钥应被缓存"""
        key1 = get_master_key()
        key2 = get_master_key()
        assert key1 == key2
