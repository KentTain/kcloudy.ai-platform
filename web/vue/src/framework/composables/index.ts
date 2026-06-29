/**
 * Framework composables 统一导出
 */

export { useColorMode } from './useColorMode'
export { useCommandPalette } from './useCommandPalette'
export { useDebouncedSearch, createDebounce } from './useDebouncedSearch'
export { useMenuPermission } from './useMenuPermission'
export { usePermission } from './usePermission'
export { useTreeData } from './useTreeData'
export { useTreeExpand } from './useTreeExpand'
export { useTreeCheck, type CheckState } from './useTreeCheck'

// 类型导出
export type {
  FieldMapping,
  UseTreeDataOptions,
  UseTreeDataReturn,
  TreeSelectNode,
  TreeNodeTree,
  TreeNode,
} from './useTreeData'

export type {
  ExpandableTreeNode,
  UseTreeExpandOptions,
  UseTreeExpandReturn,
} from './useTreeExpand'

export type {
  CheckableTreeNode,
  UseTreeCheckOptions,
  UseTreeCheckReturn,
} from './useTreeCheck'
