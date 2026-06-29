"""强制修复 __table_args__ 的格式 - 将字典移动到元组最后"""

from pathlib import Path
import re

files_to_fix = [
    'src/tenant/models/module.py',
    'src/tenant/models/module_permission.py',
    'src/tenant/models/module_role.py',
    'src/tenant/models/tenant_module.py',
]

def fix_table_args(content: str) -> str:
    """修复 __table_args__ 的格式，确保字典是元组的最后一个元素"""
    
    pattern = r'(__table_args__\s*=\s*\()([\s\S]*?)(\)\s*\n)'
    
    def fix_match(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        
        # 提取 comment 字典
        comment_match = re.search(r'\{"comment":\s*"([^"]+)"\}', body)
        if not comment_match:
            return match.group(0)
        
        comment = comment_match.group(0)
        
        # 移除原来位置的 comment（包括前后的逗号和空格）
        body = re.sub(r'\s*' + re.escape(comment) + r',?\s*', '\n        ', body)
        
        # 提取所有约束和索引
        items = []
        for line in body.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('{') and not line.endswith('},'):
                # 确保每个项以逗号结尾
                if line.endswith(','):
                    items.append(line)
                elif line.endswith(')'):
                    items.append(line + ',')
                else:
                    items.append(line + ',')
        
        # 重新构建 __table_args__
        new_body = '\n'
        for item in items:
            new_body += '        ' + item + '\n'
        new_body += '        ' + comment + ',\n    '
        
        return prefix + new_body + suffix
    
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

