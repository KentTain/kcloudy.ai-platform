"""
为 tenant 模块的模型文件添加表级 comment
"""

import pathlib
from pathlib import Path
import re

# 定义需要修改的文件和对应的表描述
files_to_modify = {
    'src/tenant/models/cache_config.py': '缓存配置表',
    'src/tenant/models/database_config.py': '数据库配置表',
    'src/tenant/models/module_menu.py': '模块菜单定义表',
    'src/tenant/models/module_menu_permission.py': '模块菜单-权限关联表',
    'src/tenant/models/module_role_permission.py': '模块角色-权限关联表',
    'src/tenant/models/pubsub_config.py': '发布订阅配置表',
    'src/tenant/models/queue_config.py': '队列配置表',
    'src/tenant/models/storage_config.py': '存储配置表',
    'src/tenant/models/tenant_config.py': '租户配置表',
    'src/tenant/models/tenant_business_config.py': '租户业务配置表',
}

def main():
    base_path = Path(__file__).parent.parent
    
    for file_path, comment in files_to_modify.items():
        path = base_path / file_path
        if not path.exists():
            print(f'File not found: {file_path}')
            continue
        
        content = path.read_text(encoding='utf-8')
        
        # 检查是否已经有 comment
        if '{"comment":' in content or "{'comment':" in content:
            print(f'Skip {file_path} - already has comment')
            continue
        
        # 查找 __table_args__ 并添加 comment
        # 匹配 __table_args__ = (...) 的内容
        pattern = r'(__table_args__\s*=\s*\([^)]+\))(\s*)'
        
        def add_comment(match):
            table_args = match.group(1)
            trailing = match.group(2)
            # 在 ) 之前添加 comment 字典
            last_paren = table_args.rfind(')')
            before_paren = table_args[:last_paren]
            # 添加 comment
            new_table_args = before_paren.rstrip() + ',\n        {"comment": "' + comment + '"},\n    )'
            return new_table_args + trailing
        
        new_content = re.sub(pattern, add_comment, content, count=1)
        
        if new_content != content:
            path.write_text(new_content, encoding='utf-8')
            print(f'Updated {file_path}')
        else:
            print(f'No changes to {file_path}')
    
    print('Done!')

if __name__ == '__main__':
    main()

