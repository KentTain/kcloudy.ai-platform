/**
 * PeopleSelect 组件统一导出
 */

export { default as PeopleSelectDialog } from "./PeopleSelectDialog.vue"
export { default as PeopleSelectView } from "./PeopleSelectView.vue"

// Composables
export { usePeopleTree } from "./usePeopleTree"
export { useOrgPeopleTree } from "./useOrgPeopleTree"

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
} from "./types"

export type {
  FlatOrgNode,
  UseOrgPeopleTreeOptions,
  UseOrgPeopleTreeReturn,
} from "./useOrgPeopleTree"
