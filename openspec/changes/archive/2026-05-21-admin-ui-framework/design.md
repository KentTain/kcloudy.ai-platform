# Admin UI Framework 技术设计

## Context

### 当前状态

`web/vue` 项目现有实现：
- 基础布局：`MainLayout.vue`（侧栏 + 内容区）
- UI 组件：`AppButton`、`AppCard`、`AppLoading`、`AppModal` 四件套
- 样式：Tailwind CSS v4 默认配置，未定义设计令牌
- 路由：静态路由配置，无权限控制
- Demo 模块：健康检查、知识库管理页面

### 设计规范目标

根据 `docs/前端PC端设计规范及框架设计探索.md`：
- 视觉主题：浅色专业后台（蔚蓝主色 `#1677FF` + 橙红辅色 `#FF5722`）
- 布局架构：侧边栏 + 顶部导航 + TagsView + 内容区
- UI 组件：完整表单/表格/树等规范
- 权限控制：动态路由 + `v-permission` 指令

### 约束

- 不引入 Element Plus，使用 Tailwind CSS v4 + 自研组件
- 设计令牌支持 `data-theme` 扩展（预留暗色主题）
- 权限系统需与后端 `/admin/v1/menus` API 对接

## Goals / Non-Goals

**Goals:**

1. 建立设计令牌系统，统一视觉语言
2. 实现 AdminLayout 四件套（Sidebar、Navbar、TagsView、Main）
3. 扩展 UI 组件库，覆盖 80% CRUD 页面需求
4. 实现权限控制系统（动态路由 + 指令 + 拦截器）
5. Demo 模块迁移至新框架

**Non-Goals:**

1. 暗色主题实现（仅预留扩展点）
2. 数据可视化组件（ECharts 集成）
3. 多租户前端隔离（后端已有，前端仅传递租户上下文）
4. 国际化支持

## Decisions

### 1. 设计令牌实现方案

**决策**：使用 Tailwind CSS v4 `@theme` 指令定义设计令牌

**理由**：
- Tailwind CSS v4 原生支持 CSS 变量生成
- 组件可直接使用语义化 class（`bg-primary`、`text-muted`）
- 支持 `data-theme` 切换，预留暗色主题扩展

**替代方案**：
- CSS 变量单独定义：需要额外配置 Tailwind，增加维护成本
- PostCSS 插件：过度工程化，Tailwind v4 已满足需求

**实现结构**：

```css
/* framework/styles/tokens.css */
@theme {
  /* 颜色 */
  --color-surface: #f5f7fa;
  --color-surface-raised: #ffffff;
  --color-primary: #1677ff;
  --color-primary-hover: #0958d9;
  --color-primary-active: #003eb3;
  --color-primary-subtle: #e8f3ff;
  --color-secondary: #ff5722;
  --color-secondary-hover: #e64a19;
  --color-secondary-subtle: #fff3e0;
  --color-success: #10b981;
  --color-danger: #ef4444;
  --color-text: #1f2937;
  --color-text-muted: #6b7280;
  --color-text-disabled: #9ca3af;
  --color-border: #e5e7eb;
  --color-border-primary: rgba(22, 119, 255, 0.35);

  /* 圆角 */
  --radius-ui: 6px;

  /* 字体 */
  --font-sans: Inter, "PingFang SC", "Microsoft YaHei", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;
}
```

### 2. 布局架构方案

**决策**：采用经典 AdminLayout 四件套架构

**理由**：
- 符合后台管理系统惯例
- 支持侧栏折叠响应式
- TagsView 提升页面切换效率

**组件结构**：

```
framework/layouts/
├── AdminLayout.vue      # 壳布局
├── components/
│   ├── AppSidebar.vue   # 侧边栏（240px/64px 折叠）
│   ├── AppNavbar.vue    # 顶部导航（60px）
│   ├── AppTagsView.vue  # 标签页
│   └── AppMain.vue      # 内容区
```

**布局尺寸**：
- 侧边栏：展开 240px，折叠 64px
- 顶栏：60px
- TagsView：32px

### 3. UI 组件库方案

**决策**：Tailwind CSS v4 + 自研组件

**理由**：
- 保持视觉一致性，避免 Element Plus 主题覆盖成本
- 组件更轻量，符合项目需求
- 设计令牌直接应用于组件

**组件规划**：

| 组件 | 优先级 | 说明 |
|------|--------|------|
| Button | P0 | 主/次/幽灵/危险四种变体 |
| Input | P0 | 输入框（聚焦/错误态） |
| Select | P1 | 下拉选择 |
| Table | P1 | 数据表格（排序/分页） |
| Form | P1 | 表单（校验） |
| Modal | P0 | 对话框 |
| Card | P0 | 卡片容器 |
| Loading | P0 | 加载状态 |
| Tree | P2 | 树形选择 |

### 4. 权限控制方案

**决策**：动态路由 + 自定义指令 + 接口拦截

**理由**：
- 符合 RBAC 权限模型
- 动态路由减少前端硬编码
- 指令方式使用便捷

**实现方案**：

```typescript
// 动态路由
const routes = await fetchUserMenus()
routes.forEach(route => router.addRoute(route))

// 权限指令
app.directive('permission', {
  mounted(el, binding) {
    const permissions = usePermissionStore().permissions
    if (!binding.value.some(p => permissions.includes(p))) {
      el.parentNode?.removeChild(el)
    }
  }
})

// 接口拦截
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 403) {
      router.push('/403')
    }
    return Promise.reject(error)
  }
)
```

## Risks / Trade-offs

### 风险 1：UI 组件开发周期

**风险**：自研组件库开发周期较长，可能影响业务模块开发进度

**缓解措施**：
- 优先实现 P0 组件（Button、Input、Modal、Card、Loading）
- P1/P2 组件按需开发，可临时使用第三方组件过渡

### 风险 2：权限 API 依赖

**风险**：后端菜单/权限 API 尚未实现，前端开发受阻

**缓解措施**：
- 提供 mock 数据，前端独立开发
- 定义 API 契约，后端并行开发

### 风险 3：设计令牌迁移成本

**风险**：现有组件使用硬编码颜色，迁移成本较高

**缓解措施**：
- 渐进式迁移，新旧 class 共存
- 使用 Codemod 工具辅助批量替换

## Migration Plan

### 阶段 1：设计令牌（P0）

1. 创建 `framework/styles/tokens.css`
2. 更新 `tailwind.config.ts` 引入令牌
3. 迁移现有组件使用语义化 class

### 阶段 2：布局框架（P0）

1. 创建 `AdminLayout.vue` 及子组件
2. 实现侧栏折叠逻辑
3. 实现 TagsView 状态管理

### 阶段 3：UI 组件库（P1）

1. 重构现有组件（Button、Card、Loading、Modal）
2. 新增 Input、Select 组件
3. 新增 Table、Form 组件

### 阶段 4：权限系统（P1）

1. 实现 permission store
2. 实现动态路由注册
3. 实现 `v-permission` 指令
4. 实现接口拦截器

### 阶段 5：Demo 模块迁移

1. 更新路由配置
2. 迁移页面至新布局
3. 应用设计令牌

## Open Questions

1. **表格组件复杂度**：是否需要虚拟滚动、可编辑单元格等高级功能？
2. **表单校验方案**：使用 VeeValidate 还是自研校验逻辑？
3. **ECharts 主题集成**：是否需要在设计令牌中定义图表配色？
