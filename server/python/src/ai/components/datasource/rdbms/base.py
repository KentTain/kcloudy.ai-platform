"""RDBMS 数据库基类

提供基于 SQLAlchemy 的异步数据库操作封装。
"""

from typing import Any
from collections.abc import Iterable
from urllib.parse import quote, quote_plus

import regex as re
import sqlparse
from langchain_community.utilities.sql_database import _format_index
from loguru import logger
from sqlalchemy import MetaData, Table, inspect, select, text
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.schema import CreateTable

from ai.components.datasource.interfaces import BaseConnect


_logger = logger.bind(name=__name__)


class RDBMSDatabase(BaseConnect):
    """SQLAlchemy 异步数据库包装器"""

    db_type: str = ""
    db_dialect: str = ""
    driver: str = ""
    default_db: list[str] = []

    def __init__(
        self,
        engine: AsyncEngine,
        schema: str | None = None,
        metadata: MetaData | None = None,
        ignore_tables: list[str] | None = None,
        include_tables: list[str] | None = None,
        sample_rows_in_table_info: int = 3,
        indexes_in_table_info: bool = False,
        custom_table_info: dict | None = None,
        view_support: bool = False,
    ):
        """
        创建异步数据库连接

        Args:
            engine: SQLAlchemy 异步引擎
            schema: 数据库 schema
            metadata: 元数据对象
            ignore_tables: 忽略的表列表
            include_tables: 包含的表列表
            sample_rows_in_table_info: 示例行数
            indexes_in_table_info: 是否包含索引信息
            custom_table_info: 自定义表信息
            view_support: 是否支持视图
        """
        self._engine = engine
        self._schema = schema
        if include_tables and ignore_tables:
            raise ValueError("Cannot specify both include_tables and ignore_tables")

        self._all_tables: set = set()
        self.view_support = view_support
        self._usable_tables: set = set()
        self._include_tables: set = set(include_tables or [])
        self._ignore_tables: set = set(ignore_tables or [])
        self._custom_table_info: dict = custom_table_info or {}
        self._indexes_in_table_info: bool = indexes_in_table_info
        self._sample_rows_in_table_info: int = sample_rows_in_table_info

        self._metadata = MetaData()

    @classmethod
    async def from_uri_db(
        cls,
        host: str,
        port: int,
        user: str,
        pwd: str,
        db_name: str,
        engine_args: dict | None = None,
        **kwargs: Any,
    ) -> "RDBMSDatabase":
        """
        从数据库 URI 构造 SQLAlchemy 异步引擎

        Args:
            host: 数据库主机
            port: 数据库端口
            user: 数据库用户
            pwd: 数据库密码
            db_name: 数据库名称
            engine_args: 其他引擎参数
        """
        db_url: str = (
            f"{cls.driver}://{quote(user)}:{quote_plus(pwd)}@{host}:{str(port)}/{db_name}"
        )
        return await cls.from_uri(db_url, engine_args, **kwargs)

    @classmethod
    async def from_uri(
        cls, database_uri: str, engine_args: dict | None = None, **kwargs: Any
    ) -> "RDBMSDatabase":
        """从 URI 构造 SQLAlchemy 异步引擎"""
        _engine_args = engine_args or {}
        async_engine = create_async_engine(database_uri, **_engine_args)
        instance = cls(async_engine, **kwargs)
        await instance._initialize()
        return instance

    async def _initialize(self):
        """异步初始化数据库连接"""
        async with self._engine.begin() as conn:
            # 反射数据库元数据
            await conn.run_sync(
                lambda sync_conn: self._metadata.reflect(bind=sync_conn)
            )
            # 同步表信息
            self._all_tables = await self._sync_tables_from_db()

    @property
    def dialect(self) -> str:
        """返回数据库方言字符串表示"""
        return self._engine.dialect.name

    async def get_show_create_table(self, table_name: str) -> str:
        """获取建表语句"""
        async with self._get_session() as session:
            cursor = await session.execute(text(f"SHOW CREATE TABLE {table_name}"))
            ans = cursor.fetchall()
            return ans[0][1] if ans else ""

    async def get_example_data(self, table_name: str, count: int = 3) -> list[dict]:
        """获取示例数据"""
        sql = f"SELECT * FROM {table_name} LIMIT {count}"
        field_names, result = await self.query_ex(sql)

        if not field_names or not result:
            return []

        return [dict(zip(field_names, row)) for row in result]

    async def get_table_names(self) -> Iterable[str]:
        """获取所有表名"""
        return self.get_usable_table_names()

    async def get_table_info(self, table_names: list[str] | None = None) -> str:
        """获取指定表的信息"""
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

        tables = []
        for table in meta_tables:
            if self._custom_table_info and table.name in self._custom_table_info:
                tables.append(self._custom_table_info[table.name])
                continue

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
            tables.append(table_info)

        final_str = "\n\n".join(tables)
        return final_str

    async def get_database_names(self) -> list[str]:
        """获取数据库名称列表"""
        async with self._get_session() as session:
            cursor = await session.execute(text("show databases;"))
            results = cursor.fetchall()
            return [d[0] for d in results if d[0] not in self.default_db]

    async def get_table_comments(self) -> list[tuple[str, str]]:
        """获取表注释"""
        db_name = await self.get_current_db_name()

        async with self._get_session() as session:
            cursor = await session.execute(
                text(
                    f"SELECT table_name, table_comment FROM information_schema.tables WHERE table_schema = '{db_name}'",
                ),
            )
            table_comments = cursor.fetchall()
            return [
                (table_comment[0], table_comment[1]) for table_comment in table_comments
            ]

    async def get_table_comment(self, table_name: str) -> dict:
        """获取表注释"""
        async with self._engine.begin() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            comment = await conn.run_sync(
                lambda sync_conn: inspector.get_table_comment(table_name)
            )
            return comment

    async def get_columns(self, table_name: str) -> list[dict]:
        """获取列信息"""
        async with self._engine.begin() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            columns = await conn.run_sync(
                lambda sync_conn: inspector.get_columns(table_name)
            )
            return columns

    async def get_column_comments(self, table_name: str) -> list[tuple[str, str]]:
        """获取指定表的列注释"""
        db_name = await self.get_current_db_name()
        async with self._get_session() as session:
            cursor = await session.execute(
                text(
                    f"SELECT column_name, column_comment FROM information_schema.columns "
                    f"WHERE table_schema = '{db_name}' and table_name = '{table_name}'",
                ),
            )
            column_comments = cursor.fetchall()
            return [
                (column_comment[0], column_comment[1])
                for column_comment in column_comments
            ]

    async def get_fields(self, table_name: str) -> list[tuple[str, str, str, str, str]]:
        """获取指定表的列字段"""
        async with self._get_session() as session:
            cursor = await session.execute(
                text(
                    f"SELECT COLUMN_NAME, COLUMN_TYPE, COLUMN_DEFAULT, IS_NULLABLE, COLUMN_COMMENT "
                    f"from information_schema.COLUMNS where table_name='{table_name}'",
                ),
            )
            fields = cursor.fetchall()
            return [
                (field[0], field[1], field[2], field[3], field[4]) for field in fields
            ]

    async def get_simple_fields(self, table_name: str) -> list[tuple]:
        """获取指定表的列字段"""
        return []

    async def get_indexes(self, table_name: str) -> list[dict]:
        """获取指定表的索引"""
        async with self._engine.begin() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            indexes = await conn.run_sync(
                lambda sync_conn: inspector.get_indexes(table_name)
            )
            return indexes

    async def get_index_info(self, table_names: list[str] | None = None) -> str:
        """获取指定表的索引信息"""
        if table_names is None:
            table_names = list(self.get_usable_table_names())

        index_infos = []
        for table_name in table_names:
            try:
                indexes = await self.get_indexes(table_name)
                if indexes:
                    indexes_formatted = "\n".join(map(_format_index, indexes))
                    index_infos.append(
                        f"Table {table_name} Indexes:\n{indexes_formatted}"
                    )
            except Exception as e:
                _logger.warning(f"获取表 {table_name} 索引信息失败: {e}")
                continue

        return "\n\n".join(index_infos)

    async def run(self, command: str, fetch: str = "all") -> list:
        """执行SQL命令并返回结果"""
        print("SQL:" + command)
        if not command or len(command) <= 0:
            return []

        parsed, ttype, sql_type, table_name = await self.__sql_parse(command)
        if ttype == sqlparse.tokens.DML:
            if sql_type == "SELECT":
                return await self._query(command, fetch)
            else:
                await self._write(command)
                select_sql = self.convert_sql_write_to_select(command)
                print(f"write result query:{select_sql}")
                if select_sql:
                    return await self._query(select_sql)
                return []
        else:
            print("DDL execution determines whether to enable through configuration ")
            async with self._get_session() as session:
                try:
                    cursor = await session.execute(text(command))
                    await session.commit()
                    if cursor.returns_rows:
                        result = cursor.fetchall()
                        field_names = tuple(cursor.keys())
                        result_list = list(result)
                        result_list.insert(0, field_names)
                        print("DDL Result:" + str(result_list))
                        if not result_list:
                            return await self.get_simple_fields(table_name)
                        return result_list
                    else:
                        return await self.get_simple_fields(table_name)
                except Exception as e:
                    await session.rollback()
                    raise e

    async def run_to_df(self, command: str, fetch: str = "all") -> Any:
        """执行SQL命令并返回DataFrame"""
        import pandas as pd

        result_lst = await self.run(command, fetch)
        if result_lst:
            columns = result_lst[0]
            values = result_lst[1:]
            return pd.DataFrame(values, columns=columns)
        return pd.DataFrame()

    ###########################################################################################################

    async def _sync_tables_from_db(self) -> set:
        """从数据库读取表信息"""
        async with self._engine.begin() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))

            _schema = None if self.db_type == "sqlite" else None

            table_names = await conn.run_sync(
                lambda sync_conn: inspector.get_table_names(schema=_schema)
            )

            view_names = []
            if self.view_support:
                view_names = await conn.run_sync(
                    lambda sync_conn: inspector.get_view_names(schema=_schema)
                )

            all_tables = set(table_names + view_names)
            return all_tables

    def get_usable_table_names(self) -> Iterable[str]:
        """获取可用的表名"""
        if self._include_tables:
            return self._include_tables
        return self._all_tables - self._ignore_tables

    def _get_session(self) -> AsyncSession:
        """获取异步会话"""
        return AsyncSession(self._engine)

    async def get_current_db_name(self) -> str:
        """获取当前数据库名称"""
        async with self._get_session() as session:
            result = await session.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            return db_name if db_name else ""

    async def table_simple_info(self):
        """获取表的简单信息"""
        db_name = await self.get_current_db_name()
        _sql = f"""
                select concat(table_name, "(" , group_concat(column_name), ")") as schema_info
                from information_schema.COLUMNS
                where table_schema="{db_name}"
                group by TABLE_NAME;
            """
        async with self._get_session() as session:
            cursor = await session.execute(text(_sql))
            results = cursor.fetchall()
            return results

    async def _get_sample_rows(self, table: Table) -> str:
        """获取示例行数据"""
        command = select(table).limit(self._sample_rows_in_table_info)

        columns_str = "\t".join([col.name for col in table.columns])

        try:
            async with self._engine.begin() as connection:
                sample_rows_result: CursorResult = await connection.execute(command)
                sample_rows = [[str(i)[:100] for i in ls] for ls in sample_rows_result]

            sample_rows_str = "\n".join(["\t".join(row) for row in sample_rows])

        except ProgrammingError:
            sample_rows_str = ""

        return f"{self._sample_rows_in_table_info} rows from {table.name} table:\n{columns_str}\n{sample_rows_str}"

    async def _get_table_indexes(self, table: Table) -> str:
        """获取表索引信息"""
        async with self._engine.begin() as conn:
            inspector = await conn.run_sync(lambda sync_conn: inspect(sync_conn))
            indexes = await conn.run_sync(
                lambda sync_conn: inspector.get_indexes(table.name)
            )
            indexes_formatted = "\n".join(map(_format_index, indexes))
            return f"Table Indexes:\n{indexes_formatted}"

    async def get_table_info_no_throw(
        self, table_names: list[str] | None = None
    ) -> str:
        """获取指定表的信息，不抛出异常"""
        try:
            return await self.get_table_info(table_names)
        except ValueError as e:
            return f"Error: {e}"

    async def _write(self, write_sql: str):
        """运行SQL写命令并返回结果"""
        print(f"Write[{write_sql}]")
        async with self._get_session() as session:
            try:
                result = await session.execute(text(write_sql))
                await session.commit()
                print(f"SQL[{write_sql}], result:{result.rowcount}")
                return result.rowcount
            except Exception as e:
                await session.rollback()
                raise e

    async def _query(self, query: str, fetch: str = "all"):
        """运行SQL查询并返回结果作为元组列表"""
        result = []

        print(f"Query[{query}]")
        if not query:
            return result

        async with self._get_session() as session:
            cursor = await session.execute(text(query))
            if cursor.returns_rows:
                if fetch == "all":
                    result = cursor.fetchall()
                elif fetch == "one":
                    result = [cursor.fetchone()]
                else:
                    raise ValueError("Fetch parameter must be either 'one' or 'all'")
                field_names = tuple(cursor.keys())
                result_list = list(result)
                result_list.insert(0, field_names)
                return result_list
            return result

    async def query_table_schema(self, table_name: str):
        """查询表结构"""
        sql = f"select * from {table_name} limit 1"
        return await self._query(sql)

    async def query_ex(self, query: str, fetch: str = "all"):
        """仅用于查询"""
        print(f"Query[{query}]")
        if not query:
            return [], None

        async with self._get_session() as session:
            cursor = await session.execute(text(query))
            if cursor.returns_rows:
                if fetch == "all":
                    result = cursor.fetchall()
                elif fetch == "one":
                    result = cursor.fetchone()
                else:
                    raise ValueError("Fetch parameter must be either 'one' or 'all'")
                field_names = list(cursor.keys())
                result_list = list(result) if result else []
                return field_names, result_list
            return [], None

    async def run_no_throw(self, command: str, fetch: str = "all") -> list:
        """执行SQL命令并返回结果，不抛出异常"""
        try:
            return await self.run(command, fetch)
        except SQLAlchemyError as e:
            return [f"Error: {e}"]

    async def get_database_list(self):
        """获取数据库列表"""
        async with self._get_session() as session:
            cursor = await session.execute(text("show databases;"))
            results = cursor.fetchall()
            return [d[0] for d in results if d[0] not in self.default_db]

    def convert_sql_write_to_select(self, write_sql: str):
        """SQL分类处理"""
        parts = write_sql.lower().split()
        cmd_type = parts[0]

        if cmd_type == "insert":
            match = re.match(
                r"insert into (\w+) \((.*?)\) values \((.*?)\)", write_sql.lower()
            )
            if match:
                table_name, columns, values = match.groups()
                columns_list = columns.split(",")
                values_list = values.split(",")
                where_clause = " AND ".join(
                    [
                        f"{col.strip()}={val.strip()}"
                        for col, val in zip(columns_list, values_list)
                    ],
                )
                return f"SELECT * FROM {table_name} WHERE {where_clause}"

        elif cmd_type == "delete":
            table_name = parts[2]
            return f"SELECT * FROM {table_name} "

        elif cmd_type == "update":
            table_name = parts[1]
            set_idx = parts.index("set")
            where_idx = parts.index("where")
            set_clause = parts[set_idx + 1 : where_idx][0].split("=")[0].strip()
            where_clause = " ".join(parts[where_idx + 1 :])
            return f"SELECT {set_clause} FROM {table_name} WHERE {where_clause}"
        else:
            raise ValueError(f"Unsupported SQL command type: {cmd_type}")

    async def __sql_parse(self, sql: str):
        """解析SQL语句"""
        sql = sql.strip()
        parsed = sqlparse.parse(sql)[0]
        sql_type = parsed.get_type()
        if sql_type == "CREATE":
            table_name = self._extract_table_name_from_ddl(parsed)
        else:
            table_name = parsed.get_name()

        first_token = parsed.token_first(skip_ws=True, skip_cm=False)
        ttype = first_token.ttype
        print(f"SQL:{sql}, ttype:{ttype}, sql_type:{sql_type}, table:{table_name}")
        return parsed, ttype, sql_type, table_name

    def _extract_table_name_from_ddl(self, parsed):
        """从CREATE TABLE语句中提取表名"""
        for token in parsed.tokens:
            if token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                return token.get_real_name()
        return None
