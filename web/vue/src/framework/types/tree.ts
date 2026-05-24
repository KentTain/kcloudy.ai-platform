/**
 * 树节点类型定义
 */

/** 树节点基础接口 */
export interface TreeNode {
  id: string
  parent_id: string | null
  name: string
  tree_level: number
  tree_leaf: boolean
  tree_sort: number
  tree_sorts: string
  tree_names: string
  parent_ids: string
}

/** 嵌套树节点接口 */
export interface TreeNodeTree extends TreeNode {
  children?: TreeNodeTree[]
}

/** 简化版树节点接口，用于纯展示组件 */
export interface TreeComponentNode {
  id: string | number
  name: string
  children?: TreeComponentNode[]
  [key: string]: any
}

/** 树操作按钮配置 */
export interface TreeAction {
  key: string
  label: string
  icon?: any
  visible?: (node: TreeComponentNode) => boolean
  handler: (node: TreeComponentNode) => void
}