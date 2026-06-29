"""修复所有 tenant 模型文件的 __table_args__ 格式"""

from pathlib import Path
import re

def fix_table_args(content: str) -> str:
    """确保 __table_args__ 中的字典在元组最后"""
    
    pattern = r'(__table_args__\s*=\s*\()([\s\S]*?)(\)\s*\n)'
    
    def fix_match(match):
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        
        # 提取所有 comment 字典
        comments = re.findall(r'\{"comment":\s*"[^"]+"\}', body)
        if not comments:
            return match.group(0)
        
        comment = comments[0]
        
        # 移除所有 comment 字典
        body = re.sub(r',?\s*' + re.escape(comment) + r'\s*,?', '', body)
        
        # 清理多余的逗号
        body = re.sub(r',\s*,', ',', body)
        body = re.sub(r'\(\s*,', '(', body)
        body = re.sub(r',\s*\)', '\n    )', body)
        
        # 清理空行
        lines = [line for line in body.split('\n') if line.strip()]
        body = '\n        '.join(line.strip().rstrip(',') + ',' for line in lines if line.strip())
        
        # 确保 body 正确格式化
        if body:
            body = body.rstrip(',') + ',\n        ' + comment + ',\n    '
        else:
            body = '\n        ' + comment + ',\n    '
        
        return prefix + body + suffix
    
    return re.sub(pattern, fix_match, content)

def main():
    base_path = Path(__file__).parent.parent / 'src' / 'tenant' / 'models'
    
    # 需要修复的文件（字典位置不对）
    files_to_fix = [
        'tenant.py',
        'tenant_admin.py',
        'plugin_installation.py',
        'tenant_business_config.py',
    ]
    
    for file_name in files_to_fix:
        path = base_path / file_name
        if not path.exists():
            print(f'File not found: {file_name}')
            continue
        
        content = path.read_text(encoding='utf-8')
        new_content = fix_table_args(content)
        
        if new_content != content:
            path.write_text(new_content, encoding='utf-8')
            print(f'Fixed {file_name}')
        else:
            print(f'No changes to {file_name}')
    
    print('Done!')

if __name__ == '__main__':
    main()

