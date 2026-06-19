# Framework 模块开发指南

本文件为 Claude Code 在 `web/vue/src/framework/` 基础设施模块中工作时提供指导。

## 模块定位

Framework 是 Vue 前端的底层基础设施模块，提供路由、状态管理、布局、权限、API 客户端和模块系统等能力。

## 依赖边界

```
demo / iam / tenant ──▶ framework
framework ──X──▶ demo / iam / tenant
```

- 业务模块可以依赖 framework
- framework 禁止依赖业务模块
- 如需业务能力，通过 Protocol、注册器或启动期注入实现依赖倒置

## 目录职责

| 目录 | 职责 |
|------|------|
| api/ | Axios 封装、请求拦截、响应处理 |
| components/ | 框架级 UI 组件（AppForm、AppFormItem） |
| directives/ | Vue 自定义指令（权限指令 v-permission） |
| events/ | EventBus 事件总线、模块事件定义 |
| layouts/ | 布局组件（AdminLayout、AppNavMain、AppPage） |
| module/ | 模块动态加载系统（ModuleDescriptor、ModuleRegistry） |
| pages/ | 公共页面（登录、403、404） |
| router/ | 路由实例创建、静态路由配置、路由守卫 |
| stores/ | Pinia Store（应用状态、用户状态、权限状态） |
| styles/ | 设计令牌、CSS 变量 |
| types/ | TypeScript 类型定义（公共类型、树类型） |
| utils/ | 工具函数（树工具、通用工具） |

## 核心组件

| 组件 | 文件 | 职责 |
|------|------|------|
| ModuleDescriptor | module/types.ts | 模块描述符协议 |
| ModuleRegistry | module/registry.ts | 模块注册中心 |
| setupFramework | module/setup.ts | 框架初始化函数 |
| EventBus | events/index.ts | 事件总线 |
| apiClient | api/client.ts | API 客户端封装 |

## 模块系统

每个业务模块必须实现 `ModuleDescriptor` 协议：

```typescript
interface ModuleDescriptor {
  name: string;                          // 模块名称
  version: string;                       // 模块版本
  getRoutes: () => RouteRecordRaw[];     // 返回路由配置（必需）
  dependencies?: string[];               // 依赖的其他模块
  getMenuItems?: () => MenuItem[];       // 返回菜单项
  setup?: (app: App, pinia: Pinia) => void; // 模块初始化
}
```

## 事件系统

EventBus 用于跨模块通信，预定义事件：

| 事件常量 | 说明 |
|----------|------|
| USER_LOGGED_IN | 用户登录成功 |
| USER_LOGGED_OUT | 用户登出 |
| TENANT_CHANGED | 租户切换 |
| MODULE_LOADED | 模块加载完成 |

## 开发规则

- 抽象能力优先定义在 `types/`
- 路由守卫自动处理登录验证、权限检查
- API 客户端统一处理 token 注入、错误拦截
- 跨模块状态通过 Pinia Store 共享，EventBus 用于一次性事件通知

## 测试

```bash
pnpm test:unit tests/framework/unit/ --run
```

详细组件 API、设计令牌、使用示例见 [API.md](API.md)。
