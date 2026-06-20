# 提案：统一 API 响应类型命名为 Success

## 为什么

前后端 API 响应类型命名不一致，存在冗余定义：
- 前端 `framework/types` 已定义 `Success` 和 `SuccessExtra`，但 `iam/types` 和 `tenant/types` 仍保留 `ApiResponse` 别名
- Python 后端 `schemas/base.py` 已提供 `Success` 类，但 `common/responses.py` 仍存在冗余的 `ApiResponse` 类
- 命名不统一导致代码维护困惑，新人难以理解应该使用哪个类型

现在是清理这些遗留问题的适当时机，统一命名为 `Success`。

## 变更内容

### 前端 Vue

- **删除 `ApiResponse` 别名定义**：清理 `iam/types/index.ts` 和 `tenant/types/index.ts` 中的别名
- **更新 API 文件导入**：10 个 API 文件从 `ApiResponse` 改为 `Success`
- **删除模块导出**：`iam/index.ts` 停止导出 `ApiResponse`
- **BREAKING**：外部代码导入 `ApiResponse` 将失效，需改用 `Success`

### Python 后端

- **删除 `ApiResponse` 类**：移除 `framework/common/responses.py` 中的冗余定义
- **删除 `success_response` 函数**：已无实际使用，Controller 层统一使用 `Success`
- **删除 `paginated_response` 函数**：已无实际使用
- **迁移 `error_response` 函数**：移至 `exception_handler.py`，保持异常处理逻辑内聚
- **更新公共导出**：`framework/common/__init__.py` 更新导出内容

### OpenSpec 规范

- **更新 `paginated-list-response` 规范**：将 "ApiResponse 字段对齐" 改为 "Success 字段对齐"

## 功能 (Capabilities)

### 新增功能

无新增功能，本次变更为重构。

### 修改功能

- `paginated-list-response`: 更新规范文档中的类型命名示例，将 `ApiResponse` 改为 `Success`

## 影响

### 前端 Vue (14 文件)

| 文件 | 变更内容 |
|------|----------|
| `iam/types/index.ts` | 删除 `ApiResponse` 别名定义 |
| `tenant/types/index.ts` | 删除 `ApiResponse` 别名导出 |
| `iam/index.ts` | 删除 `ApiResponse` 导出 |
| `iam/api/*.ts` (6 文件) | 导入 `Success` 替代 `ApiResponse` |
| `tenant/api/*.ts` (4 文件) | 导入 `Success` 替代 `ApiResponse` |

### Python 后端 (4 文件)

| 文件 | 变更内容 |
|------|----------|
| `framework/common/responses.py` | 删除整个文件 |
| `framework/common/exception_handler.py` | 迁入 `error_response` 函数 |
| `framework/common/__init__.py` | 更新导出 |
| `tests/framework/unit/common/test_common.py` | 删除废弃测试 |

### OpenSpec (1 文件)

| 文件 | 变更内容 |
|------|----------|
| `openspec/specs/paginated-list-response/spec.md` | 更新需求名称和示例 |

### Rust 后端

无变更，保留 `ApiResponse` 结构体命名（遵循 Rust 惯例）。
