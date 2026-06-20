# 设计：统一 API 响应类型命名为 Success

## 上下文

### 当前状态

**前端 Vue**：
- `framework/types/index.ts` 定义了 `Success<T>` 和 `SuccessExtra<T>`
- `iam/types/index.ts` 和 `tenant/types/index.ts` 保留了 `ApiResponse` 别名
- `ai` 和 `demo` 模块已直接使用 `Success`

**Python 后端**：
- `schemas/base.py` 提供 `Success` 和 `SuccessExtra` 类（ORJSONResponse 子类）
- `common/responses.py` 存在冗余的 `ApiResponse` 类和 `success_response` 函数
- Controller 层已统一使用 `Success`

**Rust 后端**：
- 使用 `ApiResponse<T>` 结构体，符合 Rust 命名惯例

### 约束

- 前端 `ApiResponse` 是类型别名，删除后会导致导入错误（编译时发现）
- Python `error_response` 被 `exception_handler.py` 调用，需迁移而非删除
- Rust 命名遵循不同惯例，不强制统一

## 目标 / 非目标

**目标：**
- 统一前端类型命名为 `Success`
- 清理 Python 后端冗余代码
- 更新 OpenSpec 规范文档

**非目标：**
- 不改变 Rust 后端命名（保留 `ApiResponse`）
- 不改变 API 响应格式（字段名保持不变）
- 不影响运行时行为（仅类型重命名）

## 决策

### 决策 1：前端删除别名 vs 保留别名

**选择：删除别名**

考虑的方案：
| 方案 | 优点 | 缺点 |
|------|------|------|
| 删除别名 | 代码一致性高，无歧义 | 需修改 10+ 文件 |
| 保留别名 | 平滑过渡 | 长期存在两套命名 |

理由：项目处于开发阶段，直接清理比长期维护别名更简洁。

### 决策 2：Python `error_response` 处理方式

**选择：迁移到 `exception_handler.py`**

考虑的方案：
| 方案 | 优点 | 缺点 |
|------|------|------|
| 迁移到 exception_handler | 逻辑内聚，删除整个 responses.py | 需更新导入路径 |
| 保留在 responses.py | 无需改导入 | 文件仅剩一个函数 |

理由：`error_response` 仅被异常处理器使用，迁移后逻辑更内聚，且可删除整个 `responses.py` 文件。

### 决策 3：Rust 后端命名

**选择：保留 `ApiResponse`**

理由：
- Rust 命名惯例与 TypeScript 不同
- `Success<T>` 在 Rust 中可能引起语义混淆（与 `Result<T, E>` 的 `Ok` 变体混淆）
- 无需跨语言强制统一命名

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 前端导入错误 | TypeScript 编译时即可发现，无运行时风险 |
| Python 导入路径变更 | 更新 `__init__.py` 导出，保持外部导入兼容 |
| OpenSpec 规范不一致 | 同步更新规范文档 |

## 迁移计划

### 步骤 1：前端类型清理

1. 删除 `iam/types/index.ts` 中的 `ApiResponse` 别名
2. 删除 `tenant/types/index.ts` 中的 `ApiResponse` 别名导出
3. 更新 10 个 API 文件的导入语句
4. 删除 `iam/index.ts` 中的 `ApiResponse` 导出

### 步骤 2：Python 后端清理

1. 迁移 `error_response` 到 `exception_handler.py`
2. 删除 `framework/common/responses.py`
3. 更新 `framework/common/__init__.py`
4. 删除相关测试用例

### 步骤 3：OpenSpec 规范更新

1. 更新 `paginated-list-response/spec.md` 中的命名示例

### 回滚策略

如需回滚：
- 前端：恢复 `ApiResponse` 别名定义
- Python：恢复 `responses.py` 文件
