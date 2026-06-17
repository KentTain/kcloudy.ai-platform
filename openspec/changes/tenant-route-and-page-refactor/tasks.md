# 实施任务清单

## 1. 后端 API 路由变更

- [x] 1.1 更新 resource_config_controller.py 中的路由前缀常量
  - 修改 `DB_PREFIX` 从 `/resource-configs/databases` 为 `/resources/databases`
  - 修改 `STORAGE_PREFIX` 从 `/resource-configs/storages` 为 `/resources/storages`
  - 修改 `CACHE_PREFIX` 从 `/resource-configs/caches` 为 `/resources/caches`
  - 修改 `QUEUE_PREFIX` 从 `/resource-configs/queues` 为 `/resources/queues`
  - 修改 `PUBSUB_PREFIX` 从 `/resource-configs/pubsubs` 为 `/resources/pubsubs`

- [x] 1.2 更新 module.py 中的菜单路径定义
  - 修改 MenuDef 的 path 从 `/admin/resource-configs` 为 `/admin/resources`

## 2. 后端租户统计功能

- [x] 2.1 在 tenant_service.py 添加统计查询方法
  - 实现 `get_tenant_stats()` 方法
  - 使用单次 SQL 查询计算 totalCount、inactiveCount、expiredCount

- [x] 2.2 扩展 tenant_controller.py 的列表接口
  - 在 `list_tenants` 方法中调用 `get_tenant_stats()`
  - 在响应中添加 `stats` 字段

- [x] 2.3 更新响应 Schema
  - 在 `TenantPaginatedListResponse` 中添加 `stats` 字段
  - 定义 `TenantStats` Schema

## 3. 数据库迁移

- [x] 3.1 创建迁移脚本 007_update_menu_paths_to_resources.py
  - 实现 upgrade() 方法更新 tenant.module_menus 表
  - 实现 upgrade() 方法更新 iam.menus 表
  - 实现 downgrade() 方法提供回滚能力

- [x] 3.2 测试迁移脚本
  - 在本地环境执行 upgrade
  - 验证菜单路径更新正确
  - 测试 downgrade 回滚

## 4. 前端 API 调用更新

- [x] 4.1 更新 resourceConfig.ts 中的所有 API 函数
  - 全局替换 `/tenant/admin/v1/resource-configs` 为 `/tenant/admin/v1/resources`
  - 更新 25 个 API 函数的路径

## 5. 前端路由更新

- [x] 5.1 更新 router/index.ts 中的路由配置
  - 修改 `resource-configs` 路由为 `resources`
  - 更新路由 name 和 meta 信息

## 6. 前端 TenantList 页面重构

- [x] 6.1 在 TenantList.vue 中添加统计卡片区
  - 创建统计卡片布局（grid 布局，3 列）
  - 添加租户总数卡片
  - 添加未激活数卡片
  - 添加过期数卡片

- [x] 6.2 集成统计数据展示
  - 在页面加载时获取统计数据
  - 在卡片中展示统计数值
  - 添加加载状态处理

- [x] 6.3 优化页面布局样式
  - 调整统计卡片与搜索区的间距
  - 确保响应式布局
  - 保持与 ModuleList 页面风格一致

## 7. 后端测试

- [ ] 7.1 编写 API 路由测试
  - 测试新的 `/resources/*` 路由可访问
  - 测试所有 CRUD 操作正常
  - 测试连通性测试接口正常

- [ ] 7.2 编写租户统计功能测试
  - 测试 `get_tenant_stats()` 方法
  - 测试统计数据准确性
  - 测试列表接口包含 stats 字段

- [ ] 7.3 编写迁移脚本测试
  - 测试 upgrade 正确更新菜单路径
  - 测试 downgrade 正确回滚

## 8. 前端测试

- [ ] 8.1 编写路由测试
  - 测试 `/admin/resources` 路由可访问
  - 测试路由跳转正常

- [ ] 8.2 编写统计卡片展示测试
  - 测试统计卡片正确渲染
  - 测试统计数据正确显示
  - 测试加载状态

- [ ] 8.3 编写 E2E 测试
  - 测试完整的页面导航流程
  - 测试统计数据显示流程

## 9. 部署与验证

- [ ] 9.1 执行数据库迁移
  - 在测试环境执行迁移
  - 验证菜单路径更新

- [ ] 9.2 部署后端变更
  - 部署 API 路由变更
  - 部署租户统计功能

- [ ] 9.3 部署前端变更
  - 部署路由变更
  - 部署页面重构

- [ ] 9.4 执行集成验证
  - 验证 API 路由正常
  - 验证前端页面正常
  - 验证菜单导航正常
  - 验证统计数据显示正常
