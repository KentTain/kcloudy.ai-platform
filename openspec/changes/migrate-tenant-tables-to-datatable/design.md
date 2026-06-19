## 上下文

Tenant 模块的三个列表页面当前使用原生 `<Table>` 组件配合手动状态管理：

| 页面 | 表格数 | 当前实现 |
|------|--------|----------|
| TenantList.vue | 1 | 手动 `loading`/`total`/`pagination` ref + 手动骨架屏 |
| ModuleList.vue | 1 | 手动 `loading`/`total`/`pagination` ref + 手动骨架屏 |
| ResourceConfigList.vue | 5 (Tab) | 每个表格独立手动状态管理 |

项目已有通用 `DataTable` 组件（基于 @tanstack/vue-table），提供：
- 自动骨架屏加载
- 自动空状态展示
- 内置分页控件
- AbortController 请求取消

后端已统一使用 `SuccessExtra` 响应类，格式与 DataTable 完全兼容。

## 目标 / 非目标

**目标：**
- 统一 Tenant 模块列表页面使用 DataTable 组件
- 更新前端类型定义与后端响应格式对齐
- 减少重复代码，提升可维护性

**非目标：**
- 不涉及后端 API 变更（后端已完成迁移）
- 不涉及其他模块的列表页面迁移
- 不新增 DataTable 功能

## 决策

### 决策 1：类型定义更新策略

**选择**：直接修改 `ApiResponse` 类型，标记 `PaginatedListResponse` 为废弃

**理由**：
- 后端已统一使用 `msg` 而非 `message`
- 保持前后端类型命名一致
- 减少类型转换层

**替代方案**：
- ❌ 创建适配器函数：增加额外代码层，每次 API 调用都需包装
- ❌ 保持两套类型：造成混淆，不利于长期维护

### 决策 2：搜索筛选集成方式

**选择**：响应式搜索 + 手动触发

```typescript
const searchForm = ref({ keyword: '', status: '' })

const dataTable = useDataTable<Tenant>({
  columns,
  remoteFetchFn: ({ page, page_size }) => getTenants({
    page, page_size,
    keyword: searchForm.value.keyword || undefined,
    status: searchForm.value.status || undefined,
  })
})

// 手动触发搜索
const handleSearch = () => dataTable.refresh(true)
```

**理由**：
- 用户明确点击搜索按钮后才刷新，体验更好
- 避免输入过程中频繁请求

**替代方案**：
- ❌ 监听 searchForm 自动刷新：输入时频繁请求，浪费资源
- ❌ 使用防抖：增加复杂度，搜索场景不适合

### 决策 3：Tab 切换场景实现

**选择**：每个 Tab 独立 DataTable 实例 + `enabled` 条件

```typescript
const currentType = ref<ResourceType>('database')

const databaseDataTable = useDataTable<DatabaseConfig>({
  columns: databaseColumns,
  enabled: () => currentType.value === 'database',
  remoteFetchFn: ...
})
```

**理由**：
- 每个 Tab 独立状态，切换时保留分页位置
- `enabled` 条件确保只在 Tab 激活时加载

**替代方案**：
- ❌ 单一 DataTable + 动态列：切换时需重置状态，复杂度高

## 风险 / 权衡

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| `message` → `msg` 可能有其他页面引用 | 编译错误 | 全局搜索确认影响范围，同步更新 |
| 统计卡片需额外数据源 | 数据分离 | TenantList 已有独立 `stats` API，保持现有逻辑 |
| 操作按钮渲染方式变更 | 需适应 `h()` 函数 | 创建列定义工具函数，简化代码 |
| ResourceConfigList 测试连接功能 | 特殊交互 | 作为单元格组件独立处理 |

## 实现策略

### 阶段 1：类型层更新

1. 更新 `framework/types/index.ts`
   - `ApiResponse.message` → `msg`
   - 新增 `SuccessExtra<T>` 类型

2. 更新 API 返回类型声明
   - `tenant/api/tenant.ts`
   - `tenant/api/module.ts`
   - `tenant/api/resourceConfig.ts`

### 阶段 2：页面迁移

1. TenantList.vue（最简单，作为试点）
2. ModuleList.vue
3. ResourceConfigList.vue（最复杂，5 个 Tab）

### 回滚策略

- 保留原页面文件，通过路由切换
- 验证通过后删除旧代码
