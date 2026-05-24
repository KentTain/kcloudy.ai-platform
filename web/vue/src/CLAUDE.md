# CLAUDE.md

本文件为 Claude Code 在 Vue 前端源码目录中工作时提供指导。

## 目录结构

```text
src/
├── components/                # 通用组件
├── composables/               # 组合式函数 (Vue)
├── demo/                      # Demo 业务模块
└── framework/                 # Framework UI框架模块
```

## 功能模块

| 模块 | 说明 | 详细文档 |
|------|------|----------|
| components | 业务无关的通用组件，可在任意模块使用 | [components/CLAUDE.md](components/CLAUDE.md) |
| composables | Vue 3 组合式函数，封装可复用的响应式逻辑 | [composables/CLAUDE.md](composables/CLAUDE.md) |
| demo | 业务演示模块：健康检查、知识库管理 | [demo/CLAUDE.md](demo/CLAUDE.md) |
| framework | 基础设施：UI框架、路由、状态管理、AppPage 页面骨架、树类型与工具 | [framework/CLAUDE.md](framework/CLAUDE.md) |

## 树结构支持

前端提供统一的树类型定义和工具函数：

- `framework/types/tree.ts`：TreeNode、TreeNodeTree、TreeComponentNode、TreeAction 接口
- `framework/utils/tree.ts`：buildTree、flattenTree、findNodeById、getAncestors、sortByTreeSorts 函数

树组件体系：

| 组件 | 用途 |
|------|------|
| CommonTree | 基础展示树 |
| CommonCheckboxTree | 勾选树（搜索、全选/半选） |
| CommonSelectTree | 下拉选择树（单选/多选） |
| CommonTreeList | 列表树（带操作按钮） |

## 组件开发规范

- 使用 `<script setup lang="ts">` 语法
- Props 使用 `defineProps` + `withDefaults`
- Emits 使用 `defineEmits`

## 测试

测试文件位于 `tests/` 目录，详见 [tests/CLAUDE.md](../tests/CLAUDE.md)。
