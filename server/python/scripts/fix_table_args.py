"""修复 __table_args__ 的格式"""

from pathlib import Path
import re

files_to_fix = [
    'src/tenant/models/cache_config.py',
    'src/tenant/models/database_config.py',
    'src/tenant/models/module_menu.py',
    'src/tenant/models/module_menu_permission.py',
    'src/tenant/models/module_role_permission.py',
    'src/tenant/models/pubsub_config.py',
    'src/tenant/models/queue_config.py',
    'src/tenant/models/storage_config.py',
    'src/tenant/models/tenant_config.py',
    'src/tenant/models/tenant_business_config.py',
]

def fix_table_args(content: str) -> str:
    """修复 __table_args__ 的格式，确保字典是元组的最后一个元素"""
    
    # 匹配 __table_args__ = (...) 的完整内容
    pattern = r'(__table_args__\s*=\s*\()([\s\S]*?)(\)\s*\n)'
    
    def fix_match(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        
        # 提取 comment
        comment_match = re.search(r'\{"comment":\s*"([^"]+)"\}', body)
        if not comment_match:
            return match.group(0)
        
        comment = comment_match.group(0)
        
        # 移除原来位置的 comment
        body = re.sub(r',?\s*' + re.escape(comment) + r',?\s*', '', body)
        
        # 清理多余的逗号
        body = re.sub(r',\s*,', ',', body)
        body = re.sub(r',\s*\)', '\n    )', body)
        
        # 确保 body 以换行和括号结束
        body = body.rstrip()
        if body.endswith(','):
            body = body[:-1]
        
        # 在最后添加 comment 字典（必须在元组的最后）
        body = body + ',\n        ' + comment + ',\n    '

        return prefix + body + suffix
    
    return re.sub(pattern, fix_match, content)

def main():
    base_path = Path(__file__).parent.parent
    
    for file_path in files_to_fix:
        path = base_path / file_path
        if not path.exists():
            print(f'File not found: {file_path}')
            continue
        
        content = path.read_text(encoding='utf-8')
        new_content = fix_table_args(content)
        
        if new_content != content:
            path.write_text(new_content, encoding='utf-8')
            print(f'Fixed {file_path}')
        else:
            print(f'No changes to {file_path}')
    
    print('Done!')

if __name__ == '__main__':
    main()
files_to_fix = [
    'src/tenant/models/cache_config.py',
    'src/tenant/models/database_config.py',
    'src/tenant/models/module.py',
    'src/tenant/models/module_permission.py',
    'src/tenant/models/module_role.py',
    'src/tenant/models/tenant_module.py',
    'src/tenant/models/module_menu.py',
    'src/tenant/models/module_menu_permission.py',
    'src/tenant/models/module_role_permission.py',
    'src/tenant/models/pubsub_config.py',
    'src/tenant/models/queue_config.py',
    'src/tenant/models/storage_config.py',
    'src/tenant/models/tenant_config.py',
    'src/tenant/models/tenant_business_config.py',
]

