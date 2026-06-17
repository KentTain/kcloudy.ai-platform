"""数据库类型定义"""

import os
from enum import Enum


class DbInfo:
    """数据库信息封装"""

    def __init__(self, name: str, is_file_db: bool = False):
        """
        初始化实例。

        Args:
            name: 数据库名称
            is_file_db: 是否为文件数据库
        """
        self.name = name
        self.is_file_db = is_file_db


class DBType(Enum):
    """数据库类型枚举"""

    MYSQL = DbInfo("mysql")
    ORACLE = DbInfo("oracle")
    MSSQL = DbInfo("mssql")
    POSTGRESQL = DbInfo("postgresql")
    SQLITE = DbInfo("sqlite", True)
    DAMENG = DbInfo("dm")
    CLICKHOUSE = DbInfo("clickhouse")

    def value(self) -> str:
        """获取数据库类型名称"""
        return self._value_.name

    def is_file_db(self) -> bool:
        """是否为文件数据库"""
        return self._value_.is_file_db

    @staticmethod
    def of_db_type(db_type: str) -> "DBType | None":
        """
        根据数据库类型字符串获取枚举值

        Args:
            db_type: 数据库类型字符串

        Returns:
            DBType 枚举值或 None
        """
        for item in DBType:
            if item.value() == db_type:
                return item
        return None

    @staticmethod
    def parse_file_db_name_from_path(db_type: str, local_db_path: str) -> str:
        """
        从文件路径解析数据库名称

        Args:
            db_type: 数据库类型
            local_db_path: 本地数据库文件路径

        Returns:
            数据库名称
        """
        base_name = os.path.basename(local_db_path)
        db_name = os.path.splitext(base_name)[0]
        if "." in db_name:
            db_name = os.path.splitext(db_name)[0]
        return db_type + "_" + db_name
