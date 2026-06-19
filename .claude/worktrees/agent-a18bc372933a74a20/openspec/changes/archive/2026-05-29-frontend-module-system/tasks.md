## 1. 模块系统核心

- [x] 1.1 创建 `framework/module/types.ts`，实现 ModuleDescriptor 接口和 isModuleDescriptor 类型守卫
- [x] 1.2 创建 `framework/module/registry.ts`，实现 ModuleRegistry 类
- [x] 1.3 创建 `framework/module/index.ts`，导出模块系统 API

## 2. 事件总线

- [x] 2.1 创建 `framework/events/index.ts`，实现 EventBus 类
- [x] 2.2 创建 `framework/events/index.ts`，定义 ModuleEvents 常量

## 3. 菜单 Store

- [x] 3.1 创建 `framework/stores/menu.ts`，实现菜单状态管理
- [x] 3.2 实现 fetchMenus() 方法，调用 `/api/v1/menus/user` API
- [x] 3.3 实现跨子域名菜单处理逻辑（isExternal 计算）
- [x] 3.4 实现菜单本地缓存和强制刷新

## 4. 业务模块重构

- [x] 4.1 创建 `demo/index.ts`，导出 demoModule ModuleDescriptor
- [x] 4.2 创建 `iam/index.ts`，导出 iamModule ModuleDescriptor
- [x] 4.3 创建 `tenant/index.ts`，导出 tenantModule ModuleDescriptor

## 5. 路由系统重构

- [x] 5.1 创建 `framework/module/setup.ts`，实现 setupFramework 函数
- [x] 5.2 重构 `framework/router/index.ts`，移除硬编码业务路由导入
- [x] 5.3 实现动态路由注册逻辑（router.addRoute）

## 6. 入口文件重构

- [x] 6.1 重构 `main.ts`，实现模块动态导入
- [x] 6.2 在 main.ts 中调用 setupFramework 注册模块

## 7. 类型导出

- [x] 7.1 更新 `framework/index.ts`，导出模块系统公共 API

## 8. 测试验证

- [x] 8.1 验证模块注册和路由收集
- [x] 8.2 验证事件总线订阅和发布
- [x] 8.3 验证菜单 Store 数据获取
- [x] 8.4 验证跨子域名菜单跳转逻辑
- [ ] 8.5 启动开发服务器，验证路由正常工作
