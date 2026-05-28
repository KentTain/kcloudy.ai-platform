## 上下文

### 背景

当前前端架构违反依赖倒置原则：`framework/router/index.ts` 直接导入 `demo`、`iam`、`tenant` 业务模块的路由。这导致：

1. framework 层与业务模块强耦合
2. 新增模块需要修改 framework 代码
3. 无法支持构建时选择模块组合
4. 无法实现按权限动态加载菜单

### 当前状态

- 后端已有成熟的模块系统（`framework/module/`）
- 前端路由使用 Vue Router，路由配置为静态导入
- 无模块注册机制
- 无模块间通信机制

### 约束

- 对标后端 Python 模块系统设计，保持架构一致性
- 遵循 Vue 3 组合式 API 风格
- 使用 Pinia 进行状态管理
- 保持渐进式迁移，中间状态可用

### 利益相关者

- 前端开发团队：模块系统使用者
- 后端开发团队：API 提供者（菜单 API）
- DevOps 团队：构建和部署配置

## 目标 / 非目标

**目标：**

- 实现 ModuleDescriptor 接口，定义模块契约
- 实现模块注册中心，支持运行时模块注册
- 实现模块加载器，支持依赖解析和初始化顺序
- 实现事件总线，支持模块间解耦通信
- 实现动态菜单加载，从后端 API 获取菜单树
- 重构路由系统，支持动态路由注册
- 迁移 demo、iam、tenant 三个业务模块

**非目标：**

- 构建时模块选择（属于 docker-multi-module-deploy 变更）
- 跨域名部署配置（属于 docker-multi-module-deploy 变更）
- 模块热更新（HMR 支持）
- 模块版本管理和冲突检测

## 决策

### 决策 1：ModuleDescriptor 接口设计

**选择：** 定义统一的模块描述符接口

``typescript
interface ModuleDescriptor {
  // 必填
  name: string;           // 模块名称，如 'demo', 'iam'
  version: string;        // 版本号，如 '1.0.0'
  getRoutes(): RouteRecordRaw[];  // 路由配置

  // 可选
  dependencies?: string[];        // 依赖的其他模块
  icon?: string;                  // 模块图标
  getMenuItems?(): MenuItem[];    // 菜单项（本地菜单）
  getStores?(): Record<string, unknown>;  // Pinia stores
  setup?(app: App): void | Promise<void>; // 初始化钩子
}
``

**理由：**
- 对标后端 `ModuleDescriptor` 接口设计
- 必填字段保证核心功能可用
- 可选字段提供扩展能力
- `getRoutes()` 返回函数而非数组，支持动态生成

**备选方案：** 使用纯配置对象（无方法）
- **放弃理由：** 无法支持动态路由生成和初始化钩子

### 决策 2：模块注册中心设计

**选择：** 单例模式 + Map 存储

``typescript
class ModuleRegistry {
  private modules = new Map<string, ModuleDescriptor>();

  register(module: ModuleDescriptor): void;
  get(name: string): ModuleDescriptor | undefined;
  getAll(): ModuleDescriptor[];
  has(name: string): boolean;
}
``

**理由：**
- 单例保证全局唯一注册中心
- Map 提供高效的查找和遍历
- 简单的 API 易于理解和使用

**备选方案：** 使用 Vue Provide/Inject
- **放弃理由：** 需要在组件树根部提供，不如单例灵活

### 决策 3：依赖解析算法

**选择：** 拓扑排序（Kahn 算法）

**理由：**
- 检测循环依赖
- 生成正确的初始化顺序
- 时间复杂度 O(V+E)

**备选方案：** 递归解析 + 缓存
- **放弃理由：** 无法检测循环依赖，可能栈溢出

### 决策 4：事件总线设计

**选择：** 发布/订阅模式，使用 Mitt 库

``typescript
import mitt from 'mitt';

type ModuleEvents = {
  'module:loaded': { name: string };
  'menu:updated': MenuItem[];
  'route:added': RouteRecordRaw[];
};

const emitter = mitt<ModuleEvents>();
``

**理由：**
- Mitt 轻量（< 200 bytes）
- TypeScript 类型安全
- 简单的 API

**备选方案：** 使用 Pinia Store 作为事件总线
- **放弃理由：** Pinia 不是为事件流设计的，缺少订阅/取消订阅语义

### 决策 5：路由动态注册策略

**选择：** 运行时使用 `router.addRoute()`

``typescript
// 静态路由（登录、403、404）
const router = createRouter({
  routes: constantRoutes
});

// 动态注册模块路由
moduleRegistry.getAll().forEach(module => {
  const routes = module.getRoutes();
  routes.forEach(route => {
    router.addRoute('root', route);  // 添加到根路由下
  });
});
``

**理由：**
- Vue Router 原生支持动态路由
- 保持静态路由（登录、错误页）不变
- 模块路由可按需加载

**备选方案：** 构建时生成路由配置
- **放弃理由：** 无法支持运行时按权限动态加载

### 决策 6：菜单加载策略

**选择：** 优先从后端 API 加载，本地菜单作为 fallback

``typescript
// 菜单加载流程
async function loadMenu(): Promise<MenuItem[]> {
  try {
    // 1. 尝试从后端 API 加载
    const remoteMenu = await menuApi.getUserMenu();
    return remoteMenu;
  } catch (error) {
    // 2. API 失败时使用本地菜单
    const localMenu = moduleRegistry.getAll()
      .filter(m => m.getMenuItems)
      .flatMap(m => m.getMenuItems!());
    return localMenu;
  }
}
``

**理由：**
- 后端菜单支持权限控制
- 本地菜单提供降级方案
- 开发环境可无需后端

**备选方案：** 仅使用后端菜单
- **放弃理由：** 开发环境依赖后端，增加开发复杂度

### 决策 7：状态管理命名约定

**选择：** `use{模块}{功能}Store` 格式

``typescript
// 示例
useDemoExampleStore   // demo 模块的 Example Store
useIamUserStore       // iam 模块的 User Store
useTenantConfigStore  // tenant 模块的 Config Store
``

**理由：**
- 避免命名冲突
- 一眼识别模块归属
- 与 Vue 生态惯例一致

### 决策 8：迁移策略

**选择：** 渐进式迁移，先 demo 验证

**步骤：**
1. 创建模块系统核心代码
2. 迁移 demo 模块，验证设计
3. 迁移 iam 模块
4. 迁移 tenant 模块
5. 清理 router/index.ts 中的静态导入

**理由：**
- 降低风险，逐步验证
- 保持系统可用
- 便于回滚

**备选方案：** 一次性全部迁移
- **放弃理由：** 风险高，难以定位问题

## 风险 / 权衡

### 风险 1：动态路由与懒加载冲突

**缓解措施：**
- 使用 `() => import()` 语法确保代码分割
- 测试各种路由配置场景

### 风险 2：模块初始化顺序错误

**缓解措施：**
- 依赖解析算法检测循环依赖
- 抛出明确的错误信息

### 风险 3：事件总线内存泄漏

**缓解措施：**
- 模块卸载时取消订阅
- 使用 Vue `onUnmounted` 自动清理

### 风险 4：菜单 API 不可用时的降级体验

**缓解措施：**
- 本地菜单作为 fallback
- 显示友好的错误提示

## 迁移计划

### 阶段 1：模块系统核心（1-2 天）

1. 创建 `framework/module/types.ts`
2. 创建 `framework/module/registry.ts`
3. 创建 `framework/module/loader.ts`
4. 创建 `framework/module/context.ts`
5. 创建 `framework/events/index.ts`

### 阶段 2：路由重构（1 天）

1. 修改 `framework/router/index.ts` 支持动态注册
2. 创建 `framework/router/cross-domain.ts`（预留）

### 阶段 3：菜单 Store（0.5 天）

1. 创建 `framework/stores/menu.ts`
2. 实现菜单 API 调用和本地降级

### 阶段 4：业务模块迁移（1-2 天）

1. 迁移 demo 模块（创建 `demo/index.ts` 导出 demoModule）
2. 验证路由、菜单、Store 正常工作
3. 迁移 iam 模块
4. 迁移 tenant 模块

### 阶段 5：清理与验证（0.5 天）

1. 移除 `router/index.ts` 中的静态导入
2. 更新 `main.ts` 入口
3. 集成测试

### 回滚策略

每个阶段完成后打 Git tag，出问题时回滚到上一个稳定状态。

## 开放问题

1. 是否需要支持模块的异步加载（代码分割）？当前设计已支持。
2. 是否需要模块间的依赖注入机制？当前使用事件总线解耦。
3. 跨域路由的具体实现留待 docker-multi-module-deploy 变更。
