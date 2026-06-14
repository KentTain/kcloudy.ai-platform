## 上下文

树组件统一重构（2026-06-13）已完成，`common/Tree` 组件现已具备：

```
┌─────────────────────────────────────────────────────────────────┐
│                    common/Tree 能力矩阵                          │
├─────────────────────────────────────────────────────────────────┤
│  ✅ checkable: boolean      → 复选框选择                         │
│  ✅ cascade: boolean        → 级联选择（父子联动）                │
│  ✅ loadData: Function      → 异步加载子节点                     │
│  ✅ showLine: boolean       → 连接线                             │
│  ✅ disabled: boolean       → 禁用状态                           │
│  ✅ modelValue: (string|number)[] → v-model 双向绑定             │
└─────────────────────────────────────────────────────────────────┘
```

**约束：**
- `ui/tree/` 目录仅被 `ModuleDetail.vue` 使用
- `TreeComponentNode` 仅在测试文件中使用
- 无 API 变更，无后端变更

## 目标 / 非目标

**目标：**
- 移除 `ui/tree/` 目录，消除重复代码
- 移除 `TreeComponentNode` 废弃类型
- 迁移唯一的使用者 `ModuleDetail.vue`
- 更新测试和文档

**非目标：**
- 不修改 `common/Tree` 组件功能
- 不变更树组件的数据结构或 API
- 不影响后端代码

## 决策

### 1. ModuleDetail.vue 迁移策略

**选择：直接迁移到 common/Tree + TreeSelectNode**

```typescript
// 旧代码
import { Tree } from '@/components/ui/tree'
import type { TreeNodeType } from '@/components/ui/tree'

const convertToTreeNode = (menuList: ModuleMenu[]): TreeNodeType[] => {
  return menuList.map(menu => ({
    value: menu.id,    // 旧字段
    label: menu.name,  // 旧字段
    children: convertToTreeNode(menu.children)
  }))
}
```

```typescript
// 新代码
import { Tree } from '@/components'
import type { TreeSelectNode } from '@/framework/types/tree'

const convertToTreeSelectNode = (menuList: ModuleMenu[]): TreeSelectNode[] => {
  return menuList.map(menu => ({
    id: menu.id,       // 新字段
    name: menu.name,   // 新字段
    children: convertToTreeSelectNode(menu.children)
  }))
}
```

**替代方案：保留 ui/tree 作为别名**
- 缺点：增加维护负担，延迟清理

**选择理由：`common/Tree` 功能完备，直接迁移简单且彻底。**

### 2. 测试文件更新

`tests/framework/unit/utils/tree.test.ts` 中 `TreeComponentNode` 使用：

```typescript
// 旧测试数据
const componentNodes: TreeComponentNode[] = [
  { id: '1', name: '研发部', children: [...] }
]
```

改为 `TreeSelectNode`：

```typescript
const componentNodes: TreeSelectNode[] = [
  { id: '1', name: '研发部', children: [...] }
]
```

**无需修改测试逻辑**，因为 `TreeSelectNode` 接口与 `TreeComponentNode` 兼容。

### 3. 删除顺序

```
Step 1: 迁移 ModuleDetail.vue
        ↓
Step 2: 更新测试文件
        ↓
Step 3: 删除 ui/tree/ 目录
        ↓
Step 4: 删除 TreeComponentNode 类型
        ↓
Step 5: 更新文档
```

## 风险 / 权衡

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| ModuleDetail.vue 迁移遗漏 | 运行时错误 | 迁移后运行单元测试验证 |
| 文档引用遗漏 | 开发者困惑 | 全局搜索 `ui/tree` 和 `TreeNodeType` |
| 测试失败 | CI 阻塞 | 先更新测试，再删除代码 |

## 迁移计划

**Step 1: 迁移 ModuleDetail.vue**
- 文件：`web/vue/src/tenant/pages/admin/ModuleDetail.vue`
- 改动：import 路径、类型名称、字段映射

**Step 2: 更新测试文件**
- 文件：`web/vue/tests/framework/unit/utils/tree.test.ts`
- 改动：`TreeComponentNode` → `TreeSelectNode`

**Step 3: 删除 ui/tree 目录**
- 删除：`web/vue/src/components/ui/tree/` 整个目录

**Step 4: 删除废弃类型**
- 文件：`web/vue/src/framework/types/tree.ts`
- 改动：移除 `TreeComponentNode` 接口

**Step 5: 更新文档**
- 更新 CLAUDE.md 中关于 tree 组件的引用
