## 为什么

当前前端 framework 模块直接引用业务模块（demo、iam、tenant），违反依赖倒置原则。这阻碍了模块独立部署和按需加载，需要实现前端模块系统来实现依赖倒置，支持动态路由注册和菜单加载。

## 变更内容

### 新增

- **ModuleDescriptor 接口**：定义模块描述符接口，包含 name、version、getRoutes() 等字段
- **ModuleRegistry 注册中心**：模块注册中心，支持运行时验证和路由收集
- **动态路由注册**：通过 `router.addRoute()` 动态添加模块路由
- **事件总线**：跨模块通信的事件发布订阅机制
- **菜单 Store**：从后端 API 获取菜单数据，支持跨子域名菜单导航

### 重构

- **framework/router/**：移除硬编码的业务路由导入，改为动态注册
- **demo/index.ts**：导出 demoModule ModuleDescriptor
- **iam/index.ts**：导出 iamModule ModuleDescriptor
- **tenant/index.ts**：导出 tenantModule ModuleDescriptor

### 移除

- **framework/router/index.ts**：移除 `import { demoRoutes }` 等硬编码导入

## 功能 (Capabilities)

### 新增功能

- `module-descriptor`: 模块描述符接口定义和类型守卫
- `module-registry`: 模块注册中心，支持注册、验证、路由收集
- `event-bus`: 事件总线，支持跨模块通信
- `menu-store`: 菜单状态管理，支持跨子域名菜单

### 修改功能

无现有功能的需求变更。

## 影响

### 代码影响

| 目录 | 影响 |
|------|------|
| `src/framework/module/` | 新增模块系统核心代码 |
| `src/framework/events/` | 新增事件总线 |
| `src/framework/stores/menu.ts` | 新增菜单 Store |
| `src/framework/router/index.ts` | 重构为动态路由注册 |
| `src/demo/index.ts` | 新增，导出 demoModule |
| `src/iam/index.ts` | 新增，导出 iamModule |
| `src/tenant/index.ts` | 新增，导出 tenantModule |
| `src/main.ts` | 修改，动态导入模块 |

### API 依赖

| API | 说明 |
|-----|------|
| `GET /api/v1/menus/user` | 依赖后端菜单系统（变更 1） |

### 依赖关系

- **依赖变更 1**：需要后端菜单系统提供 `/api/v1/menus/user` API
- 子域名部署支持在变更 3（Docker）实现
