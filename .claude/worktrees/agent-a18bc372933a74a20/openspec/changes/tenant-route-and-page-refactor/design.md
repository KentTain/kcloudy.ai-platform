# 技术设计文档

## 上下文

### 当前状态

**API 路由现状**
- 资源配置 API 使用 `/tenant/admin/v1/resource-configs/{type}` 路径
- 与其他模块路由风格不一致（如 `/tenant/admin/v1/modules`）
- 路径较长，不符合 RESTful 最佳实践

**前端页面现状**
- `TenantList.vue` 使用 `AppPage` 组件，结构简洁
- 缺少统计信息展示，用户无法快速了解租户概况
- 与 `ModuleList.vue` 风格不一致

**菜单数据现状**
- `tenant.module_menus` 表存储模块菜单定义
- `iam.menus` 表存储租户可见菜单
- 存在历史迁移 `006_update_menu_paths.py`（曾将 `resources` 改为 `resource-configs`）

### 约束条件

- **向后兼容**：API 路径变更是破坏性变更，需同步更新前后端
- **数据一致性**：菜单数据需通过迁移脚本更新
- **最小改动**：保留现有架构，仅优化路由和页面布局

## 目标 / 非目标

**目标：**

1. **统一 API 路由风格**
   - 将 `resource-configs` 简化为 `resources`
   - 与其他模块路由保持一致

2. **优化租户管理页面**
   - 添加统计卡片区域，展示关键指标
   - 提升用户决策效率

3. **确保数据一致性**
   - 自动化菜单数据迁移
   - 提供回滚机制

**非目标：**

- 不修改资源配置的数据模型和业务逻辑
- 不重构租户管理的其他页面（如 TenantForm、TenantDetail）
- 不引入新的统计维度（如按时间段统计）
- 不修改权限体系

## 决策

### 决策 1：API 路由变更策略

**选择方案**：全链路同步变更（后端 API + 前端调用 + 菜单数据）

**理由**：
- 保持前后端一致性，避免 API 路径不匹配导致的混淆
- 利用已有的迁移脚本机制（参考 `006_update_menu_paths.py`）
- 变更影响可控，仅需更新常量定义和前端 API 调用

**替代方案**：
- ❌ 仅前端路由变更：会导致前端路由与后端 API 路径不一致，增加维护成本
- ❌ 版本化 API（`/v2/resources`）：过度设计，当前场景无需多版本共存

### 决策 2：租户统计数据获取方式

**选择方案**：扩展现有列表接口，添加 `stats` 字段

**理由**：
- 避免额外的 HTTP 请求，减少网络开销
- 统计数据与列表数据高度相关，在同一个接口返回更合理
- 实现简单，仅需扩展 Service 层查询逻辑

**接口设计**：
```python
# GET /tenant/admin/v1/tenants
{
  "code": 200,
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "stats": {  # 新增字段
      "totalCount": 100,
      "inactiveCount": 15,
      "expiredCount": 8
    }
  }
}
```

**替代方案**：
- ❌ 新增独立统计接口：需要额外的 HTTP 请求，增加前后端交互复杂度
- ❌ 前端自行计算：数据量大时性能差，且无法处理分页场景

### 决策 3：统计指标实现

**统计指标定义**：

| 指标 | SQL 逻辑 | 说明 |
|------|---------|------|
| 租户总数 | `COUNT(*) WHERE deleted_at IS NULL` | 所有未删除的租户 |
| 未激活数 | `COUNT(*) WHERE status = 'inactive'` | 状态为停用的租户 |
| 过期数 | `COUNT(*) WHERE expired_at < NOW()` | 已过期的租户 |

**实现方式**：
```python
# tenant/services/tenant_service.py
async def get_tenant_stats() -> dict:
    """获取租户统计数据"""
    async with async_session() as session:
        # 使用单次查询计算所有统计
        result = await session.execute(
            select(
                func.count().label('total'),
                func.count(case((Tenant.status == 'inactive', 1))).label('inactive'),
                func.count(case((Tenant.expired_at < datetime.now(), 1))).label('expired')
            ).where(Tenant.deleted_at.is_(None))
        )
        row = result.one()
        return {
            "totalCount": row.total,
            "inactiveCount": row.inactive,
            "expiredCount": row.expired
        }
```

**性能考虑**：
- 使用单次 SQL 查询计算所有统计，避免多次查询
- 添加数据库索引（`status`, `expired_at` 字段已有索引）

### 决策 4：前端布局方案

**选择方案**：保留 `AppPage` 组件，添加统计卡片区

**理由**：
- 改动最小化，降低引入 bug 的风险
- 保持与其他页面的一致性（AppPage 是框架组件）
- 统计卡片作为独立组件，可复用

**布局结构**：
```
<AppPage>
  <template #actions>  ← 保持不变
    <Button>新建租户</Button>
  </template>

  <!-- 新增统计卡片区 -->
  <div class="grid gap-4 md:grid-cols-3">
    <StatsCard label="租户总数" :value="stats.totalCount" />
    <StatsCard label="未激活数" :value="stats.inactiveCount" />
    <StatsCard label="过期数" :value="stats.expiredCount" />
  </div>

  <Card>  ← 原有的搜索 + 表格区域
    <!-- 搜索区 -->
    <!-- 数据表格 -->
  </Card>

  <Pagination />  ← 保持不变
</AppPage>
```

**替代方案**：
- ❌ 完全重构为 ModuleList 布局：需要移除 AppPage，改动较大，风险较高

### 决策 5：数据迁移策略

**选择方案**：创建新的迁移脚本 `007_update_menu_paths_to_resources.py`

**理由**：
- 遵循数据库迁移最佳实践
- 提供回滚机制（downgrade）
- 与历史迁移 `006_update_menu_paths.py` 形成完整链路

**迁移内容**：
```python
# 更新 tenant.module_menus
UPDATE tenant.module_menus
SET path = '/admin/resources'
WHERE code = 'tenant.resources' AND path = '/admin/resource-configs';

# 更新 iam.menus
UPDATE iam.menus
SET path = '/admin/resources'
WHERE code = 'tenant.resources' AND path = '/admin/resource-configs';
```

**执行时机**：部署时自动执行（Alembic）

## 风险 / 权衡

### 风险 1：API 路径变更导致客户端失效

**风险描述**：外部系统或已缓存的前端代码可能调用旧 API 路径

**缓解措施**：
- ✅ 前后端同步部署，确保一致性
- ✅ 更新 API 文档，通知相关方
- ⚠️ 不提供向后兼容（旧 API 将直接失效）

### 风险 2：菜单数据迁移失败

**风险描述**：迁移脚本执行失败导致菜单路径不一致

**缓解措施**：
- ✅ 提供回滚机制（downgrade）
- ✅ 迁移前备份数据库
- ✅ 在测试环境验证迁移脚本

### 风险 3：统计数据性能问题

**风险描述**：租户数量增长后，统计查询可能变慢

**缓解措施**：
- ✅ 使用单次 SQL 查询，避免 N+1 问题
- ✅ 确保 `status` 和 `expired_at` 字段有索引
- 🔄 未来可考虑缓存统计数据（如 Redis）

### 权衡：统计卡片组件复用性

**权衡说明**：
- 当前设计为内联统计卡片，未抽取为独立组件
- 牺牲复用性换取实现速度
- 如其他页面需要类似功能，再抽取为 `StatsCard` 组件

## 迁移计划

### 阶段 1：后端变更

1. **更新 API 路由前缀**
   - 修改 `resource_config_controller.py` 的 5 个 PREFIX 常量
   - 运行单元测试验证路由变更

2. **添加租户统计接口**
   - 扩展 `tenant_controller.py` 的 `list_tenants` 方法
   - 在 `tenant_service.py` 添加 `get_tenant_stats` 方法
   - 更新响应 Schema，添加 `stats` 字段

3. **创建数据库迁移**
   - 创建 `007_update_menu_paths_to_resources.py`
   - 本地测试迁移脚本（upgrade + downgrade）

### 阶段 2：前端变更

1. **更新 API 调用**
   - 修改 `resourceConfig.ts` 的 25 个 API 函数路径
   - 全局替换 `/resource-configs` → `/resources`

2. **更新前端路由**
   - 修改 `router/index.ts` 的路由配置
   - 测试路由跳转

3. **重构 TenantList 页面**
   - 添加统计卡片区
   - 集成统计数据展示
   - 调整布局样式

### 阶段 3：数据迁移

1. **执行数据库迁移**
   ```bash
   uv run python manage.py db upgrade
   ```

2. **验证菜单数据**
   - 检查 `tenant.module_menus` 表
   - 检查 `iam.menus` 表
   - 验证前端菜单导航

### 阶段 4：测试验证

1. **后端测试**
   - API 路由测试
   - 统计接口测试
   - 迁移脚本测试

2. **前端测试**
   - 页面路由测试
   - 统计卡片展示测试
   - E2E 测试

### 回滚策略

如需回滚：
1. 执行数据库迁移回滚：`uv run python manage.py db downgrade -1`
2. 回滚后端代码变更
3. 回滚前端代码变更
