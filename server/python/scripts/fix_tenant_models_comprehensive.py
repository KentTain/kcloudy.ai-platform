"""全面修复 tenant 模型：添加 EnumType 和表级 comment"""

from pathlib import Path
import re

def process_tenant_py():
    """处理 tenant.py - 添加 EnumType 和 comment"""
    path = Path('src/tenant/models/tenant.py')
    content = path.read_text(encoding='utf-8')
    
    # 添加 EnumType 导入
    if 'from framework.database.types.enum import EnumType' not in content:
        content = content.replace(
            'from tenant.models.enums import TenantStatus',
            'from tenant.models.enums import TenantStatus\nfrom framework.database.types.enum import EnumType'
        )
    
    # 修改 status 字段为 EnumType
    content = re.sub(
        r'status: Mapped\[str\] = mapped_column\(\s*String\(20\), nullable=False, default=TenantStatus\.ACTIVE, comment="[^"]+"\)',
        'status: Mapped[str] = mapped_column(\n        EnumType(enum_class=TenantStatus, length=20), nullable=False, default=TenantStatus.ACTIVE, comment="状态"\n    )',
        content
    )
    
    # 添加表级 comment（在 __table_args__ 最后添加字典）
    content = re.sub(
        r'__table_args__\s*=\s*\(\s*Index\("ix_tenants_code", "code"\),\s*Index\("ix_tenants_status", "status"\),\s*\)',
        '__table_args__ = (\n        Index("ix_tenants_code", "code"),\n        Index("ix_tenants_status", "status"),\n        {"comment": "租户表"},\n    )',
        content
    )
    
    path.write_text(content, encoding='utf-8')
    print(f'Processed {path}')

def process_tenant_admin_py():
    """处理 tenant_admin.py - 添加 EnumType 和 comment"""
    path = Path('src/tenant/models/tenant_admin.py')
    content = path.read_text(encoding='utf-8')
    
    # 添加 EnumType 和枚举导入
    if 'from tenant.models.enums import TenantAdminRole' not in content:
        content = content.replace(
            'from tenant.models import BaseModel',
            'from tenant.models import BaseModel\nfrom tenant.models.enums import TenantAdminRole\nfrom framework.database.types.enum import EnumType'
        )
    
    # 修改 role 字段为 EnumType
    content = re.sub(
        r'role: Mapped\[str\] = mapped_column\(\s*String\(50\), nullable=False, default="ordinaryAdmin", comment="[^"]+"\)',
        'role: Mapped[str] = mapped_column(\n        EnumType(enum_class=TenantAdminRole, length=20), nullable=False, default=TenantAdminRole.ORDINARY_ADMIN, comment="角色"\n    )',
        content
    )
    
    # 添加表级 comment
    content = re.sub(
        r'__table_args__\s*=\s*\(Index\("ix_tenant_admins_username", "username"\),\)',
        '__table_args__ = (\n        Index("ix_tenant_admins_username", "username"),\n        {"comment": "租户管理员表"},\n    )',
        content
    )
    
    path.write_text(content, encoding='utf-8')
    print(f'Processed {path}')

def process_plugin_installation_py():
    """处理 plugin_installation.py - 添加 EnumType 和 comment"""
    path = Path('src/tenant/models/plugin_installation.py')
    content = path.read_text(encoding='utf-8')
    
    # 添加 EnumType 和枚举导入
    if 'from tenant.models.enums import PluginInstallationStatus, PluginInstallType' not in content:
        content = content.replace(
            'from tenant.models import BaseModel',
            'from tenant.models import BaseModel\nfrom tenant.models.enums import PluginInstallationStatus, PluginInstallType\nfrom framework.database.types.enum import EnumType'
        )
    
    # 修改 status 字段为 EnumType
    content = re.sub(
        r'status: Mapped\[str\] = mapped_column\(\s*String\(16\),\s*nullable=False,\s*default="PENDING",\s*comment="[^"]+"\)',
        'status: Mapped[str] = mapped_column(\n        EnumType(enum_class=PluginInstallationStatus, length=16),\n        nullable=False,\n        default=PluginInstallationStatus.PENDING,\n        comment="状态",\n    )',
        content
    )
    
    # 修改 plugin_type 字段为 EnumType
    content = re.sub(
        r'plugin_type: Mapped\[str \| None\] = mapped_column\(\s*String\(16\),\s*nullable=True,\s*comment="[^"]+"\)',
        'plugin_type: Mapped[str | None] = mapped_column(\n        EnumType(enum_class=PluginInstallType, length=16),\n        nullable=True,\n        comment="插件类型",\n    )',
        content
    )
    
    # 添加表级 comment
    content = re.sub(
        r'__table_args__\s*=\s*\(\s*UniqueConstraint\(\s*"tenant_id", "plugin_id", name="ix_plugin_installations_tenant_plugin"\s*\),\s*\)',
        '__table_args__ = (\n        UniqueConstraint(\n            "tenant_id", "plugin_id", name="ix_plugin_installations_tenant_plugin"\n        ),\n        {"comment": "插件安装记录表"},\n    )',
        content
    )
    
    path.write_text(content, encoding='utf-8')
    print(f'Processed {path}')

def process_tenant_business_config_py():
    """处理 tenant_business_config.py - 添加表级 comment"""
    path = Path('src/tenant/models/tenant_business_config.py')
    content = path.read_text(encoding='utf-8')
    
    # 添加表级 comment
    if '__table_args__' not in content:
        content = content.rstrip() + '\n\n    __table_args__ = (\n        {"comment": "租户业务配置表"},\n    )\n'
        path.write_text(content, encoding='utf-8')
        print(f'Processed {path}')
    else:
        print(f'Skip {path} - already has __table_args__')

def main():
    base_path = Path(__file__).parent.parent
    import os
    os.chdir(base_path)
    
    process_tenant_py()
    process_tenant_admin_py()
    process_plugin_installation_py()
    process_tenant_business_config_py()
    
    print('Done!')

if __name__ == '__main__':
    main()

