## 为什么

当前前端框架直接导入业务模块路由，违反依赖倒置原则，导致 framework 层与业务模块强耦合。需要实现前端模块系统，对标后端 Python 模块系统设计，支持模块动态注册、依赖解析和按权限加载菜单。

## 变更内容

### 新增

- 模块系统核心（`framework/module/`）：ModuleDescriptor 接口、模块注册中心、模块加载器、模块上下文
- 事件总线（`framework/events/`）：模块间解耦通信机制
- 菜单 Store（`framework/stores/menu.ts`）：动态菜单状态管理
- 跨域路由支持（`framework/router/cross-domain.ts`）：多域名部署场景

### 修改

- **BREAKING** 路由系统重构：`framework/router/index.ts` 从静态导入改为动态注册
- 业务模块入口重构：`demo/index.ts`、`iam/index.ts`、`tenant/index.ts` 导出 ModuleDescriptor
- 应用入口重构：`src/main.ts` 支持模块动态加载

## 功能 (Capabilities)

### 新增功能

- `module-system`: 前端模块系统核心，包含 ModuleDescriptor 接口、模块注册中心、模块加载器、模块上下文
- `event-bus`: 模块间事件总线，支持发布/订阅模式的解耦通信
- `dynamic-menu`: 动态菜单加载，从后端 API 获取菜单树并按权限过滤
- `cross-domain-routing`: 跨域路由支持，允许模块配置外部域名

### 修改功能

（无现有规范，均为新增）

## 影响

### 代码影响

新增文件：
- `web/vue/src/framework/module/types.ts`
- `web/vue/src/framework/module/registry.ts`
- `web/vue/src/framework/module/loader.ts`
- `web/vue/src/framework/module/context.ts`
- `web/vue/src/framework/events/index.ts`
- `web/vue/src/framework/stores/menu.ts`
- `web/vue/src/framework/router/cross-domain.ts`
- `web/vue/src/config/modules.ts`（构建时生成）

修改文件：
- `web/vue/src/framework/router/index.ts`
- `web/vue/src/demo/index.ts`
- `web/vue/src/iam/index.ts`
- `web/vue/src/tenant/index.ts`
- `web/vue/src/main.ts`

### API 依赖

依赖后端菜单 API（`backend-menu-system` 变更）：
- `GET /admin/v1/menus/user`：获取当前用户的菜单树

### 兼容性考虑

- 渐进式迁移：先迁移 demo 模块验证设计，再迁移 iam 和 tenant
- 中间状态兼容：路由系统同时支持静态导入和动态注册，确保迁移期间系统可用

### 构建影响

- 需要更新 Vite 配置支持动态导入
- 后续变更（docker-multi-module-deploy）将支持构建时模块选择
