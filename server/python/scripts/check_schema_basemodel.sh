#!/bin/bash
# Schema BaseModel 使用检查脚本
#
# 检查业务模块的 Schema 文件是否使用了正确的基类。
# 违规文件将被列出并导致脚本返回非零退出码。

set -e

# 项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 需要检查的模块
MODULES=("iam" "tenant" "ai" "demo")

# 排除的目录（相对于 src/）
EXCLUDE_DIRS=("ai_plugin/sdk")

# 违规计数
VIOLATIONS=0

echo "检查 Schema BaseModel 使用情况..."
echo "========================================"
echo ""

for module in "${MODULES[@]}"; do
    SCHEMA_DIR="$ROOT_DIR/src/$module/schemas"

    if [ ! -d "$SCHEMA_DIR" ]; then
        continue
    fi

    echo "检查模块: $module"
    echo "----------------------------------------"

    # 查找所有 .py 文件
    while IFS= read -r -d '' file; do
        # 检查是否在排除目录中
        relative_path="${file#$ROOT_DIR/src/}"
        skip=false

        for exclude_dir in "${EXCLUDE_DIRS[@]}"; do
            if [[ "$relative_path" == "$exclude_dir"* ]]; then
                skip=true
                break
            fi
        done

        if [ "$skip" = true ]; then
            continue
        fi

        # 检查是否有违规的 import 语句
        # 匹配: from pydantic import ... BaseModel ...
        if grep -q "from pydantic import .*BaseModel" "$file" 2>/dev/null; then
            echo "[违规] $relative_path"
            echo "  - 发现: from pydantic import ... BaseModel ..."
            echo "  - 应改为: from framework.schemas import BaseModel"
            echo ""
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done < <(find "$SCHEMA_DIR" -name "*.py" -type f -print0)

    echo ""
done

echo "========================================"
echo "检查完成"
echo ""

if [ $VIOLATIONS -gt 0 ]; then
    echo "[错误] 发现 $VIOLATIONS 个违规文件"
    echo ""
    echo "请运行以下命令自动修复："
    echo "  python scripts/migrate_schema_basemodel.py"
    echo ""
    exit 1
else
    echo "[通过] 所有 Schema 文件均使用正确的基类"
    exit 0
fi
