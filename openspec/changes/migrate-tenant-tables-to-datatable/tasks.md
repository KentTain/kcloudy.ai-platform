## 1. 类型定义更新

- [x] 1.1 更新 `framework/types/index.ts`，`ApiResponse.message` 改为 `msg`
- [x] 1.2 新增 `SuccessExtra<T>` 类型定义
- [x] 1.3 标记 `PaginatedListResponse<T>` 为废弃

## 2. API 类型声明更新

- [x] 2.1 更新 `tenant/api/tenant.ts`，`getTenants` 返回类型改为 `SuccessExtra<Tenant[]>`
- [x] 2.2 更新 `tenant/api/module.ts`，`getModules` 返回类型改为 `SuccessExtra<Module[]>`
- [x] 2.3 更新 `tenant/api/resourceConfig.ts`，所有 `getXxxConfigs` 返回类型改为 `SuccessExtra<XxxConfig[]>`

## 3. TenantList 页面迁移

- [x] 3.1 移除手动状态管理（loading、total、pagination refs）
- [x] 3.2 创建 Tenant 类型列定义（ColumnDef<Tenant>[]）
- [x] 3.3 使用 useDataTable 初始化表格状态
- [x] 3.4 替换模板中的原生 Table 为 DataTable 组件
- [x] 3.5 实现搜索筛选集成（handleSearch 调用 dataTable.refresh）
- [x] 3.6 保留统计卡片区独立逻辑

## 4. ModuleList 页面迁移

- [ ] 4.1 移除手动状态管理
- [ ] 4.2 创建 Module 类型列定义
- [ ] 4.3 使用 useDataTable 初始化表格状态
- [ ] 4.4 替换模板中的原生 Table 为 DataTable 组件
- [ ] 4.5 实现搜索筛选集成
- [ ] 4.6 保留统计卡片区独立逻辑

## 5. ResourceConfigList 页面迁移

- [ ] 5.1 重构页面结构，每个 Tab 使用独立 DataTable
- [ ] 5.2 创建 DatabaseConfig 类型列定义
- [ ] 5.3 创建 StorageConfig 类型列定义
- [ ] 5.4 创建 CacheConfig 类型列定义
- [ ] 5.5 创建 QueueConfig 类型列定义
- [ ] 5.6 创建 PubsubConfig 类型列定义
- [ ] 5.7 使用 `enabled` 条件控制 Tab 激活时加载
- [ ] 5.8 实现测试连接按钮的单元格渲染
- [ ] 5.9 替换模板中的原生 Table 为 DataTable 组件
- [ ] 5.10 实现全局搜索刷新所有 DataTable

## 6. 验证与清理

- [ ] 6.1 验证 TenantList 功能正常（列表、搜索、分页、操作按钮）
- [ ] 6.2 验证 ModuleList 功能正常
- [ ] 6.3 验证 ResourceConfigList 5 个 Tab 功能正常
- [ ] 6.4 验证骨架屏加载状态
- [ ] 6.5 验证空状态展示
- [ ] 6.6 运行前端构建，确保无 TypeScript 错误
- [ ] 6.7 提交代码，遵循 Conventional Commits
