"""正确修复 tenant 模块的模型文件"""

from pathlib import Path

def add_table_comment(file_path: str, comment: str, has_table_args: bool = False):
    """添加表级 comment"""
    path = Path(file_path)
    content = path.read_text(encoding='utf-8')
    
    if '__table_args__' in content:
        # 已有 __table_args__，在最后添加 comment 字典
        if '{"comment":' in content or "{'comment':" in content:
            print(f'Skip {file_path} - already has comment')
            return
        
        # 找到 __table_args__ 的结束位置
        lines = content.split('\n')
        table_args_start = -1
        table_args_end = -1
        paren_count = 0
        in_table_args = False
        
        for i, line in enumerate(lines):
            if '__table_args__' in line:
                table_args_start = i
                in_table_args = True
                paren_count += line.count('(') - line.count(')')
            elif in_table_args:
                paren_count += line.count('(') - line.count(')')
                if paren_count == 0:
                    table_args_end = i
                    break
        
        if table_args_end >= 0:
            # 在 ) 之前添加 comment
            new_lines = lines[:table_args_end]
            # 检查最后一行是否只有 )
            if new_lines[-1].strip() == ')':
                new_lines[-1] = '        {"comment": "' + comment + '"},'
                new_lines.append('    )')
            else:
                new_lines.append('        {"comment": "' + comment + '"},')
                new_lines.append('    )')
            new_lines.extend(lines[table_args_end+1:])
            new_content = '\n'.join(new_lines)
            path.write_text(new_content, encoding='utf-8')
            print(f'Added comment to {file_path}')
    else:
        # 没有 __table_args__，在类最后添加
        lines = content.rstrip().split('\n')
        new_lines = lines.copy()
        new_lines.append('')
        new_lines.append('    __table_args__ = (')
        new_lines.append('        {"comment": "' + comment + '"},')
        new_lines.append('    )')
        new_content = '\n'.join(new_lines) + '\n'
        path.write_text(new_content, encoding='utf-8')
        print(f'Added __table_args__ to {file_path}')

def main():
    base_path = Path(__file__).parent.parent
    
    # 需要添加表级 comment 的文件
    files_to_fix = [
        ('src/tenant/models/module.py', '模块定义表'),
        ('src/tenant/models/module_permission.py', '模块权限表'),
        ('src/tenant/models/module_role.py', '模块角色表'),
        ('src/tenant/models/tenant_module.py', '租户模块分配表'),
    ]
    
    for file_path, comment in files_to_fix:
        path = base_path / file_path
        if path.exists():
            add_table_comment(str(path), comment)
        else:
            print(f'File not found: {file_path}')
    
    print('Done!')

if __name__ == '__main__':
    main()

