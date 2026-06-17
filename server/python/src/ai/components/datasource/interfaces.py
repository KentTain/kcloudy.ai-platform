"""数据库连接接口定义"""

from abc import ABC, abstractmethod
from typing import Any
from collections.abc import Iterable


class BaseConnect(ABC):
    """数据库连接基类"""

    @abstractmethod
    async def get_show_create_table(self, table_name: str) -> str:
        """
        获取指定表的DDL

        Args:
            table_name: 表名

        Returns:
            DDL 字符串
        """
        raise NotImplementedError

    @abstractmethod
    async def get_example_data(self, table_name: str, count: int = 3) -> list[dict]:
        """
        获取指定表的示例数据

        Args:
            table_name: 表名
            count: 示例数据数量

        Returns:
            示例数据列表
        """
        raise NotImplementedError

    @abstractmethod
    async def get_table_names(self) -> Iterable[str]:
        """
        获取所有表名

        Returns:
            表名集合
        """
        raise NotImplementedError

    @abstractmethod
    async def get_table_info(self, table_names: list[str] | None = None) -> str:
        """
        获取指定表的表信息

        Args:
            table_names: 表名集合

        Returns:
            表信息字符串
        """
        raise NotImplementedError

    @abstractmethod
    async def get_database_names(self) -> list[str]:
        """
        获取数据库名称

        Returns:
            数据库名称列表
        """
        raise NotImplementedError

    @abstractmethod
    async def get_table_comments(self) -> list[tuple[str, str]]:
        """
        获取所有表注释

        Returns:
            表注释列表（table_name, comment）
        """
        raise NotImplementedError

    @abstractmethod
    async def get_table_comment(self, table_name: str) -> dict:
        """
        获取表注释

        Args:
            table_name: 表名

        Returns:
            包含 text 字段的字典
        """
        raise NotImplementedError

    @abstractmethod
    async def get_columns(self, table_name: str) -> list[dict]:
        """
        获取指定表的列信息

        Args:
            table_name: 表名

        Returns:
            列信息列表
        """
        raise NotImplementedError

    @abstractmethod
    async def get_column_comments(self, table_name: str) -> list[tuple[str, str]]:
        """
        获取指定表的列注释

        Args:
            table_name: 表名

        Returns:
            列注释列表（column_name, comment）
        """
        raise NotImplementedError

    @abstractmethod
    async def get_fields(self, table_name: str) -> list[tuple[str, str, str, str, str]]:
        """
        获取指定表的列信息

        Args:
            table_name: 表名

        Returns:
            列信息集合 [(name, type, default_expression, is_in_primary_key, comment)]
        """
        raise NotImplementedError

    async def get_simple_fields(self, table_name: str) -> list[tuple]:
        """
        获取指定表的列信息

        Args:
            table_name: 表名

        Returns:
            列信息集合
        """
        return await self.get_fields(table_name)

    @abstractmethod
    async def get_indexes(self, table_name: str) -> list[dict]:
        """
        获取指定表的索引

        Args:
            table_name: 表名

        Returns:
            索引信息列表
        """
        raise NotImplementedError

    @abstractmethod
    async def get_index_info(self, table_names: list[str] | None = None) -> str:
        """
        获取指定表的索引信息

        Args:
            table_names: 表名集合

        Returns:
            索引信息字符串
        """
        raise NotImplementedError

    @abstractmethod
    async def run(self, command: str, fetch: str = "all") -> list:
        """
        执行SQL命令

        Args:
            command: SQL命令
            fetch: 获取类型

        Returns:
            查询结果
        """
        raise NotImplementedError

    @abstractmethod
    async def run_to_df(self, command: str, fetch: str = "all") -> Any:
        """
        执行SQL命令并返回DataFrame

        Args:
            command: SQL命令
            fetch: 获取类型

        Returns:
            DataFrame
        """
        raise NotImplementedError
