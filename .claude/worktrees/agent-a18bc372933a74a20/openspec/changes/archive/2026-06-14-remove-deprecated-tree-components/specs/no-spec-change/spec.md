# 无规范变更

本变更为代码清理工作，移除已废弃的 `ui/tree` 目录和 `TreeComponentNode` 类型。

## 说明

- 不引入新功能
- 不修改现有功能的行为
- 仅移除已标记 `@deprecated` 的代码
- `common/Tree` 已具备 `ui/Tree` 的全部功能

## 迁移影响

现有使用 `ui/tree` 的代码需迁移至 `common/Tree` 和 `TreeSelectNode` 类型，此为实现细节变更，不影响功能规范。
