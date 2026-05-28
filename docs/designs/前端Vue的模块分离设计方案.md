# 前端 Vue 模块分离设计方案

## 1. 问题分析

### 1.1 当前架构问题

当前前端 framework 模块直接引用业务模块，违反了依赖倒置原则：

```
┌─────────────────────────────────────────────────────────────┐
│                   当前前端架构依赖关系                          │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │   framework  │
                    │   (基础设施)  │
                    └──────┬───────┘
                           │ ❌ 违反依赖原则
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐      ┌──────────┐
    │  demo   │      │   iam   │      │  tenant  │
    │ (业务)   │      │ (业务)  │      │  (业务)  │
    └─────────┘      └─────────┘      └──────────┘
```

**具体违反依赖倒置的地方：**

1. framework/router/index.ts 直接导入业务模块：

   ``` typescript
   import { demoRoutes } from "@/demo/router";
   import { iamRoutes } from "@/iam/router";
   import { tenantRoutes } from "@/tenant/router";
   ```

2. asyncRoutes 配置硬编码业务路由：

   ``` typescript
   children: [
     ...demoRoutes,    // ❌ 硬编码
     ...iamRoutes,     // ❌ 硬编码
     ...tenantRoutes,  // ❌ 硬编码
   ]
   ```

### 1.2 后端 Python 的解决方案

后端通过模块系统实现了依赖倒置：

```
┌─────────────────────────────────────────────────────────────┐
│               后端 Python 模块系统设计                       │
└─────────────────────────────────────────────────────────────┘

framework/module/                    业务模块 (demo/iam)
├── **init**.py                     ├── **init**.py
├── descriptor.py  ◀─────────────────┤  实现 ModuleDescriptor
│   └─ ModuleDescriptor             │
├── registry.py   ◀─────────────────┤  注册到 ModuleRegistry
│   └─ ModuleRegistry               │
└── loader.py                        └── router, models, etc.

依赖方向：
  demo/iam ──▶ framework/module (依赖抽象)
  framework ──X──▶ demo/iam (不依赖具体)
```

## 2. 解决方案

### 2.1 前端模块系统设计

对标后端设计，前端实现相同的模块系统架构：

```
┌─────────────────────────────────────────────────────────────┐
│              前端 Vue 模块系统设计 (对标后端)                │
└─────────────────────────────────────────────────────────────┘

framework/module/
├── types.ts          # 模块描述符接口定义
├── registry.ts       # 模块注册中心
├── loader.ts         # 模块加载器
└── context.ts        # Vue 提供的模块上下文

业务模块结构：
demo/
├── index.ts          # 导出模块描述符
├── router/
├── pages/
└── ...

依赖方向：
  demo/iam ──▶ framework/module (依赖接口)
  framework ──X──▶ demo/iam (不依赖具体)
```

### 2.2 ModuleDescriptor 接口设计

``` typescript
// framework/module/types.ts
import type { RouteRecordRaw, App } from 'vue';

export interface MenuItem {
  id: string;
  name: string;
  path: string;
  icon?: string;
  children?: MenuItem[];
}

export interface ModuleDescriptor {
  // 必填字段
  name: string;
  version: string;
  
  // 必填方法
  getRoutes(): RouteRecordRaw[];
  
  // 可选字段
  dependencies?: string[];
  icon?: string;
  
  // 可选方法
  getMenuItems?(): MenuItem[];
  getStores?(): Record<string, unknown>;
  setup?(app: App): void | Promise<void>;
  
  // 类型标记（用于运行时检测）
  readonly **module_descriptor**: unique symbol;
}
```

### 2.3 模块注册中心

``` typescript
// framework/module/registry.ts
import type { ModuleDescriptor } from './types';
import { isModuleDescriptor } from './types';

export class ModuleRegistry {
  private modules = new Map<string, ModuleDescriptor>();
  
  register(module: unknown): void {
    // 类型检查
    if (!isModuleDescriptor(module)) {
      throw new TypeError(
        Invalid module descriptor:       );
    }

    // 名称检查
    if (!/^[a-z][a-z0-9-]*\$/.test(module.name)) {
      throw new Error(
        Invalid module name "": must be lowercase alphanumeric with hyphens
      );
    }
    
    // 版本检查
    if (!/^\d+\.\d+\.\d+(-[\w.]+)?\$/.test(module.version)) {
      throw new Error(
        Invalid module version "": must follow semver
      );
    }
    
    // 重复检查
    if (this.modules.has(module.name)) {
      throw new Error(Module "" is already registered);
    }
    
    this.modules.set(module.name, module);
    console.log([ModuleRegistry] Registered: \@\);
  }
  
  getRoutes(): RouteRecordRaw[] {
    return Array.from(this.modules.values())
      .flatMap(m => m.getRoutes());
  }
  
  getMenuItems(): MenuItem[] {
    return Array.from(this.modules.values())
      .filter(m => m.getMenuItems)
      .flatMap(m => m.getMenuItems!());
  }
}
```

### 2.4 动态路由注册

``` typescript
// framework/module/setup.ts
export function setupFramework(
  app: App,
  options: { modules: ModuleDescriptor[] }
) {
  const registry = new ModuleRegistry();
  
  // 注册所有模块
  for (const module of options.modules) {
    registry.register(module);
    module.setup?.(app);
  }
  
  // 创建路由实例（空路由）
  const router = createRouter({
    history: createWebHistory(),
    routes: constantRoutes,  // 只包含登录、403、404
  });
  
  // 动态添加模块路由
  const moduleRoutes = registry.getRoutes();
  for (const route of moduleRoutes) {
    router.addRoute(route);  // ← 运行时动态添加
  }
  
  app.use(router);
  app.provide('moduleRegistry', registry);
}
```

### 2.5 业务模块示例

``` typescript
// demo/index.ts
import type { ModuleDescriptor } from '@ai-platform/framework';
import { demoRoutes } from './router';
import { useDemoStore } from './stores';

export const demoModule: ModuleDescriptor = {
  name: 'demo',
  version: '1.0.0',
  
  getRoutes() {
    return [
      {
        path: '/',
        component: () => import('@ai-platform/framework/layouts/AdminLayout'),
        children: demoRoutes,
      }
    ];
  },
  
  getMenuItems() {
    return [
      { id: 'home', name: '首页', path: '/', icon: 'home' },
      { id: 'datasets', name: '知识库', path: '/datasets', icon: 'database' },
    ];
  },
  
  getStores() {
    return { demo: useDemoStore };
  },
  
  setup(app) {
    console.log('Demo module initialized');
  }
};
```

## 3. 菜单系统设计（后端驱动）

### 3.1 数据模型设计

菜单归属 IAM 模块，继承 BaseModel 和 TreeNodeMixin：

```python

# iam/models/menu.py

from sqlalchemy import String, Boolean, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSON

from iam.models import BaseModel
from framework.database import TreeNodeMixin

class Menu(BaseModel, TreeNodeMixin):
    """
    菜单模型

    继承 TreeNodeMixin 提供树形结构支持：
    - parent_id: 父菜单 ID
    - tree_leaf: 是否为叶子节点
    - tree_level: 树层级
    - tree_sort: 排序号
    - tree_sorts: 排序路径
    - tree_names: 名称路径
    - parent_ids: 父ID路径
    """
    __tablename__ = "menus"
    
    # 覆盖 TreeNodeMixin 的 parent_id，使用 ForeignKey
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("menus.id", ondelete="SET NULL"), nullable=True, comment="父部门ID"
    )
    module: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        comment="所属模块（demo/iam/tenant）"
    )
    code: Mapped[str] = mapped_column(
        String(100), 
        unique=True, 
        nullable=False,
        comment="菜单编码，如 demo:home, iam:user:list"
    )
    name: Mapped[str] = mapped_column(
        String(100), 
        nullable=False, 
        comment="菜单名称（显示用）"
    )
    path: Mapped[str] = mapped_column(
        String(200), 
        nullable=False, 
        comment="前端路由路径，如 /users, /datasets"
    )
    icon: Mapped[str | None] = mapped_column(
        String(50), 
        nullable=True, 
        comment="图标标识"
    )
    is_visible: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True,
        comment="是否显示"
    )
    deployment_base_url: Mapped[str | None] = mapped_column(
        String(200), 
        nullable=True,
        comment="模块部署地址，NULL 表示当前域"
    )
    metadata: Mapped[dict | None] = mapped_column(
        JSON, 
        nullable=True, 
        comment="扩展元数据"
    )

    @classmethod
    def tree_name_field(cls) -> str:
        """TreeNodeMixin 需要重写此方法"""
        return "name"

    __table_args__ = (
        Index("ix_menus_module", "module"),
        Index("ix_menus_code", "code"),
    )

class MenuPermission(BaseModel):
    """菜单-权限关联"""
    **tablename** = "menu_permissions"

    menu_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("menus.id", ondelete="CASCADE"),
        nullable=False,
        comment="菜单ID"
    )
    permission_id: Mapped[str] = mapped_column(
        String(36), 
        ForeignKey("permissions.id", ondelete="CASCADE"),
        nullable=False,
        comment="权限ID"
    )

    __table_args__ = (
        Index("ix_menu_permissions_menu_id", "menu_id"),
        Index("ix_menu_permissions_permission_id", "permission_id"),
        UniqueConstraint("menu_id", "permission_id", name="uq_menu_permissions"),
    )
```

### 3.2 权限关联设计

采用 **方案 B**：菜单关联权限，权限再关联角色：

```
┌──────────┐         ┌────────────┐         ┌──────────┐
│  Menu    │────────▶│ Permission │────────▶│  Role    │
└──────────┘         └────────────┘         └──────────┘
     │                     ▲
     └─────────────────────┘
       menu_permissions 表
```

**优势：**

1. 复用现有 Permission 模型，不破坏 RBAC 设计
2. 菜单可以有多个权限（查看菜单需要任一权限）
3. 权限变更自动反映到菜单可见性

### 3.3 API 设计

```
GET /api/v1/menus/user
返回当前用户可见的菜单树（含部署路径）

响应示例：
{
  "menus": [
    {
      "id": "1",
      "parent_id": "ROOT",
      "module": "demo",
      "code": "demo:home",
      "name": "首页",
      "path": "/",
      "icon": "home",
      "tree_level": 0,
      "tree_sort": 1,
      "deployment_base_url": null,
      "children": []
    },
    {
      "id": "2",
      "parent_id": "ROOT",
      "module": "iam",
      "code": "iam:user",
      "name": "用户管理",
      "path": "/users",
      "icon": "user",
      "tree_level": 0,
      "tree_sort": 2,
      "deployment_base_url": "https://iam.example.com",
      "children": [...]
    }
  ]
}
```

### 3.4 前端处理逻辑

``` typescript
// framework/stores/menu.ts
export interface MenuTreeNode {
  id: string;
  parentId: string;
  module: string;
  code: string;
  name: string;
  path: string;
  icon?: string;
  treeLevel: number;
  treeSort: number;
  deploymentBaseUrl: string | null;
  children?: MenuTreeNode[];
  isExternal?: boolean;  // 前端计算
}

export const useMenuStore = defineStore('menu', () => {
  const menus = ref<MenuTreeNode[]>([]);
  const currentOrigin = window.location.origin;
  
  const fetchMenus = async () => {
    const response = await apiClient.get('/api/v1/menus/user');

    // 处理跨域菜单
    const processMenu = (menu: MenuTreeNode): MenuTreeNode => {
      const isExternal = menu.deploymentBaseUrl && 
                         menu.deploymentBaseUrl !== currentOrigin;
      
      return {
        ...menu,
        isExternal,
        children: menu.children?.map(processMenu)
      };
    };
    
    menus.value = response.data.menus.map(processMenu);
  };
  
  return { menus, fetchMenus };
});
```

### 3.5 跨域菜单导航

``` typescript
// framework/router/cross-domain.ts
export function setupCrossDomainRoutes(router: Router, menus: MenuTreeNode[]) {
  const processMenu = (menu: MenuTreeNode) => {
    if (menu.isExternal) {
      // 跨域菜单：添加外部链接路由
      router.addRoute({
        path: menu.path,
        name: external-\,
        beforeEnter: (to, from, next) => {
          // 外部链接：直接跳转
          window.location.href = \;
        },
        meta: { hidden: true }
      });
    }

    if (menu.children) {
      menu.children.forEach(processMenu);
    }
  };
  
  menus.forEach(processMenu);
}
```

## 4. 模块间通信机制

### 4.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│                   状态管理三层架构                           │
└─────────────────────────────────────────────────────────────┘

Layer 1: Framework Stores（全局共享）
├── userStore          # 用户信息、权限
├── appStore           # 应用状态
└── tenantStore        # 租户信息（如果框架级）

Layer 2: Module Stores（模块私有）
├── demo/demoStore     # Demo 模块状态
├── iam/iamStore       # IAM 模块状态
└── tenant/tenantStore # Tenant 模块状态

Layer 3: Event Bus（跨模块通信）
└── framework/eventBus # 事件总线
```

### 4.2 事件总线实现

``` typescript
// framework/events/index.ts
type EventHandler = (payload: any) => void;

class EventBus {
  private listeners = new Map<string, Set<EventHandler>>();
  
  on(event: string, handler: EventHandler) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);

    return () => this.off(event, handler);
  }
  
  emit(event: string, payload?: any) {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach(h => h(payload));
    }
  }
  
  off(event: string, handler: EventHandler) {
    this.listeners.get(event)?.delete(handler);
  }
}

// 模块通信事件定义
export const ModuleEvents = {
  // 用户相关
  USER_LOGGED_IN: 'user:logged-in',
  USER_LOGGED_OUT: 'user:logged-out',
  TENANT_CHANGED: 'tenant:changed',
  
  // 模块相关
  MODULE_LOADED: 'module:loaded',
  MODULE_ERROR: 'module:error',
  
  // 数据相关
  DATA_REFRESH_REQUESTED: 'data:refresh-requested',
} as const;

export const eventBus = new EventBus();
```

### 4.3 使用示例

``` typescript
// tenant 模块发送租户变更事件
import { eventBus, ModuleEvents } from '@ai-platform/framework';

const switchTenant = async (tenantId: string) => {
  await tenantApi.switchTenant(tenantId);
  
  // 通知其他模块刷新数据
  eventBus.emit(ModuleEvents.TENANT_CHANGED, { tenantId });
};

// demo 模块监听租户变更
import { eventBus, ModuleEvents } from '@ai-platform/framework';
import { onMounted, onUnmounted } from 'vue';

onMounted(() => {
  const unsubscribe = eventBus.on(
    ModuleEvents.TENANT_CHANGED,
    ({ tenantId }) => {
      // 刷新 Demo 模块数据
      fetchDemoData(tenantId);
    }
  );
  
  onUnmounted(unsubscribe);
});
```

### 4.4 模块声明依赖与事件

``` typescript
// demo/index.ts
export const demoModule: ModuleDescriptor = {
  name: 'demo',
  version: '1.0.0',
  dependencies: ['iam'],  // ← 声明依赖
  
  // 订阅的事件（可选扩展）
  events: {
    [ModuleEvents.TENANT_CHANGED]: 'handleTenantChange',
  },
  
  handleTenantChange({ tenantId }) {
    console.log('Tenant changed in demo:', tenantId);
  }
};
```

## 5. 独立部署方案

### 5.1 方案概述

不改变目录结构，通过 Docker 构建时控制哪些模块被打包：

```
┌─────────────────────────────────────────────────────────────┐
│              Docker 构建时模块选择方案                       │
└─────────────────────────────────────────────────────────────┘

项目结构（不变）：
web/vue/
├── src/
│   ├── framework/
│   ├── demo/
│   ├── iam/
│   └── tenant/
└── Dockerfile

Dockerfile:
├── 接收 BUILD_MODULES 参数
├── 动态生成模块配置文件
└── Vite 构建时只打包指定模块
```

### 5.2 Dockerfile 实现

```dockerfile

# web/vue/Dockerfile

ARG NODE_VERSION=20

FROM node:\-alpine AS builder

# 构建参数：要包含的模块

ARG BUILD_MODULES=demo,iam,tenant

WORKDIR /app

# 复制 package.json

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

# 复制源码

COPY . .

# 生成模块配置文件

RUN echo "export const ENABLED_MODULES = [''];" \
    > src/config/modules.ts

# 构建

RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

### 5.3 入口文件动态导入

``` typescript
// src/main.ts
import { createApp } from 'vue';
import { setupFramework } from '@/framework';
import { ENABLED_MODULES } from '@/config/modules';

const app = createApp(App);

// 动态导入模块
const moduleLoaders: Record<string, () => Promise<ModuleDescriptor>> = {
  demo: () => import('@/demo').then(m => m.demoModule),
  iam: () => import('@/iam').then(m => m.iamModule),
  tenant: () => import('@/tenant').then(m => m.tenantModule),
};

async function bootstrap() {
  const modules = await Promise.all(
    ENABLED_MODULES.map(name => moduleLoaders[name]?.())
  );
  
  setupFramework(app, {
    modules: modules.filter(Boolean),
  });
  
  app.mount('#app');
}

bootstrap();
```

### 5.4 多容器部署示例

```yaml

# docker-compose.yml

services:

# Demo 模块独立部署

  demo-app:
    build:
      context: ./web/vue
      args:
        BUILD_MODULES: demo
    environment:
      - MODULE_BASE_PATH=/
    ports:
      - "3001:80"
  
# IAM 模块独立部署

  iam-app:
    build:
      context: ./web/vue
      args:
        BUILD_MODULES: iam
    environment:
      - MODULE_BASE_PATH=/
    ports:
      - "3002:80"
  
# 平台版（包含所有模块）

  platform-app:
    build:
      context: ./web/vue
      args:
        BUILD_MODULES: demo,iam,tenant
    ports:
      - "3000:80"
```

### 5.5 菜单与部署路径配置

后端菜单数据中配置 deployment_base_url：

| 模块 | deployment_base_url | 说明 |
|------|---------------------|------|
| demo | null | 同域部署 |
| iam | <https://iam.example.com> | 独立部署 |
| tenant | <https://tenant.example.com> | 独立部署 |

前端根据 deployment_base_url 判断是否跨域，并做相应处理。

## 6. 类型安全检测

### 6.1 TypeScript 接口约束

``` typescript
// framework/module/types.ts
import type { RouteRecordRaw, App } from 'vue';

export interface MenuItem {
  id: string;
  name: string;
  path: string;
  icon?: string;
  children?: MenuItem[];
}

export interface ModuleDescriptor {
  // 必填字段
  name: string;
  version: string;
  
  // 必填方法
  getRoutes(): RouteRecordRaw[];
  
  // 可选字段
  dependencies?: string[];
  icon?: string;
  
  // 可选方法
  getMenuItems?(): MenuItem[];
  getStores?(): Record<string, unknown>;
  setup?(app: App): void | Promise<void>;
  
  // 类型标记（用于运行时检测）
  readonly **module_descriptor**: unique symbol;
}

// 类型守卫
export function isModuleDescriptor(obj: unknown): obj is ModuleDescriptor {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    'name' in obj &&
    'version' in obj &&
    'getRoutes' in obj &&
    typeof obj.name === 'string' &&
    typeof obj.version === 'string' &&
    typeof obj.getRoutes === 'function'
  );
}
```

### 6.2 运行时验证

在模块注册中心中进行验证（见 2.3 节）：

- 类型检查
- 名称检查（小写字母、数字、连字符）
- 版本检查（semver 格式）
- 重复检查
- 路由检查

### 6.3 依赖检查

``` typescript
// framework/module/loader.ts
export function validateDependencies(
  modules: ModuleDescriptor[]
): void {
  const moduleNames = new Set(modules.map(m => m.name));
  const errors: string[] = [];
  
  for (const module of modules) {
    for (const dep of module.dependencies || []) {
      if (!moduleNames.has(dep)) {
        errors.push(
          Module "" depends on "" which is not registered
        );
      }
    }
  }
  
  if (errors.length > 0) {
    throw new Error(
      Module dependency validation failed:\n    );
  }
}
```

### 6.4 构建时检查（Vite 插件）

``` typescript
// vite-plugins/module-check.ts
import type { Plugin } from 'vite';
import { glob } from 'glob';
import fs from 'fs';

export function moduleTypeCheck(): Plugin {
  return {
    name: 'module-type-check',

    buildStart() {
      const moduleFiles = glob.sync('src/*/index.ts');
      
      for (const file of moduleFiles) {
        const content = fs.readFileSync(file, 'utf-8');
        
        // 检查是否导出了 xxxModule
        if (!/export\s+(const|let)\s+\w+Module\s*[:=]/.test(content)) {
          this.warn(
            \ should export a ModuleDescriptor (e.g., export const demoModule: ModuleDescriptor = {...})
          );
        }
      }
    },
  };
}
```

## 7. 架构全景图

```
┌─────────────────────────────────────────────────────────────┐
│               前端 Vue 模块分离架构全景图                    │
└─────────────────────────────────────────────────────────────┘

framework/
├── module/
│   ├── types.ts           # ModuleDescriptor 接口
│   ├── registry.ts        # 模块注册中心（运行时验证）
│   ├── loader.ts          # 模块加载器（依赖解析）
│   └── context.ts         # 模块上下文
├── events/
│   └── index.ts           # 事件总线
├── stores/
│   ├── user.ts            # 全局用户状态
│   ├── menu.ts            # 菜单状态（跨域支持）
│   └── app.ts             # 应用状态
└── router/
    ├── index.ts           # 动态路由注册
    └── cross-domain.ts    # 跨域路由处理

demo/
├── index.ts               # 导出 demoModule
├── router/
├── pages/
└── stores/

配置文件：
├── src/config/modules.ts  # 构建时生成
└── Dockerfile             # BUILD_MODULES 参数

后端：
├── iam/models/menu.py     # 菜单模型（BaseModel, TreeNodeMixin）
└── iam/api/menus.py       # 菜单 API
```

## 8. 改造前后对比

```
┌──────────────────────────────────────────────────────────────┐
│                    改造前 vs 改造后                           │
└──────────────────────────────────────────────────────────────┘

改造前：
┌──────────────┐
│   framework  │──────┐
│   router.ts  │      │ import
└──────────────┘      │
                      ▼
              ┌───────────────┐
              │ demo/iam/...  │
              └───────────────┘

改造后：
┌──────────────┐              ┌───────────────┐
│   framework  │◄─────────────│ demo/iam/...  │
│   registry   │  register    │   module      │
└──────────────┘              └───────────────┘
       │
       │ getRoutes()
       ▼
┌──────────────┐
│ dynamic      │
│ router       │
└──────────────┘
```

## 9. 实施步骤

### 9.1 后端实施

1. 创建菜单模型 iam/models/menu.py
2. 创建菜单-权限关联模型 iam/models/menu.py
3. 创建菜单服务 iam/services/menu_service.py
4. 创建菜单 API iam/controllers/menu_controller.py
5. 创建数据库迁移脚本
6. 初始化菜单种子数据

### 9.2 前端实施

1. 创建模块系统核心代码：
   - framework/module/types.ts
   - framework/module/registry.ts
   - framework/module/loader.ts
   - framework/module/context.ts

2. 创建事件总线：
   - framework/events/index.ts

3. 重构路由系统：
   - framework/router/index.ts - 改为动态注册
   - framework/router/cross-domain.ts - 跨域路由

4. 重构业务模块：
   - demo/index.ts - 导出 demoModule
   - iam/index.ts - 导出 iamModule
   - enant/index.ts - 导出 tenantModule

5. 创建菜单 Store：
   - framework/stores/menu.ts

6. 修改入口文件：
   - src/main.ts - 动态导入模块

7. 添加构建支持：
   - 创建 vite-plugins/module-check.ts
   - 修改 vite.config.ts
   - 创建 Dockerfile

### 9.3 测试验证

1. 单元测试：
   - 模块注册中心测试
   - 类型守卫测试
   - 依赖解析测试

2. 集成测试：
   - 动态路由注册测试
   - 跨域菜单导航测试
   - 事件总线通信测试

3. 构建测试：
   - 不同 BUILD_MODULES 组合构建
   - 独立部署验证

## 10. 风险与注意事项

### 10.1 风险点

1. **路由懒加载兼容性**：动态路由可能与部分路由懒加载方案冲突
2. **跨域 Cookie**：跨域部署需要配置 CORS 和 Cookie 策略
3. **构建体积**：动态导入可能影响代码分割效果

### 10.2 缓解措施

1. 充分测试各种路由配置场景
2. 在 Docker Compose/K8s 中配置统一的域名或使用子域名
3. 使用 Rollup 的 manualChunks 配置优化代码分割

## 11. 参考资源

- 后端模块系统：server/python/src/framework/module/
- TreeNodeMixin 设计：server/python/src/framework/database/mixins/tree.py
- 权限模型：server/python/src/iam/models/permission.py
- 角色模型：server/python/src/iam/models/role.py
