/**
 * PeopleSelect 组件统一导出
 */

// 主组件
export { default as PeopleSelect } from './PeopleSelect.vue'
export { default as PeopleSelectDialog } from './PeopleSelectDialog.vue'
export { default as PeopleSelectView } from './PeopleSelectView.vue'
export { default as PeopleDisplay } from './PeopleDisplay.vue'

// 基础组件
export { default as PeopleAvatar } from './PeopleAvatar.vue'
export { default as OrgTreeNodeComponent } from './OrgTreeNode.vue'
export { default as UserTreeNodeComponent } from './UserTreeNode.vue'

// Composables
export { usePeopleTree } from './usePeopleTree'
export { useOrgPeopleTree } from './useOrgPeopleTree'

// 服务函数
export {
  fetchUserDetails,
  fetchOrganizationDetails,
  searchUsers,
  searchOrganizations,
  loadOrgUserTree,
  loadOrgUsers,
  clearUserCache,
  clearOrgCache,
  clearAllCache,
} from './service'

// 类型导出
export type {
  OrgTreeNode,
  PeopleItem,
  PeopleSelectEvent,
  PeopleSelectOptions,
  UsePeopleTreeReturn,
  UserItem,
  OrganizationItem,
  UserModelValue,
  UserItemValue,
  OrganizationModelValue,
  UserConfirmEvent,
  OrganizationConfirmEvent,
  CheckState,
  SelectTarget,
  FlatNode,
} from './types'

export type {
  FlatOrgNode,
  UseOrgPeopleTreeOptions,
  UseOrgPeopleTreeReturn,
} from './useOrgPeopleTree'
