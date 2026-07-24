"""文档库默认种子数据"""

import logging

from sqlalchemy import select

logger = logging.getLogger(__name__)


async def run(*, dry_run: bool = False) -> int:
    """创建文档库默认种子数据

    初始化默认元数据字段定义。

    Args:
        dry_run: 仅预览，不写入数据库

    Returns:
        初始化的记录数
    """
    from document.models import LibraryMetadataField
    from framework.database.core.engine import get_session

    created = 0

    async with get_session() as session:
        # 默认元数据字段定义
        default_fields = [
            {
                "name": "分类",
                "field_type": "enum",
                "is_required": False,
                "enum_values": ["技术文档", "产品文档", "设计文档", "其他"],
                "sort_order": 1,
            },
            {
                "name": "优先级",
                "field_type": "enum",
                "is_required": False,
                "enum_values": ["高", "中", "低"],
                "sort_order": 2,
            },
            {
                "name": "版本",
                "field_type": "string",
                "is_required": False,
                "sort_order": 3,
            },
        ]

        for field_def in default_fields:
            stmt = select(LibraryMetadataField).where(
                LibraryMetadataField.name == field_def["name"],
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing is None:
                if not dry_run:
                    field = LibraryMetadataField(
                        name=field_def["name"],
                        field_type=field_def["field_type"],
                        is_required=field_def.get("is_required", False),
                        enum_values=field_def.get("enum_values"),
                        sort_order=field_def.get("sort_order", 0),
                    )
                    session.add(field)
                created += 1
                logger.info(f"创建元数据字段: {field_def['name']}")

        if not dry_run and created > 0:
            await session.commit()

    return created
