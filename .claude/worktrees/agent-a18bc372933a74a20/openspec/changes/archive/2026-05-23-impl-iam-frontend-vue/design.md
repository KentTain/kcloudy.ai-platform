# IAM 前端模块技术设计

## Context

项目后端已完整实现 IAM 模块（租户、用户、角色、权限、部门），前端仅有基础登录页面。现需要基于后端 API 实现完整的 IAM 前端模块，集成到现有 Framework 框架中。

**当前状态：**
- 后端 IAM 模块已完成，包含完整的 API 端点和业务逻辑
- 前端 Framework 框架已提供基础布局（AdminLayout）、路由守卫、权限指令
- 现有 Demo 模块作为参考结构

**约束条件：**
- 使用 Vue 3 + TypeScript + Vite
- 使用 Element Plus 作为 UI 组件库
- 复用现有 Framework 的 API 客户端、状态管理、权限控制
- 遵循现有模块的目录结构和代码规范

## Goals / Non-Goals

**Goals:**
- 实现完整的 IAM 前端功能，与后端 API 一一对应
- 遵循现有代码规范和目录结构
- 集成现有 Framework 的权限控制和路由守卫
- 提供良好的用户体验和响应式布局

**Non-Goals:**
- 后端 API 实现（后端已完成）
- 移动端适配（仅 PC 端）
- 国际化（仅中文）
- OAuth 第三方登录前端（仅实现对接入口）

## Decisions

### 1. 模块目录结构

采用与 Demo 模块一致的目录结构：

```
iam/
├── api/           # API 客户端（封装后端 API 调用）
├── components/    # 业务组件（复用 Framework UI 组件）
├── pages/         # 页面组件（每个功能对应独立页面）
├── router/        # 路由配置（模块路由定义）
├── stores/        # 状态管理（Pinia Store）
└── types/         # 类型定义（与后端 Schema 对应）
```

**决策依据：** 遵循现有模块结构，便于理解和维护。

### 2. API 客户端封装

使用 Framework 的 `apiClient` 封装所有 API 调用：

```typescript
import { get, post, put, del } from "@/framework/api/client";

// 示例：获取用户列表
export const getUsers = (params: QueryParams) =>
  get<ApiResponse<UserListVo>>("/v1/users", { params });
```

**决策依据：** 统一使用 Framework 提供的 Axios 封装，自动处理 Token 和错误响应。

### 3. 状态管理方案

使用 Pinia 管理模块状态，与 Framework 的用户状态集成：

- 复用 `useUserStore` 管理登录用户信息
- 新增 IAM 专用 Store（如 `useTenantStore`）管理业务数据

**决策依据：** 保持与 Framework 一致的状态管理方案。

### 4. 权限控制集成

利用 Framework 现有的权限机制：

- 路由守卫根据用户角色动态生成菜单
- 页面内使用 `v-permission` 指令控制元素显示
- API 请求自动携带 Token

**决策依据：** 复用现有 Framework 权限控制，减少重复开发。

### 5. 页面布局

使用 Framework 的 `AdminLayout` 作为父布局：

- 侧边栏：动态渲染菜单
- 顶栏：显示当前租户、用户信息、登出按钮
- 内容区：页面组件

**决策依据：** 保持与现有页面一致的布局风格。

## Risks / Trade-offs

### 风险 1: 后端 API 变更

**风险：** 后端 API 字段或结构可能发生变化  
**缓解：** 前后端使用 TypeScript 类型定义，保持同步更新

### 风险 2: 权限粒度控制

**风险：** 当前权限模型为粗粒度（角色-权限），页面级权限控制可能不足  
**缓解：** 实现页面内按钮级别的权限指令补充

### 风险 3: 大数据量性能

**风险：** 用户列表、权限列表等可能包含大量数据  
**缓解：** 实现分页加载、虚拟滚动等优化

### 权衡 1: 代码复用 vs 封装

**选择：** 优先复用 Framework 组件，必要时封装 IAM 专用组件  
**原因：** 减少重复代码，保持整体一致性

### 权衡 2: 功能完整性 vs 迭代速度

**选择：** 首期实现核心功能（登录、用户、角色、权限），租户和管理后台后续迭代  
**原因：** 平衡交付速度和功能价值
