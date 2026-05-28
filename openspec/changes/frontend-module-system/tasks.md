## 1. 模块系统核心

- [ ] 1.1 创建 `framework/module/types.ts`，定义 ModuleDescriptor、MenuItem 接口
- [ ] 1.2 创建 `framework/module/registry.ts`，实现 ModuleRegistry 单例
- [ ] 1.3 创建 `framework/module/loader.ts`，实现依赖解析（拓扑排序）和模块加载
- [ ] 1.4 创建 `framework/module/context.ts`，实现 Vue Provide/Inject 模块上下文
- [ ] 1.5 创建 `framework/module/index.ts`，导出模块系统公共 API

## 2. 事件总线

- [ ] 2.1 安装 Mitt 依赖（`pnpm add mitt`）
- [ ] 2.2 创建 `framework/events/index.ts`，定义事件类型和事件总线实例
- [ ] 2.3 创建 `framework/events/types.ts`，定义 ModuleEvents 类型
- [ ] 2.4 实现 `useEventBus` composable，支持自动清理订阅

## 3. 路由系统重构

- [ ] 3.1 修改 `framework/router/index.ts`，分离 constantRoutes 和动态路由逻辑
- [ ] 3.2 创建 `framework/router/dynamic.ts`，实现动态路由注册函数
- [ ] 3.3 创建 `framework/router/cross-domain.ts`，实现跨域路由支持（预留）
- [ ] 3.4 在路由守卫中集成模块加载和菜单初始化

## 4. 菜单 Store

- [ ] 4.1 创建 `framework/stores/menu.ts`，定义菜单状态和操作
- [ ] 4.2 实现 `fetchMenu()` 方法，调用后端 API `GET /admin/v1/menus/user`
- [ ] 4.3 实现 `getLocalMenu()` 方法，从模块注册中心获取本地菜单
- [ ] 4.4 实现菜单缓存逻辑，支持缓存失效和刷新
- [ ] 4.5 实现错误处理和 fallback 机制

## 5. 业务模块迁移 - demo

- [ ] 5.1 创建 `demo/index.ts`，导出 demoModule（实现 ModuleDescriptor）
- [ ] 5.2 实现 demoModule.getRoutes()，返回 demo 模块路由配置
- [ ] 5.3 实现 demoModule.getMenuItems()，返回 demo 模块菜单项
- [ ] 5.4 实现 demoModule.setup()，初始化 demo 模块（如有必要）
- [ ] 5.5 在 `main.ts` 中注册 demoModule

## 6. 业务模块迁移 - iam

- [ ] 6.1 创建 `iam/index.ts`，导出 iamModule
- [ ] 6.2 实现 iamModule.getRoutes()，返回 iam 模块路由配置
- [ ] 6.3 实现 iamModule.getMenuItems()，返回 iam 模块菜单项
- [ ] 6.4 在 `main.ts` 中注册 iamModule
- [ ] 6.5 移除 `framework/router/index.ts` 中 iam 路由的静态导入

## 7. 业务模块迁移 - tenant

- [ ] 7.1 创建 `tenant/index.ts`，导出 tenantModule
- [ ] 7.2 实现 tenantModule.getRoutes()，返回 tenant 模块路由配置
- [ ] 7.3 实现 tenantModule.getMenuItems()，返回 tenant 模块菜单项
- [ ] 7.4 在 `main.ts` 中注册 tenantModule
- [ ] 7.5 移除 `framework/router/index.ts` 中 tenant 路由的静态导入

## 8. 应用入口重构

- [ ] 8.1 修改 `main.ts`，创建并配置模块注册中心
- [ ] 8.2 修改 `main.ts`，按顺序注册 demo、iam、tenant 模块
- [ ] 8.3 修改 `main.ts`，调用 `loadModules()` 加载模块
- [ ] 8.4 修改 `main.ts`，动态注册模块路由到 router
- [ ] 8.5 提供 moduleRegistry 和 eventBus 到 Vue app

## 9. 清理与验证

- [ ] 9.1 移除 `framework/router/index.ts` 中所有业务模块的静态导入
- [ ] 9.2 移除 `framework/router/index.ts` 中硬编码的业务路由展开
- [ ] 9.3 验证路由导航正常（demo、iam、tenant 模块页面）
- [ ] 9.4 验证菜单显示正常（从后端 API 加载或本地 fallback）
- [ ] 9.5 验证模块依赖解析正确（如有依赖关系）

## 10. 测试

- [ ] 10.1 创建 `tests/framework/unit/module/registry.test.ts`，测试模块注册
- [ ] 10.2 创建 `tests/framework/unit/module/loader.test.ts`，测试依赖解析
- [ ] 10.3 创建 `tests/framework/unit/module/cyclic-deps.test.ts`，测试循环依赖检测
- [ ] 10.4 创建 `tests/framework/unit/events/event-bus.test.ts`，测试事件总线
- [ ] 10.5 创建 `tests/framework/unit/stores/menu.test.ts`，测试菜单 Store
- [ ] 10.6 创建 `tests/framework/integration/module-loading.test.ts`，测试模块加载集成
