/**
 * @deprecated 此类型已废弃，请使用 `TreeSelectNode` 替代。
 * 迁移指南：
 * - value → id
 * - label → name
 * - selected 字段已移除，请使用组件的 modelValue 管理
 *
 * 新类型导入路径: `import type { TreeSelectNode } from '@/framework/types/tree'`
 * 或从本文件导入: `import type { TreeSelectNode } from '@/components/ui/tree/types'`
 *
 * @see TreeSelectNode
 */
export interface TreeNodeType {
  children: TreeNodeType[];
  disabled?: boolean;
  isLeaf?: boolean;
  label: string;
  selected?: boolean;
  value?: any;
}

export type TreeNodeValue = TreeNodeType["value"];

export interface TreeProps {
  cascade?: boolean;
  checkable?: boolean;
  dark?: boolean;
  data?: TreeNodeType[];
  expandedValue?: TreeNodeValue[];
  expandOnRowClick?: boolean;
  loadData?: (node: TreeNodeType, callback: (children: TreeNodeType[]) => void) => void;
  modelValue?: any[];
  multiple?: boolean;
  showLine?: boolean;
}

export interface TreeNodeProps {
  cascade?: boolean;
  checkable?: boolean;
  dark?: boolean;
  expandedValues?: TreeNodeValue[];
  expandOnRowClick?: boolean;
  isLastNode?: boolean;
  level: number;
  loadData?: (node: TreeNodeType, callback: (children: TreeNodeType[]) => void) => void;
  node: TreeNodeType;
  selectedValues?: any[];
  showLine?: boolean;
}

export type TreeEmits = {
  (e: "update:modelValue", value: any[]): void;
  (e: "update:expandedValue", value: TreeNodeValue[]): void;
  (e: "on-expand", node: TreeNodeType): void;
  (e: "on-node-click", node: TreeNodeType): void;
  (e: "on-load", node: TreeNodeType): void;
};

export type TreeNodeEmits = {
  (e: "update-expanded", node: TreeNodeType, expanded: boolean): void;
  (e: "on-expand", node: TreeNodeType): void;
  (e: "on-node-click", node: TreeNodeType): void;
  (e: "on-load", node: TreeNodeType): void;
};

/**
 * @deprecated 此类型别名已废弃，请使用 `TreeSelectNode` 替代。
 * @see TreeSelectNode
 */
export type TreeNode = TreeNodeType;

// ============================================================================
// 新类型重导出 - 推荐使用
// ============================================================================

/**
 * 树选择节点接口 - 推荐使用
 *
 * 用于 TreeSelect、CheckboxTree、选择器场景的数据结构。
 * 与后端 TreeNodeMixin 字段命名对齐。
 *
 * @example
 * ```typescript
 * import type { TreeSelectNode } from '@/components/ui/tree/types'
 *
 * const nodes: TreeSelectNode[] = [
 *   { id: '1', name: 'Node 1', children: [{ id: '1-1', name: 'Child 1' }] }
 * ]
 * ```
 */
export { TreeSelectNode } from '@/framework/types/tree'
