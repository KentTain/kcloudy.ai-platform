/** biome-ignore-all lint/suspicious/noExplicitAny: 允许 any 类型用于树节点值 */
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

// 向后兼容别名
export type TreeNode = TreeNodeType;
