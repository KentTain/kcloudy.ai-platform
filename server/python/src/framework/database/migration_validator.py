"""
启动时数据库迁移验证器

在应用启动时自动检查并执行数据库迁移，确保表结构存在。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import text

from framework.utils.log_util import write_error, write_info, write_success, write_warning

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

_logger = logger.bind(name=__name__)


class StartupMigrationValidator:
    """启动时迁移验证器"""

    def __init__(self, src_path: Path, auto_migrate: bool = False):
        """
        初始化迁移验证器

        Args:
            src_path: 源码路径（用于定位模块迁移目录）
            auto_migrate: 是否自动运行缺失的迁移
        """
        self.src_path = src_path
        self.auto_migrate = auto_migrate

    async def validate_and_migrate(self, session: AsyncSession) -> dict:
        """
        验证数据库迁移状态，根据配置决定是否自动运行迁移

        Args:
            session: 数据库会话

        Returns:
            验证结果字典，包含各模块的迁移状态
        """
        from framework.module import get_registry

        registry = get_registry()
        modules = registry.get_all_modules()

        results = {
            "total_modules": len(modules),
            "modules": {},
            "all_migrated": True,
            "need_migration": [],
            "auto_migrated": [],
        }

        for module in modules:
            module_name = module.name
            module_schema = module.schema

            try:
                # 检查 schema 是否存在
                schema_exists = await self._check_schema_exists(
                    session, module_schema
                )

                if not schema_exists:
                    if self.auto_migrate:
                        # 自动创建 schema
                        await session.execute(
                            text(f"CREATE SCHEMA IF NOT EXISTS {module_schema}")
                        )
                        await session.commit()
                        write_info(f"[{module_name}] 已自动创建 Schema: {module_schema}")
                    else:
                        write_warning(f"[{module_name}] Schema 不存在，需要运行迁移")
                        results["modules"][module_name] = {
                            "status": "schema_missing",
                            "schema": module_schema,
                        }
                        results["all_migrated"] = False
                        results["need_migration"].append(module_name)
                        continue

                # 检查 alembic_version 表是否存在
                version_table_exists = await self._check_version_table_exists(
                    session, module_schema
                )

                if not version_table_exists:
                    if self.auto_migrate:
                        # 自动运行迁移
                        write_info(f"[{module_name}] 自动执行数据库迁移...")
                        migrated = await self._run_module_migration(module_name)
                        if migrated:
                            results["modules"][module_name] = {
                                "status": "auto_migrated",
                                "schema": module_schema,
                            }
                            results["auto_migrated"].append(module_name)
                            write_success(f"[{module_name}] 自动迁移完成")
                        else:
                            results["modules"][module_name] = {
                                "status": "migration_failed",
                                "schema": module_schema,
                            }
                            results["all_migrated"] = False
                            results["need_migration"].append(module_name)
                    else:
                        write_warning(f"[{module_name}] 迁移版本表不存在，需要运行迁移")
                        results["modules"][module_name] = {
                            "status": "version_table_missing",
                            "schema": module_schema,
                        }
                        results["all_migrated"] = False
                        results["need_migration"].append(module_name)
                    continue

                # 检查当前版本
                current_version = await self._get_current_version(
                    session, module_schema
                )
                results["modules"][module_name] = {
                    "status": "up_to_date",
                    "schema": module_schema,
                    "version": current_version,
                }
                write_info(f"[{module_name}] 迁移版本: {current_version}")

            except Exception as e:
                _logger.exception(f"[{module_name}] 迁移验证失败: {e}")
                results["modules"][module_name] = {
                    "status": "error",
                    "error": str(e),
                }
                results["all_migrated"] = False
                results["need_migration"].append(module_name)

        # 输出迁移状态汇总
        if results["auto_migrated"]:
            write_success(f"自动迁移完成: {results['auto_migrated']}")

        if results["need_migration"]:
            if self.auto_migrate:
                write_error(f"自动迁移失败: {results['need_migration']}")
            else:
                write_warning(
                    f"检测到 {len(results['need_migration'])} 个模块需要运行迁移: "
                    f"{results['need_migration']}"
                )
                write_info(
                    "请运行: uv run python manage.py db migrate --all --yes"
                )
                write_info(
                    "或在配置中设置 sqlalchemy.auto_migrate: true 自动运行迁移"
                )

        return results

    async def _check_schema_exists(
        self, session: AsyncSession, schema: str
    ) -> bool:
        """检查 schema 是否存在"""
        result = await session.execute(
            text(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name = :schema"
            ),
            {"schema": schema},
        )
        return result.scalar() is not None

    async def _check_version_table_exists(
        self, session: AsyncSession, schema: str
    ) -> bool:
        """检查 alembic_version 表是否存在"""
        result = await session.execute(
            text(
                """
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = :schema AND table_name = 'alembic_version'
                """
            ),
            {"schema": schema},
        )
        return result.scalar() is not None

    async def _get_current_version(
        self, session: AsyncSession, schema: str
    ) -> str | None:
        """获取当前迁移版本"""
        try:
            result = await session.execute(
                text(f"SELECT version_num FROM {schema}.alembic_version")
            )
            return result.scalar()
        except Exception:
            return None

    async def _run_module_migration(self, module_name: str) -> bool:
        """
        运行模块的数据库迁移

        Args:
            module_name: 模块名称

        Returns:
            是否成功
        """
        import concurrent.futures

        def run_migration():
            """在线程中运行迁移"""
            try:
                from alembic import command
                from alembic.config import Config

                from demo.configs import settings

                module_dir = self.src_path / module_name / "migrations"
                config_file = module_dir / "alembic.ini"

                # 创建配置
                if config_file.exists():
                    config = Config(str(config_file))
                else:
                    global_config_file = (
                        Path(__file__).parent.parent.parent / "alembic.ini"
                    )
                    config = Config(str(global_config_file))

                config.set_main_option("script_location", str(module_dir))
                config.set_main_option(
                    "version_locations", str(module_dir / "versions")
                )
                config.set_main_option(
                    "sqlalchemy.url", str(settings.sqlalchemy.url)
                )

                # 运行迁移
                command.upgrade(config, "head")
                return True

            except Exception as e:
                _logger.exception(f"[{module_name}] 迁移执行失败: {e}")
                return False

        try:
            # 在线程池中运行同步的 alembic 命令
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as executor:
                success = await loop.run_in_executor(executor, run_migration)

            if success:
                write_success(f"[{module_name}] 迁移执行成功")
            else:
                write_error(f"[{module_name}] 迁移执行失败")

            return success

        except Exception as e:
            _logger.exception(f"[{module_name}] 迁移执行失败: {e}")
            write_error(f"[{module_name}] 迁移执行失败: {e}")
            return False

    async def verify_data_integrity(self, session: AsyncSession) -> dict:
        """
        验证数据完整性

        检查关键数据是否存在

        Args:
            session: 数据库会话

        Returns:
            验证结果
        """
        checks = {
            "tenant.modules": "SELECT COUNT(*) FROM tenant.modules",
            "tenant.tenants": "SELECT COUNT(*) FROM tenant.tenants",
            "tenant.module_roles": "SELECT COUNT(*) FROM tenant.module_roles WHERE module_id IS NULL",
            "tenant.module_menus": "SELECT COUNT(*) FROM tenant.module_menus",
            "iam.roles": "SELECT COUNT(*) FROM iam.roles",
            "iam.menus": "SELECT COUNT(*) FROM iam.menus",
            "iam.users": "SELECT COUNT(*) FROM iam.users",
        }

        results = {}
        all_passed = True

        for name, query in checks.items():
            try:
                result = await session.execute(text(query))
                count = result.scalar()
                passed = count > 0
                results[name] = {"count": count, "passed": passed}
                if not passed:
                    all_passed = False
                    write_warning(f"数据验证失败: {name} (count=0)")
            except Exception as e:
                results[name] = {"error": str(e), "passed": False}
                all_passed = False
                write_error(f"数据验证错误: {name} - {e}")

        results["all_passed"] = all_passed
        return results
