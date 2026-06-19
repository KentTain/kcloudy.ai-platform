from binascii import hexlify, unhexlify

from ai_plugin.server.core.entities.invocation import InvokeType
from ai_plugin.server.core.runtime import BackwardsInvocation


class StorageInvocationError(Exception):
    """
    存储调用异常类

    当存储调用执行过程中发生问题时抛出的自定义异常
    """

    pass


class StorageInvocation(BackwardsInvocation[dict]):
    """
    存储调用类

    提供持久化存储操作的接口，包括读取、写入、删除和检查键是否存在
    """

    def set(self, key: str, val: bytes) -> None:
        """
        向持久化存储中设置键值对

        Args:
            key: 存储键名
            val: 存储的字节数据

        Raises:
            StorageInvocationError: 当调用返回无效数据时抛出
        """
        for data in self._backwards_invoke(
            InvokeType.Storage,
            dict,
            {"opt": "set", "key": key, "value": hexlify(val).decode()},
        ):
            if data["data"] == "ok":
                return

            raise StorageInvocationError(f"意外的数据: {data['data']}")

    def get(self, key: str) -> bytes:
        """
        从持久化存储中获取键对应的值

        Args:
            key: 存储键名

        Returns:
            bytes: 存储的字节数据

        Raises:
            StorageInvocationError: 当找不到对应键时抛出
        """

        for data in self._backwards_invoke(
            InvokeType.Storage,
            dict,
            {
                "opt": "get",
                "key": key,
            },
        ):
            return unhexlify(data["data"])

        raise StorageInvocationError("未找到数据")

    def delete(self, key: str) -> None:
        """
        从持久化存储中删除指定键

        Args:
            key: 要删除的存储键名

        Raises:
            StorageInvocationError: 当调用返回无效数据时抛出
        """
        for data in self._backwards_invoke(
            InvokeType.Storage,
            dict,
            {
                "opt": "del",
                "key": key,
            },
        ):
            if data["data"] == "ok":
                return

            raise StorageInvocationError(f"意外的数据: {data['data']}")

        raise StorageInvocationError("未找到数据")

    def exist(self, key: str) -> bool:
        """
        检查持久化存储中是否存在指定键

        Args:
            key: 要检查的存储键名

        Returns:
            bool: 如果键存在返回True，否则返回False

        Raises:
            StorageInvocationError: 当调用未返回任何数据时抛出
        """
        for data in self._backwards_invoke(
            InvokeType.Storage,
            dict,
            {
                "opt": "exist",
                "key": key,
            },
        ):
            return data["data"]

        raise StorageInvocationError("未找到数据")
