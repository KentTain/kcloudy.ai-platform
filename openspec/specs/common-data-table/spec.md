# common-data-table 规格

## 概述

高级数据表格组件，基于 @tanstack/vue-table 实现，支持远程数据加载、分页、骨架屏等功能。

## 功能需求

### 核心功能

- 基于 @tanstack/vue-table 的表格渲染
- 远程数据加载（分页查询）
- 自动分页控制
- 加载状态展示（骨架屏 + 刷新遮罩）
- 空状态展示

### 组件 API

#### DataTable

**Props:**

```typescript
interface DataTableProps {
  alonTable: AlonTableState<any>  // 表格状态对象
  fixedLayout?: boolean            // 是否固定列宽
}
```

**Slots:**

- 默认插槽：自定义单元格渲染

#### DataTablePagination

**Props:**

```typescript
interface DataTablePaginationProps {
  table: Table<any>  // @tanstack Table 实例
}
```

#### useDataTable

**参数:**

```typescript
interface UseDataTableOptions<TData> {
  columns: ColumnDef<TData>[]
  columnVisibility?: () => VisibilityState
  initialState?: InitialTableState
  remoteFetchFn: (pageQuery: { page: number; page_size: number; signal: AbortSignal }) => Promise<ApiResponse<TData[]>>
  enabled?: () => boolean
}
```

**返回:**

```typescript
interface DataTableState<TData> {
  loading: Ref<boolean>
  refresh: (firstPage?: boolean, skipLoading?: boolean) => void
  table: Table<TData>
}
```

## 迁移来源

- 源文件：`D:\Project\ai\Alon\apps\kbhub\web\src\components\alon\alon-table\`
- 目标位置：`web/vue/src/components/common/data-display/table/`

## 文件清单

| 源文件 | 目标文件 |
|--------|----------|
| AlonDataTable.vue | DataTable.vue |
| AlonDataTablePagination.vue | DataTablePagination.vue |
| use-alon-table.ts | use-data-table.ts |

## 依赖

- @tanstack/vue-table@^8.21.3
- ui/table（Table, TableBody, TableCell, TableHead, TableHeader, TableRow）
- ui/scroll-area
- ui/skeleton
- lucide-vue-next（Loader2Icon）

## 验收标准

- [ ] 组件迁移完成，文件位置正确
- [ ] 重命名完成（移除 Alon 前缀）
- [ ] 导入路径更新正确
- [ ] 类型定义迁移完整
- [ ] 构建通过
