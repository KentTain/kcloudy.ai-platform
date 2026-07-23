"""插件包存储记录模型"""

from sqlalchemy import BigInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from framework.database.mixins.active_record import ActiveRecordMixin
from tenant.models import BaseModel


class TenantPluginPackage(BaseModel, ActiveRecordMixin):
    """插件包存储记录模型

    存储从远程市场下载的插件包文件记录，包括存储路径、校验和等信息。
    """

    __tablename__ = "plugin_packages"

    plugin_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
        comment="插件ID：author/name",
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="版本号",
    )
    marketplace_id: Mapped[str | None] = mapped_column(
        String(36),
        index=True,
        comment="来源市场ID",
    )
    storage_path: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        comment="MinIO 存储路径",
    )
    file_size: Mapped[int | None] = mapped_column(
        BigInteger,
        comment="文件大小（字节）",
    )
    checksum: Mapped[str | None] = mapped_column(
        String(128),
        comment="SHA256 校验和",
    )
    manifest: Mapped[dict | None] = mapped_column(
        JSONB,
        comment="解析后的 manifest",
    )

    __table_args__ = (
        UniqueConstraint(
            "plugin_id", "version", "marketplace_id",
            name="uq_plugin_packages_plugin_version_marketplace"
        ),
        {"comment": "插件包存储记录表"},
    )
