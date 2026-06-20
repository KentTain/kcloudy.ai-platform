# 增量规范：分页列表响应

本增量规范更新 `paginated-list-response` 功能的类型命名。

## 修改需求

### 需求:Success 字段对齐

前端 `Success<T>` 类型必须与后端响应格式对齐。后端已统一使用 `msg` 字段，前端必须同步更新。

#### 场景:Success 字段定义

- **当** 定义 `Success<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `code: number`
  - `msg: string`
  - `data: T`
- **那么** 禁止使用 `message` 字段名

## 重命名需求

### 需求:ApiResponse 字段对齐

**FROM:** `ApiResponse 字段对齐`
**TO:** `Success 字段对齐`

**原因**: 统一类型命名为 `Success`，与后端 `framework.schemas.base.Success` 保持一致。

**迁移方案**:
- 前端代码中使用 `ApiResponse<T>` 的地方改为 `Success<T>`
- 导入路径从模块内部 types 改为 `@/framework/types`
