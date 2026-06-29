"""为 tenant_business_config.py 添加表级 comment"""

from pathlib import Path

file_path = Path('src/tenant/models/tenant_business_config.py')
content = file_path.read_text(encoding='utf-8')

if '__table_args__' not in content:
    lines = content.rstrip().split('\n')
    last_field_end = -1
    for i in range(len(lines) - 1, -1, -1):
        if ')' in lines[i] and 'mapped_column' in ''.join(lines[max(0,i-3):i+1]):
            last_field_end = i
            break

    if last_field_end >= 0:
        new_lines = lines[:last_field_end+1]
        new_lines.append('')
        new_lines.append('    __table_args__ = (')
        new_lines.append('        {"comment": "租户业务配置表"},')
        new_lines.append('    )')
        new_content = '\n'.join(new_lines) + '\n'
        file_path.write_text(new_content, encoding='utf-8')
        print('Added __table_args__ to tenant_business_config.py')
    else:
        print('Could not find insertion point')
else:
    print('__table_args__ already exists')

