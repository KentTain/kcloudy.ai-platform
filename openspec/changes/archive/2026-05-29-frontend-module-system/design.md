## 上下文

前端模块系统对标后端 Python 的模块系统设计，实现依赖倒置原则。当前前端 framework 直接导入业务模块路由，阻碍模块独立部署。

参考设计文档：`docs/designs/前端Vue的模块分离设计方案.md`

### 约束

- 使用 Vue 3 + TypeScript + Pinia
- 路由使用 Vue Router 4
- 子域名部署，Cookie 共享（Domain=.example.com）
- 依赖后端菜单 API（变更 1）

## 目标 / 非目标

**目标：**

- 实现 ModuleDescriptor 接口和 ModuleRegistry 注册中心
- 重构 framework/router，移除硬编码业务路由导入
- 业务模块通过 ModuleDescriptor 自注册
- 实现事件总线支持跨模块通信
- 实现菜单 Store 从后端获取菜单数据

**非目标：**

- Docker 构建配置（变更 3）
- 完整的菜单 CRUD 界面
- 微前端框架集成（如 qiankun）

## 决策

### 决策 1：运行时动态注册 vs 构建时静态导入

**选择：** 运行时动态注册

**理由：**
- 支持模块按需加载
- 与后端模块系统设计一致
- 支持未来扩展（如远程模块加载）

**替代方案：**
- 构建时静态导入 → 无法支持独立部署场景

### 决策 2：事件总线实现方式

**选择：** 简单的发布-订阅模式

**理由：**
- 轻量级，无外部依赖
- 满足当前跨模块通信需求
- 易于理解和调试

**替代方案：**
- 使用 Mitt 库 → 引入额外依赖
- 使用 Pinia Store 共享状态 → 耦合度高

### 决策 3：菜单数据来源

**选择：** 后端 API 驱动

**理由：**
- 支持权限控制
- 支持跨模块菜单配置
- 与后端 RBAC 体系集成

**替代方案：**
- 前端静态配置 → 无法支持权限控制

### 决策 4：跨子域名菜单导航

**选择：** 整页跳转（window.location.href）

**理由：**
- 实现简单，无需微前端框架
- 子域名间 Cookie 共享，用户状态保持
- 各模块独立部署，互不影响

**替代方案：**
- iframe 嵌入 → 用户体验差，样式隔离复杂
- 微前端框架 → 过度设计，增加复杂度

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|----------|
| 动态路由调试困难 | 在开发环境添加路由注册日志 |
| 事件总线缺少类型安全 | 定义 ModuleEvents 常量，使用 TypeScript 类型约束 |
| 菜单 API 失败时无菜单 | 实现本地缓存和降级策略 |
| 子域名跳转用户体验 | 跳转前显示 loading 提示 |

## 迁移计划

### 步骤 1：创建模块系统核心

1. 创建 `framework/module/types.ts` - ModuleDescriptor 接口
2. 创建 `framework/module/registry.ts` - ModuleRegistry 类
3. 创建 `framework/events/index.ts` - EventBus 类

### 步骤 2：重构业务模块

1. 创建 `demo/index.ts` - 导出 demoModule
2. 创建 `iam/index.ts` - 导出 iamModule
3. 创建 `tenant/index.ts` - 导出 tenantModule

### 步骤 3：重构路由和入口

1. 修改 `framework/router/index.ts` - 移除硬编码导入
2. 修改 `main.ts` - 动态导入模块并注册

### 步骤 4：实现菜单 Store

1. 创建 `framework/stores/menu.ts` - 菜单状态管理
2. 实现跨子域名菜单处理逻辑

## 待解决问题

无。
