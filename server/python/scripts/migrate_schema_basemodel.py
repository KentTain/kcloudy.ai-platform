#!/usr/bin/env python3
"""
Schema BaseModel 迁移脚本

将业务模块的 Schema 从 pydantic.BaseModel 迁移到 framework.schemas.BaseModel。
"""

import argparse
import re
from pathlib import Path
from typing import NamedTuple


class MigrationResult(NamedTuple):
    """迁移结果"""

    file_path: Path
    changed: bool
    import_replaced: bool
    config_removed: bool
    lines_changed: int


def migrate_file(file_path: Path, dry_run: bool = False) -> MigrationResult:
    """
    迁移单个 Schema 文件。

    Args:
        file_path: 文件路径
        dry_run: 是否仅预览变更

    Returns:
        MigrationResult: 迁移结果
    """
    content = file_path.read_text(encoding="utf-8")
    original_content = content
    lines_changed = 0

    # 1. 替换 import 语句
    # 匹配: from pydantic import ... BaseModel ...
    import_replaced = False

    def replace_import(match: re.Match) -> str:
        """替换 import 语句"""
        nonlocal import_replaced
        # 检查是否已经从 framework 导入 BaseModel
        if "from framework.schemas" in content:
            # 已经导入，删除 pydantic 的 BaseModel
            before = match.group(1)
            after = match.group(2)
            # 移除 BaseModel
            before_items = [item.strip() for item in before.split(",") if item.strip() and item.strip() != "BaseModel"]
            after_items = [item.strip() for item in after.split(",") if item.strip() and item.strip() != "BaseModel"]

            all_items = before_items + after_items
            if all_items:
                return f"from pydantic import {', '.join(all_items)}"
            else:
                return ""  # 所有项都已迁移，删除整行

        import_replaced = True
        before = match.group(1)
        after = match.group(2)

        # 提取所有导入项
        before_items = [item.strip() for item in before.split(",") if item.strip()]
        after_items = [item.strip() for item in after.split(",") if item.strip()]
        all_items = before_items + after_items

        # 移除 BaseModel（将从 framework 导入）
        other_items = [item for item in all_items if item != "BaseModel"]

        # 构建新的导入语句
        lines = []
        lines.append("from framework.schemas import BaseModel")

        if other_items:
            lines.append(f"from pydantic import {', '.join(other_items)}")

        return "\n".join(lines)

    # 匹配: from pydantic import <before> BaseModel <after>
    pattern = r"from pydantic import ([^(\n]*?)\bBaseModel\b([^(\n]*)"
    new_content = re.sub(pattern, replace_import, content)

    if new_content != content:
        content = new_content
        lines_changed += 1

    # 2. 删除冗余的 model_config
    config_removed = False

    # 匹配: model_config = ConfigDict(from_attributes=True)
    # 注意：只删除仅包含 from_attributes=True 的配置
    pattern_simple = r'\s*model_config\s*=\s*ConfigDict\(from_attributes=True\)\s*\n'
    new_content = re.sub(pattern_simple, '\n', content)

    if new_content != content:
        content = new_content
        config_removed = True
        lines_changed += 1

    # 3. 删除多余的空行（连续 2 个以上空行变成 2 个）
    content = re.sub(r'\n{3,}', '\n\n', content)

    # 4. 删除文件末尾的多余空行
    content = content.rstrip() + '\n'

    changed = content != original_content

    if changed and not dry_run:
        file_path.write_text(content, encoding="utf-8")

    return MigrationResult(
        file_path=file_path,
        changed=changed,
        import_replaced=import_replaced,
        config_removed=config_removed,
        lines_changed=lines_changed,
    )


def find_schema_files(root_path: Path, exclude_dirs: set[str] | None = None) -> list[Path]:
    """
    查找所有 Schema 文件。

    Args:
        root_path: 根目录
        exclude_dirs: 排除的目录

    Returns:
        Schema 文件列表
    """
    if exclude_dirs is None:
        exclude_dirs = {"ai_plugin/sdk"}

    schema_files = []

    for module in ["iam", "tenant", "ai", "demo"]:
        module_path = root_path / "src" / module / "schemas"
        if module_path.exists():
            for file_path in module_path.rglob("*.py"):
                # 检查是否在排除目录中
                relative_path = file_path.relative_to(root_path)
                if any(excluded in str(relative_path) for excluded in exclude_dirs):
                    continue
                schema_files.append(file_path)

    return sorted(schema_files)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="迁移 Schema BaseModel")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="仅预览变更，不实际修改文件",
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path(__file__).parent.parent,
        help="项目根目录（默认为脚本所在目录的上两级）",
    )
    parser.add_argument(
        "--file",
        type=Path,
        help="仅迁移指定文件",
    )

    args = parser.parse_args()

    if args.file:
        # 迁移单个文件
        result = migrate_file(args.file, dry_run=args.dry_run)
        if result.changed:
            print(f"[OK] {result.file_path.relative_to(args.path)}")
            if result.import_replaced:
                print(f"  - 替换 import 语句")
            if result.config_removed:
                print(f"  - 删除冗余 model_config")
        else:
            print(f"[SKIP] {result.file_path.relative_to(args.path)} (无需变更)")
    else:
        # 迁移所有文件
        schema_files = find_schema_files(args.path)

        print(f"找到 {len(schema_files)} 个 Schema 文件\n")

        results = []
        for file_path in schema_files:
            result = migrate_file(file_path, dry_run=args.dry_run)
            results.append(result)

            if result.changed:
                print(f"[OK] {file_path.relative_to(args.path)}")
                if result.import_replaced:
                    print(f"  - 替换 import 语句")
                if result.config_removed:
                    print(f"  - 删除冗余 model_config")
            else:
                print(f"[SKIP] {file_path.relative_to(args.path)} (无需变更)")

        # 统计
        changed_count = sum(1 for r in results if r.changed)
        import_replaced_count = sum(1 for r in results if r.import_replaced)
        config_removed_count = sum(1 for r in results if r.config_removed)

        print(f"\n{'='*60}")
        print(f"总计: {len(results)} 个文件")
        print(f"已变更: {changed_count} 个文件")
        print(f"  - 替换 import: {import_replaced_count} 个文件")
        print(f"  - 删除 model_config: {config_removed_count} 个文件")

        if args.dry_run:
            print(f"\n[WARNING] 预览模式，未实际修改文件")


if __name__ == "__main__":
    main()
