"""MySQL 数据库连接器"""

from loguru import logger
from sqlalchemy.schema import CreateTable

from ai.components.datasource.rdbms.base import RDBMSDatabase

_logger = logger.bind(name=__name__)


class MySQLConnect(RDBMSDatabase):
    """MySQL数据库连接"""

    db_type: str = "mysql"
    db_dialect: str = "mysql"
    driver: str = "mysql+aiomysql"

    default_db = ["information_schema", "performance_schema", "sys", "mysql"]

    async def get_table_info_map(
        self, table_names: list[str] | None = None
    ) -> dict[str, str]:
        """
        获取表的详细信息

        Args:
            table_names: 表名数组不传查询全部

        Returns:
            dict: k 表名，v 建表语句 + 索引 + 示例数据
        """
        all_table_names = self.get_usable_table_names()
        if table_names is not None:
            missing_tables = set(table_names).difference(all_table_names)
            if missing_tables:
                raise ValueError(f"table_names {missing_tables} not found in database")
            all_table_names = table_names

        meta_tables = [
            tbl
            for tbl in self._metadata.sorted_tables
            if tbl.name in set(all_table_names)
            and not (self.dialect == "sqlite" and tbl.name.startswith("sqlite_"))
        ]

        tables = {}
        for table in meta_tables:
            # 添加创建表命令
            async with self._engine.begin() as conn:
                create_table_sql = await conn.run_sync(
                    lambda sync_conn, t=table: str(CreateTable(t).compile(sync_conn))
                )

            table_info = f"{create_table_sql.rstrip()}"
            has_extra_info = (
                self._indexes_in_table_info or self._sample_rows_in_table_info
            )
            if has_extra_info:
                table_info += "\n\n/*"
            if self._indexes_in_table_info:
                indexes_info = await self._get_table_indexes(table)
                table_info += f"\n{indexes_info}\n"
            if self._sample_rows_in_table_info:
                sample_rows_info = await self._get_sample_rows(table)
                table_info += f"\n{sample_rows_info}\n"
            if has_extra_info:
                table_info += "*/"
            tables[table.name] = table_info

        return tables
