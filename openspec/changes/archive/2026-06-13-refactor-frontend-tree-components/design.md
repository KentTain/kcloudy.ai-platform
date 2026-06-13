## 上下文

前端树组件现状：

```
┌─────────────────────────────────────────────────────────────────┐
│                        当前问题                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  类型定义                    组件                      业务组件  │
│  ┌─────────────┐            ┌─────────────┐          ┌────────┐ │
│  │ ui/types.ts │            │  ui/Tree    │          │ Dept   │ │
│  │ value/label │◄───────────│ checkbox    │◄─────────│ Tree   │ │
│  └─────────────┘            │ cascade     │          └────────┘ │
│         │                   │ loadData    │               ▲    │
│         │ 不兼容             └─────────────┘               │    │
│         ▼                           │                       │    │
│  ┌─────────────┐            ┌─────────────┐          ┌────────┐ │
│  │framework/   │            │ common/Tree │          │ Menu   │ │
│  │ tree.ts     │◄───────────│ 展示树      │◄─────────│ Tree   │ │
│  │ id/name     │            │ 无checkbox  │          └────────┘ │
│  └─────────────┘            └─────────────┘               ▲    │
│                                     │                       │    │
│                                     │                       │    │
│                               ┌─────────────┐          ┌────────┐│
│                               │CheckboxTree │          │ Perm   ││
│                               │ 搜索过滤    │◄─────────│ Tree   ││
│                               └─────────────┘          └────────┘│
│                                                                 │
│  问题：类型转换、组件选择困难、业务组件重复代码                  │
└─────────────────────────────────────────────────────────────────┘
```

约束：
- 保持向后兼容，现有业务代码渐进式迁移
- 不影响后端 API
- 遵循 Vue 3 + TypeScript + Composition API

## 目标 / 非目标

**目标：**
- 统一树组件类型定义，与后端 TreeNodeMixin 字段命名对齐
- 合并 ui/Tree 和 common/Tree，消除选择困惑
- 抽取 useTreeData composable，消除业务组件 70% 重复代码
- 增强 common/Tree 组件能力，覆盖 checkbox/cascade/loadData

**非目标：**
- 不重构后端树模型
- 不新增树组件类型
- 不强制同步迁移所有业务代码

## 决策

### 1. 三层类型体系

```
┌─────────────────────────────────────────────────────────────────┐
│                        统一类型体系                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: TreeNode (与后端对齐)                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  interface TreeNode {                                    │   │
│  │    id: string                                             │   │
│  │    parent_id: string | null                              │   │
│  │    name: string                                           │   │
│  │    tree_level: number                                     │   │
│  │    tree_leaf: boolean                                     │   │
│  │    tree_sort, tree_sorts, tree_names, parent_ids         │   │
│  │  }                                                        │   │
│  │  用途: API 响应、数据存储                                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  Layer 2: TreeNodeTree (嵌套结构)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  interface TreeNodeTree extends TreeNode {               │   │
│  │    children?: TreeNodeTree[]                             │   │
│  │  }                                                        │   │
│  │  用途: 树形展示、buildTree() 输出                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                    │
│                            ▼                                    │
│  Layer 3: TreeSelectNode (选择器)                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  interface TreeSelectNode {                              │   │
│  │    id: string | number                                   │   │
│  │    name: string                                           │   │
│  │    children?: TreeSelectNode[]                           │   │
│  │    disabled?: boolean                                     │   │
│  │    isLeaf?: boolean   // ← 从 tree_leaf 映射             │   │
│  │  }                                                        │   │
│  │  用途: TreeSelect、CheckboxTree、选择器场景               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**替代方案**：保留两套类型，使用泛型统一
- 缺点：认知负担、转换代码仍存在

**选择理由**：三层体系清晰划分职责，与后端对齐，渐进式迁移。

### 2. useTreeData Composable API

```typescript
interface UseTreeDataOptions<TInput, TNode extends TreeSelectNode> {
  // 数据源
  source: Ref<TInput[]> | TInput[]
  
  // 字段映射（默认 id/name/children）
  fieldMapping?: {
    id?: string
    name?: string
    children?: string
  }
  
  // 选中状态
  modelValue?: Ref<(string | number)[]> | (string | number)[]
  mode?: 'single' | 'multiple'
  
  // 搜索
  searchable?: boolean
  searchQuery?: Ref<string>
  
  // 展开
  defaultExpandLevel?: number
}

interface UseTreeDataReturn<TNode> {
  // 转换后的树数据
  treeData: ComputedRef<TNode[]>
  
  // 选中状态
  selectedIds: Ref<(string | number)[]>
  selectedNodes: ComputedRef<TNode[]>
  
  // 搜索
  filteredData: ComputedRef<TNode[]>
  
  // 工具方法
  findNode: (id: string | number) => TNode | undefined
  getAncestors: (id: string | number) => TNode[]
  toggleSelect: (id: string | number) => void
  clearSelection: () => void
}

function useTreeData<TInput, TNode extends TreeSelectNode>(
  options: UseTreeDataOptions<TInput, TNode>
): UseTreeDataReturn<TNode>
```

### 3. 组件合并策略

```
┌─────────────────────────────────────────────────────────────────┐
│                      组件合并方案                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  合并前                          合并后                         │
│  ─────────────────────────────   ─────────────────────────────  │
│                                                                 │
│  ui/Tree                        → 废弃，迁移到 common/Tree      │
│  ui/TreeNode                    → 保留为内部实现                │
│  ui/tree/types.ts               → 废弃，提供 @deprecated 别名   │
│                                                                 │
│  common/Tree                    → 增强，支持 checkbox/cascade   │
│  common/CheckboxTree            → 保持，内部使用 common/Tree    │
│  common/TreeList                → 保持                         │
│  common/TreeSelect              → 适配 TreeSelectNode           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**增强后的 common/Tree Props**：

```typescript
interface TreeProps {
  // 数据
  data: TreeSelectNode[]
  
  // 选择（新增）
  checkable?: boolean          // 显示 checkbox
  cascade?: boolean            // 级联选择
  modelValue?: (string | number)[]
  multiple?: boolean
  
  // 异步加载（新增）
  loadData?: (node: TreeSelectNode, callback: (children: TreeSelectNode[]) => void) => void
  
  // 展示
  defaultExpandLevel?: number
  showLine?: boolean
  disabled?: boolean
  
  // 事件
  'on-node-click'?: (node: TreeSelectNode) => void
  'on-node-toggle'?: (node: TreeSelectNode, expanded: boolean) => void
  'update:modelValue'?: (value: (string | number)[]) => void
}
```

### 4. 业务组件重构示例

**重构前 - DepartmentTree.vue**（~100 行）：
```typescript
// 数据转换（重复）
const treeData = computed(() => 
  props.departments.map(dept => ({
    id: dept.id,
    name: dept.name,
    children: dept.children?.map(...)
  }))
)

// 选中管理（重复）
const selectedIdArray = ref<(string | number)[]>(...)
watch(() => props.modelValue, ...)

// 查找逻辑（重复）
function findDeptById(id: string) { ... }
function flattenDepartments(depts: Department[]) { ... }
```

**重构后**（~30 行）：
```typescript
const { treeData, selectedIds, findNode } = useTreeData({
  source: () => props.departments,
  modelValue: () => props.modelValue,
  mode: props.mode,
})

// 仅保留业务特化逻辑
const handleNodeSelect = (value: (string | number)[]) => {
  const dept = findNode(value[0])
  emit('node-click', { id: value[0], data: dept })
}
```

## 风险 / 权衡

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 现有代码导入路径变更 | 编译错误 | 提供 @deprecated 别名，IDE 提示迁移 |
| Props API 变更 | 运行时错误 | 保留旧 Props 作为别名，控制台警告 |
| useTreeData 学习成本 | 开发效率 | 文档 + 示例代码 + 类型提示 |
| 组件合并回归风险 | 功能缺失 | 增加测试覆盖，渐进式迁移 |

## 迁移计划

**Phase 1: 类型与 Composable（本次变更）**
1. 新增 TreeSelectNode 类型
2. 实现 toSelectNode/toSelectNodes 转换
3. 实现 useTreeData composable
4. 添加废弃标记

**Phase 2: 组件增强（本次变更）**
1. common/Tree 增加 checkbox/cascade/loadData
2. common/CheckboxTree 使用 useTreeData
3. common/TreeSelect 适配新类型

**Phase 3: 业务迁移（本次变更）**
1. DepartmentTree 使用 useTreeData
2. MenuTree 使用 useTreeData
3. PermissionTree 使用 useTreeData

**Phase 4: 清理（后续）**
1. 移除 ui/tree 目录
2. 移除废弃别名

## 开放问题

- [ ] common/Tree 的 checkbox 样式是否复用 ui/Tree 的实现？
- [ ] useTreeData 是否需要支持异步数据源？
