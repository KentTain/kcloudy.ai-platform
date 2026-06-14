/**
 * 统一树节点类型体系
 *
 * 三层类型体系，与后端 TreeNodeMixin 字段命名对齐：
 *
 * @example
 * ```ts
 * // Layer 1: TreeNode — API 响应、数据存储（与后端对齐）
 * // Layer 2: TreeNodeTree — 树形展示，buildTree() 输出
 * // Layer 3: TreeSelectNode — TreeSelect、CheckboxTree、选择器场景
 *
 * import type { TreeNode, TreeNodeTree, TreeSelectNode } from '@/framework/types/tree'
 * import { toSelectNode, toSelectNodes } from '@/framework/utils/tree'
 * ```
 *
 * @see {@link ../utils/tree.ts} 转换函数 toSelectNode / toSelectNodes
 * @see {@link ../composables/useTreeData.ts} useTreeData composable
 */

/**
 * 树节点基础接口（Layer 1）
 *
 * 字段命名与后端 TreeNodeMixin 完全对齐。
 * 用于 API 响应、数据存储、平铺列表。
 *
 * @see TreeNodeMixin 后端树模型
 */
export interface TreeNode {
  /** 节点唯一标识 */
  id: string
  /** 父节点 ID，null 表示根节点 */
  parent_id: string | null
  /** 节点名称 */
  name: string
  /** 树层级（从 0 开始） */
  tree_level: number
  /** 是否是叶子节点 */
  tree_leaf: boolean
  /** 排序号 */
  tree_sort: number
  /** 排序路径（逗号分隔的格式化排序号） */
  tree_sorts: string
  /** 名称路径（树名称分隔符连接的祖先名称） */
  tree_names: string
  /** 祖先 ID 路径（逗号分隔的祖先 ID） */
  parent_ids: string
}

/**
 * 嵌套树节点接口（Layer 2）
 *
 * 继承 TreeNode，添加 children 属性。
 * 用于树形数据展示、buildTree() 输出。
 */
export interface TreeNodeTree extends TreeNode {
  /** 子节点列表 */
  children?: TreeNodeTree[]
}

/**
 * 树操作按钮配置
 *
 * @template TNode 树节点类型，默认为 TreeSelectNode
 */
export interface TreeAction {
  /** 按钮唯一标识 */
  key: string
  /** 按钮显示文本 */
  label: string
  /** 按钮图标组件 */
  icon?: any
  /** 按钮可见性判断函数 */
  visible?: (node: TreeSelectNode) => boolean
  /** 按钮点击处理函数 */
  handler: (node: TreeSelectNode) => void
}

/**
 * 树选择节点接口（Layer 3）
 *
 * 用于 TreeSelect、CheckboxTree、TreeList 以及所有选择器场景。
 * 字段命名与 TreeNode 对齐（id/name vs value/label）。
 *
 * @example
 * ```ts
 * import type { TreeSelectNode } from '@/framework/types/tree'
 *
 * const nodes: TreeSelectNode[] = [
 *   { id: '1', name: '根节点', children: [{ id: '1-1', name: '子节点' }] }
 * ]
 * ```
 *
 * @see {@link ../utils/tree.ts#toSelectNode} 从 TreeNode 转换
 * @see {@link ../composables/useTreeData.ts#useTreeData} useTreeData composable
 */
export interface TreeSelectNode {
  /** 节点唯一标识 */
  id: string | number
  /** 节点名称 */
  name: string
  /** 子节点列表 */
  children?: TreeSelectNode[]
  /** 是否禁用（不从 TreeNode 映射，需手动设置） */
  disabled?: boolean
  /** 是否为叶子节点（从 TreeNode.tree_leaf 映射） */
  isLeaf?: boolean
}