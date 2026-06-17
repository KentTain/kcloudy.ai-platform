"""加密算法接口定义"""

from abc import ABC, abstractmethod


class BaseEncryption(ABC):
    """加密算法基类"""

    @abstractmethod
    def encrypt(self, data: str | bytes) -> str:
        """加密数据"""
        pass

    @abstractmethod
    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        pass
