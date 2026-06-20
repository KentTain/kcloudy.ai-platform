# 任务清单：统一 API 响应类型命名为 Success

## 1. 前端类型定义清理

- [x] 1.1 删除 `iam/types/index.ts` 中的 `ApiResponse` 别名定义（第 7 行和第 15 行）
- [x] 1.2 删除 `tenant/types/index.ts` 中的 `ApiResponse` 别名导出（第 9 行）
- [x] 1.3 删除 `iam/index.ts` 中的 `ApiResponse` 导出（第 32 行）

## 2. 前端 API 文件迁移

- [x] 2.1 更新 `iam/api/auth.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.2 更新 `iam/api/user.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.3 更新 `iam/api/role.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.4 更新 `iam/api/permission.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.5 更新 `iam/api/department.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.6 更新 `iam/api/menu.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.7 更新 `tenant/api/tenant.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.8 更新 `tenant/api/tenantModule.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.9 更新 `tenant/api/module.ts`：导入 `Success` 替代 `ApiResponse`
- [x] 2.10 更新 `tenant/api/resourceConfig.ts`：导入 `Success` 替代 `ApiResponse`

## 3. Python 后端清理

- [x] 3.1 迁移 `error_response` 函数到 `framework/common/exception_handler.py`
- [x] 3.2 更新 `framework/common/exception_handler.py` 中的导入语句
- [x] 3.3 删除 `framework/common/responses.py` 文件
- [x] 3.4 更新 `framework/common/__init__.py`：移除 `success_response` 导出，更新 `error_response` 导入路径
- [x] 3.5 删除 `tests/framework/unit/common/test_common.py` 中的废弃测试用例

## 4. OpenSpec 规范更新

- [x] 4.1 更新 `openspec/specs/paginated-list-response/spec.md`：将 "ApiResponse 字段对齐" 改为 "Success 字段对齐"

## 5. 验证

- [x] 5.1 前端 TypeScript 编译通过，无类型错误
- [x] 5.2 Python 后端测试通过
- [x] 5.3 检查无遗漏的 `ApiResponse` 引用
