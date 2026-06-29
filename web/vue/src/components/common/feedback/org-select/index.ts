/**
 * OrganizationSelect 组件统一导出
 */

// 主组件
export { default as OrganizationSelect } from './OrganizationSelect.vue'
export { default as OrganizationSelectDialog } from './OrganizationSelectDialog.vue'
export { default as OrganizationSelectView } from './OrganizationSelectView.vue'
export { default as OrgTreeNodeComponent } from './OrgTreeNode.vue'

// Composables
export { useOrgTree } from './useOrgTree'

// 类型导出
export type {
  OrgSelectNode,
  OrgFlatNode,
  OrgSelectOptions,
} from './types'

export type {
  OrganizationItem,
  OrganizationModelValue,
  OrganizationConfirmEvent,
  CheckState,
} from './types'

export type {
  UseOrgTreeOptions,
  UseOrgTreeReturn,
} from './useOrgTree'
