/**
 * Framework composables 统一导出
 */

export { useColorMode } from './useColorMode'
export { useCommandPalette } from './useCommandPalette'
export { useDebouncedSearch, createDebounce } from './useDebouncedSearch'
export { useMenuPermission } from './useMenuPermission'
export { usePermission } from './usePermission'
export { useTreeData } from './useTreeData'

// 类型导出
export type {
  FieldMapping,
  UseTreeDataOptions,
  UseTreeDataReturn,
  TreeSelectNode,
  TreeNodeTree,
  TreeNode,
} from './useTreeData'
