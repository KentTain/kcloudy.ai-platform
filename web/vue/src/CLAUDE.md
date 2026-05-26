# Vue 前端开发指南

本文件为 Claude Code 在 Vue 前端源码目录中工作时提供指导。

## 目录结构

```text
src/
├── components/                # 通用组件
│   ├── ui/                    # UI 基础组件（CommonButton、CommonInput 等）
│   └── common/                # 通用业务组件（预留）
├── composables/               # 组合式函数（useAsync、useDebounce 等）
├── demo/                      # Demo 业务模块
├── tenant/                    # Tenant 租户管理模块
├── iam/                       # IAM 身份认证与权限模块
├── framework/                 # Framework UI框架模块
└── lib/                       # 工具库
```

## 功能模块

| 模块 | 说明 | 详细文档 |
|------|------|----------|
| components | 业务无关的通用组件，可在任意模块使用 | 见下方"组件体系" |
| composables | Vue 3 组合式函数，封装可复用的响应式逻辑 | 见下方"Composables" |
| demo | 业务演示模块：健康检查、知识库管理 | [demo/CLAUDE.md](demo/CLAUDE.md) |
| tenant | 租户管理模块：租户创建、切换、配置 | [tenant/CLAUDE.md](tenant/CLAUDE.md) |
| iam | 身份认证与权限模块：用户、角色、权限管理 | [iam/CLAUDE.md](iam/CLAUDE.md) |
| framework | 基础设施：UI框架、路由、状态管理、AppPage 页面骨架、树类型与工具 | [framework/CLAUDE.md](framework/CLAUDE.md) |

## 组件体系

### 组件层级与命名

| 层级 | 目录 | 前缀 | 示例 | 说明 |
|------|------|------|------|------|
| 技术栈通用组件 | `src/components/ui/` | `Common` | `CommonButton` | 跨模块共享的基础组件 |
| 模块级通用组件 | `{模块}/components/` | `{模块}` | `DemoDatasetCard` | 模块专用组件 |
| 框架级组件 | `framework/components/` | `App` | `AppForm` | 与框架功能耦合的组件 |

### 常用通用组件

| 组件 | 用途 |
|------|------|
| CommonButton、CommonInput、CommonModal | 基础 UI 组件 |
| CommonTree、CommonCheckboxTree、CommonSelectTree | 树组件体系 |
| CommonTable、CommonSelect | 数据展示与选择 |

### 组件开发规范

- 使用 `<script setup lang="ts">` 语法
- Props 使用 `defineProps` + `withDefaults`
- Emits 使用 `defineEmits`
- 样式使用 scoped CSS，优先使用 Tailwind 类

## Composables

常用组合式函数：

| 函数 | 说明 | 用途 |
|------|------|------|
| `useAsync` | 异步状态管理 | API 调用、加载状态 |
| `useDebounce` | 防抖处理 | 搜索输入、窗口调整 |
| `useLocalStorage` | 本地存储响应式封装 | 持久化数据 |
| `usePagination` | 分页逻辑 | 列表分页 |
| `usePermission` | 权限检查 | 按钮级权限控制 |
| `useTheme` | 主题切换 | 深色/浅色模式 |

命名规范：使用 `use` 前缀，文件名与函数名一致，返回对象包含状态和方法。

### Composable vs Store

| 场景 | 推荐 |
|------|------|
| 组件内局部状态 | Composable |
| 跨组件共享状态 | Pinia Store |
| 一次性的逻辑封装 | Composable |
| 需要持久化的全局状态 | Pinia Store |

## 树结构支持

前端提供统一的树类型定义和工具函数：

- `framework/types/tree.ts`：TreeNode、TreeNodeTree、TreeComponentNode、TreeAction 接口
- `framework/utils/tree.ts`：buildTree、flattenTree、findNodeById、getAncestors、sortByTreeSorts 函数

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](../tests/CLAUDE.md)。
