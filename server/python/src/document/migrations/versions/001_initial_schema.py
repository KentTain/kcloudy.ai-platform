"""Document 模块初始数据库模式

Revision ID: 001_document_initial
Revises:
Create Date: 2026-07-24

创建 document schema 下的 15 张表：
1.  library             - 文档库
2.  library_member      - 文档库成员
3.  folder              - 文件夹（树形）
4.  document            - 文档
5.  document_version    - 文档版本
6.  library_role        - 权限组
7.  library_role_member - 权限组成员
8.  resource_acl        - 资源访问控制
9.  tag                 - 标签
10. tag_group           - 标签分组
11. persona             - 人设
12. library_metadata_field - 元数据字段定义
13. resource_metadata   - 资源元数据值
14. recycle_item        - 回收站
15. config_item         - 文档库配置

关键约定：
- 所有表使用 schema="document"
- 所有表有 id (String PK)、tenant_id、created_at、updated_at、created_by、updated_by
- 跨模块引用（library_id、user_id 等）使用 String 列，不加 ForeignKey
- folder 的 parent_id 无 ForeignKey（TreeNodeMixin 虚拟根节点设计）

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_document_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# 模块 schema
MODULE_SCHEMA = "document"


def upgrade() -> None:
    # 创建 document schema
    op.execute(f"CREATE SCHEMA IF NOT EXISTS {MODULE_SCHEMA}")

    # ==================== 1. library - 文档库 ====================
    op.create_table(
        "library",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("type", sa.String(20), nullable=False, comment="文档库类型"),
        sa.Column("code", sa.String(64), nullable=False, comment="文档库编码"),
        sa.Column("name", sa.String(128), nullable=False, comment="文档库名称"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("icon", sa.String(64), nullable=True, comment="图标"),
        sa.Column("owner_id", sa.String(36), nullable=False, comment="所有者用户ID"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default="true", comment="是否启用"),
        sa.Column("allow_submit_to_kb", sa.Boolean, nullable=False, server_default="true", comment="是否允许提交入库"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_library_tenant_id", "library", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_type", "library", ["type"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_owner_id", "library", ["owner_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_code", "library", ["code"], schema=MODULE_SCHEMA)

    # ==================== 2. library_member - 文档库成员 ====================
    op.create_table(
        "library_member",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("user_id", sa.String(36), nullable=False, comment="用户ID"),
        sa.Column("user_name", sa.String(256), nullable=False, comment="用户名"),
        sa.Column("role", sa.String(20), nullable=False, comment="成员角色"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="成员状态"),
        sa.Column("remarks", sa.String(256), nullable=True, comment="备注"),
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_library_member_library_id", "library_member", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_member_user_id", "library_member", ["user_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_member_role", "library_member", ["role"], schema=MODULE_SCHEMA)

    # ==================== 3. folder - 文件夹（树形，TreeNodeMixin） ====================
    op.create_table(
        "folder",
        sa.Column("id", sa.String(36), primary_key=True),
        # TreeNodeMixin 字段（parent_id 无 ForeignKey）
        sa.Column("parent_id", sa.String(36), nullable=False, server_default="root", comment="父节点ID"),
        sa.Column("tree_leaf", sa.Boolean, nullable=False, server_default="true", comment="是否叶子节点"),
        sa.Column("tree_level", sa.Integer, nullable=False, server_default="0", comment="树层级"),
        sa.Column("tree_sort", sa.Integer, nullable=False, server_default="0", comment="排序号"),
        sa.Column("tree_sorts", sa.String(512), nullable=False, server_default="", comment="排序路径"),
        sa.Column("tree_names", sa.String(512), nullable=False, server_default="", comment="名称路径"),
        sa.Column("parent_ids", sa.String(1024), nullable=False, server_default="root,", comment="父ID路径"),
        # 业务字段
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("name", sa.String(256), nullable=False, comment="文件夹名称"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="active", comment="生命周期状态"),
        sa.Column("acl_inherit_enabled", sa.Boolean, nullable=False, server_default="true", comment="是否启用权限继承"),
        sa.Column("is_sensitive", sa.Boolean, nullable=False, server_default="false", comment="是否敏感"),
        sa.Column("doc_count", sa.Integer, nullable=False, server_default="0", comment="文档数"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_folder_library_id", "folder", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_folder_lifecycle_status", "folder", ["lifecycle_status"], schema=MODULE_SCHEMA)
    op.create_index("ix_folder_parent_id", "folder", ["parent_id"], schema=MODULE_SCHEMA)

    # ==================== 4. document - 文档 ====================
    op.create_table(
        "document",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("folder_id", sa.String(36), nullable=True, comment="文件夹ID（空为根目录）"),
        sa.Column("owner_id", sa.String(36), nullable=False, comment="所有者用户ID"),
        sa.Column("storage_key", sa.String(512), nullable=False, comment="MinIO 存储键"),
        sa.Column("name", sa.String(256), nullable=False, comment="文档名称"),
        sa.Column("document_type", sa.String(20), nullable=False, comment="文档类型"),
        sa.Column("lifecycle_status", sa.String(20), nullable=False, server_default="uploading", comment="生命周期状态"),
        sa.Column("processing_status", sa.String(20), nullable=False, server_default="pending_parse", comment="处理状态"),
        sa.Column("acl_inherit_enabled", sa.Boolean, nullable=False, server_default="true", comment="是否启用权限继承"),
        sa.Column("file_size", sa.Integer, nullable=False, server_default="0", comment="文件大小（字节）"),
        sa.Column("mime_type", sa.String(128), nullable=True, comment="MIME 类型"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("meta_data", postgresql.JSONB, nullable=True, comment="元数据"),
        sa.Column("task_id", sa.String(36), nullable=True, comment="切片索引任务ID"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_document_library_id", "document", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_document_folder_id", "document", ["folder_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_document_lifecycle_status", "document", ["lifecycle_status"], schema=MODULE_SCHEMA)

    # ==================== 5. document_version - 文档版本 ====================
    op.create_table(
        "document_version",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_id", sa.String(36), nullable=False, comment="文档ID"),
        sa.Column("version_no", sa.Integer, nullable=False, comment="版本号"),
        sa.Column("storage_key", sa.String(512), nullable=False, comment="MinIO 存储键"),
        sa.Column("file_size", sa.Integer, nullable=False, comment="文件大小"),
        sa.Column("uploaded_by", sa.String(36), nullable=False, comment="上传人ID"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_document_version_document_id", "document_version", ["document_id"], schema=MODULE_SCHEMA)

    # ==================== 6. library_role - 权限组 ====================
    op.create_table(
        "library_role",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("role_kind", sa.String(20), nullable=False, comment="权限组类型"),
        sa.Column("code", sa.String(64), nullable=False, comment="权限组编码"),
        sa.Column("name", sa.String(128), nullable=False, comment="权限组名称"),
        sa.Column("description", sa.String(512), nullable=True, comment="描述"),
        sa.Column("system_builtin", sa.Boolean, nullable=False, server_default="false", comment="是否系统内置"),
        sa.Column("permissions", postgresql.JSONB, nullable=True, comment="权限定义（动作->等级）"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_library_role_library_id", "library_role", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_role_kind", "library_role", ["role_kind"], schema=MODULE_SCHEMA)

    # ==================== 7. library_role_member - 权限组成员 ====================
    op.create_table(
        "library_role_member",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("role_id", sa.String(36), nullable=False, comment="权限组ID"),
        sa.Column("user_id", sa.String(36), nullable=False, comment="用户ID"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_library_role_member_library_id", "library_role_member", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_role_member_role_id", "library_role_member", ["role_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_library_role_member_user_id", "library_role_member", ["user_id"], schema=MODULE_SCHEMA)

    # ==================== 8. resource_acl - 资源访问控制 ====================
    op.create_table(
        "resource_acl",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("resource_type", sa.String(20), nullable=False, comment="资源类型"),
        sa.Column("resource_id", sa.String(36), nullable=False, comment="资源ID"),
        sa.Column("subject_id", sa.String(36), nullable=False, comment="主体ID（用户ID/角色ID）"),
        sa.Column("subject_type", sa.String(20), nullable=False, server_default="user", comment="主体类型"),
        sa.Column("action", sa.String(64), nullable=False, comment="动作（read/preview/download/edit）"),
        sa.Column("effect", sa.String(20), nullable=False, comment="效果"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0", comment="优先级"),
        sa.Column("inherited_from_resource_id", sa.String(36), nullable=True, comment="继承来源资源ID"),
        sa.Column("condition_json", postgresql.JSONB, nullable=True, comment="条件"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_resource_acl_library_id", "resource_acl", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_resource_acl_resource", "resource_acl", ["resource_type", "resource_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_resource_acl_subject", "resource_acl", ["subject_id"], schema=MODULE_SCHEMA)

    # ==================== 9. tag - 标签 ====================
    op.create_table(
        "tag",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, comment="标签名称"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("color", sa.String(32), nullable=True, comment="颜色"),
        sa.Column("group_id", sa.String(36), nullable=True, comment="分组ID"),
        sa.Column("persona_id", sa.String(36), nullable=True, comment="引用人设ID"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active", comment="状态"),
        sa.Column("doc_count", sa.Integer, nullable=False, server_default="0", comment="引用文档数"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tag_tenant_id", "tag", ["tenant_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_tag_group_id", "tag", ["group_id"], schema=MODULE_SCHEMA)

    # ==================== 10. tag_group - 标签分组 ====================
    op.create_table(
        "tag_group",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, comment="分组名称"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_tag_group_tenant_id", "tag_group", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 11. persona - 人设 ====================
    op.create_table(
        "persona",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(128), nullable=False, comment="人设名称"),
        sa.Column("role", sa.String(256), nullable=True, comment="角色定位"),
        sa.Column("instruction", sa.Text, nullable=False, comment="指令内容"),
        sa.Column("description", sa.Text, nullable=True, comment="描述"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_persona_tenant_id", "persona", ["tenant_id"], schema=MODULE_SCHEMA)

    # ==================== 12. library_metadata_field - 元数据字段定义 ====================
    op.create_table(
        "library_metadata_field",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("name", sa.String(128), nullable=False, comment="字段名称"),
        sa.Column("field_type", sa.String(20), nullable=False, comment="字段类型"),
        sa.Column("is_required", sa.Boolean, nullable=False, server_default="false", comment="是否必填"),
        sa.Column("enum_values", postgresql.JSONB, nullable=True, comment="枚举值列表"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0", comment="排序"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_library_metadata_field_library_id", "library_metadata_field", ["library_id"], schema=MODULE_SCHEMA)

    # ==================== 13. resource_metadata - 资源元数据值 ====================
    op.create_table(
        "resource_metadata",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("resource_type", sa.String(20), nullable=False, comment="资源类型（folder/document）"),
        sa.Column("resource_id", sa.String(36), nullable=False, comment="资源ID"),
        sa.Column("field_id", sa.String(36), nullable=False, comment="元数据字段ID"),
        sa.Column("field_name", sa.String(128), nullable=False, comment="字段名称（冗余）"),
        sa.Column("value", sa.String(1024), nullable=True, comment="元数据值"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_resource_metadata_resource", "resource_metadata", ["resource_type", "resource_id"], schema=MODULE_SCHEMA)

    # ==================== 14. recycle_item - 回收站 ====================
    op.create_table(
        "recycle_item",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="源文档库ID"),
        sa.Column("resource_type", sa.String(20), nullable=False, comment="资源类型"),
        sa.Column("resource_id", sa.String(36), nullable=False, comment="资源ID"),
        sa.Column("original_parent_id", sa.String(36), nullable=True, comment="原父资源ID"),
        sa.Column("original_path", sa.String(1024), nullable=True, comment="原路径"),
        sa.Column("deleted_by", sa.String(36), nullable=False, comment="删除人ID"),
        sa.Column("status", sa.String(20), nullable=False, server_default="in_recycle", comment="状态"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True, comment="过期时间（自动清理）"),
        sa.Column("restored_by", sa.String(36), nullable=True, comment="恢复人ID"),
        sa.Column("restored_at", sa.DateTime(timezone=True), nullable=True, comment="恢复时间"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_recycle_item_library_id", "recycle_item", ["library_id"], schema=MODULE_SCHEMA)
    op.create_index("ix_recycle_item_status", "recycle_item", ["status"], schema=MODULE_SCHEMA)

    # ==================== 15. config_item - 文档库配置 ====================
    op.create_table(
        "config_item",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("library_id", sa.String(36), nullable=False, comment="文档库ID"),
        sa.Column("config_key", sa.String(128), nullable=False, comment="配置键"),
        sa.Column("config_value", postgresql.JSONB, nullable=True, comment="配置值"),
        # 公共字段
        sa.Column("tenant_id", sa.String(36), nullable=False, comment="租户ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="创建时间"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, comment="更新时间"),
        sa.Column("created_by", sa.String(36), nullable=True, comment="创建人"),
        sa.Column("updated_by", sa.String(36), nullable=True, comment="更新人"),
        schema=MODULE_SCHEMA,
    )
    op.create_index("ix_config_item_library_id", "config_item", ["library_id"], schema=MODULE_SCHEMA)
    op.create_unique_constraint("uq_config_item_library_key", "config_item", ["library_id", "config_key"], schema=MODULE_SCHEMA)


def downgrade() -> None:
    # 删除所有表和 schema（CASCADE 自动处理依赖顺序）
    op.execute(f"DROP SCHEMA IF EXISTS {MODULE_SCHEMA} CASCADE")
