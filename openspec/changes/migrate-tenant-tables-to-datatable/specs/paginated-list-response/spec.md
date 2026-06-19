# paginated-list-response 增量规范

## 概述

更新分页列表响应规范，新增 `SuccessExtra<T>` 类型以支持 DataTable 组件的标准化分页响应格式。

## 修改需求

### 需求:前端分页响应泛型

前端必须提供 `PaginatedListResponse<T>` 泛型接口，与后端分页响应格式对齐，替代原有的 `PageResult<T>`。

#### 场景:PaginatedListResponse 泛型定义

- **当** 定义 `PaginatedListResponse<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `items: T[]`
  - `total: number`
  - `page: number`
  - `page_size: number`

#### 场景:API 调用使用泛型

- **当** API 函数返回分页数据
- **那么** 必须使用 `ApiResponse<PaginatedListResponse<XxxResponse>>` 类型
- **那么** 禁止使用 `ApiResponse<PageResult<XxxResponse>>` 类型

### 需求:SuccessExtra 类型定义

前端必须新增 `SuccessExtra<T>` 类型，与后端 `SuccessExtra` 响应类完全对齐。

#### 场景:SuccessExtra 泛型定义

- **当** 定义 `SuccessExtra<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `code: number`
  - `msg: string`
  - `data: T`
  - `total: number`
  - `page: number`
  - `page_size: number`

#### 场景:DataTable 使用 SuccessExtra

- **当** useDataTable 的 `remoteFetchFn` 返回数据
- **那么** 返回类型必须为 `Promise<SuccessExtra<TData[]>>`
- **那么** `data` 字段直接是数组，不是嵌套对象

### 需求:ApiResponse 类型更新

前端 `ApiResponse<T>` 类型必须与后端响应格式对齐，`message` 字段改为 `msg`。

#### 场景:ApiResponse 字段更新

- **当** 定义 `ApiResponse<T>` 接口
- **那么** 该接口必须包含以下字段：
  - `code: number`
  - `msg: string`
  - `data: T`

#### 场景:现有代码迁移

- **当** 现有代码使用 `response.message`
- **那么** 必须改为 `response.msg`

## 新增需求

### 需求:PaginatedListResponse 废弃标记

`PaginatedListResponse<T>` 必须标记为废弃，推荐使用 `SuccessExtra<T[]>` 替代。

#### 场景:类型迁移提示

- **当** 代码使用 `PaginatedListResponse<T>`
- **那么** TypeScript 显示废弃警告，提示使用 `SuccessExtra<T[]>`

## 验收标准

- [ ] `SuccessExtra<T>` 类型定义完整
- [ ] `ApiResponse.msg` 字段更新
- [ ] `PaginatedListResponse<T>` 标记废弃
- [ ] 现有 API 类型声明更新完成
