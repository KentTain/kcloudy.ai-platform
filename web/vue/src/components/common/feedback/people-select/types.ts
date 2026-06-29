/**
 * PeopleSelect 组件类型定义
 *
 * 提供组织树节点、用户项、选择事件等类型，
 * 与后端 API 响应对齐。
 *
 * @see server/python/src/iam/schemas/org_user.py 后端 Schema 定义
 */

import type { TreeNode, TreeNodeTree } from '@/framework/types/tree'

// ==============================================================================
// 数据接口（与后端 API 响应对齐）
// ==============================================================================

/**
 * 用户简要信息
 *
 * 对应后端 UserSimpleVo
 */
export interface UserItem {
  /** 用户 ID */
  id: string
  /** 用户名 */
  username: string
  /** 昵称 */
  nickname?: string | null
  /** 头像 URL */
  avatar?: string | null
  /** 邮箱 */
  email?: string | null
  /** 状态 */
  status: string
  /** 所属组织 ID */
  org_id?: string | null
  /** 组织路径名称 */
  org_tree_names?: string | null
}

/**
 * 组织简要信息
 *
 * 对应后端 OrganizationSimpleVo，继承树节点基础字段。
 */
export interface OrganizationItem extends TreeNode {
  /** 租户 ID */
  tenant_id: string
  /** 组织名称 */
  name: string
  /** 组织编码 */
  code?: string | null
  /** 状态 */
  status: string
}

/**
 * 组织人员树节点
 *
 * 对应后端 OrgUserTreeVo，继承树节点嵌套字段。
 * 每个组织节点包含直属人员列表和子组织列表。
 */
export interface OrgTreeNode extends TreeNodeTree {
  /** 租户 ID */
  tenant_id: string
  /** 组织名称 */
  name: string
  /** 组织编码 */
  code?: string | null
  /** 状态 */
  status: string
  /** 直属子组织数量 */
  has_org_num: number
  /** 直属人员数量 */
  has_user_num: number
  /** 直属人员列表 */
  users: UserItem[]
  /** 子节点 */
  children?: OrgTreeNode[]
}

// ==============================================================================
// 值类型（用于 v-model）
// ==============================================================================

/**
 * 用户选择器值类型
 *
 * 单选模式：string（用户 ID）
 * 多选模式：string[]（用户 ID 数组）
 */
export type UserModelValue = string | string[]

/**
 * 用户项值类型
 *
 * 用于需要完整用户信息的场景
 */
export interface UserItemValue {
  /** 用户 ID */
  id: string
  /** 用户名 */
  username: string
  /** 昵称 */
  nickname?: string | null
}

/**
 * 组织选择器值类型
 *
 * 单选模式：string（组织 ID）
 * 多选模式：string[]（组织 ID 数组）
 */
export type OrganizationModelValue = string | string[]

// ==============================================================================
// 事件类型
// ==============================================================================

/**
 * 用户选择确认事件
 */
export interface UserConfirmEvent {
  /** 选中的人员 ID 列表 */
  ids: string[]
  /** 选中的人员对象列表 */
  items: UserItem[]
}

/**
 * 组织选择确认事件
 */
export interface OrganizationConfirmEvent {
  /** 选中的组织 ID 列表 */
  ids: string[]
  /** 选中的组织对象列表 */
  items: OrganizationItem[]
}

// ==============================================================================
// 内部状态类型
// ==============================================================================

/**
 * 复选框状态
 */
export type CheckState = 'checked' | 'unchecked' | 'indeterminate'

/**
 * 选择目标类型
 */
export type SelectTarget = 'user' | 'organization'

/**
 * 扁平化树节点
 *
 * 用于树形数据的平面化展示和快速查找
 */
export interface FlatNode {
  /** 节点 ID */
  id: string
  /** 节点名称 */
  name: string
  /** 父节点 ID */
  parent_id: string | null
  /** 树层级 */
  tree_level: number
  /** 是否是叶子节点 */
  tree_leaf: boolean
  /** 是否展开 */
  expanded: boolean
  /** 复选框状态 */
  checkState: CheckState
  /** 原始节点数据 */
  data: OrgTreeNode | UserItem
}

// ==============================================================================
// 兼容旧接口（向后兼容）
// ==============================================================================

/**
 * 旧版人员项（已废弃）
 *
 * @deprecated 使用 UserItem 代替，字段 user_id 改为 id
 */
export interface PeopleItem {
  /** 用户 ID */
  user_id: string
  /** 用户名 */
  username: string
  /** 昵称 */
  nickname?: string
  /** 邮箱 */
  email?: string
  /** 手机号 */
  phone?: string
  /** 状态 */
  status: string
  /** 是否部门负责人 */
  is_leader?: boolean
}

/**
 * 旧版人员选择确认事件（已废弃）
 *
 * @deprecated 使用 UserConfirmEvent 代替
 */
export interface PeopleSelectEvent {
  /** 选中的人员 ID 列表 */
  userIds: string[]
  /** 选中的人员对象列表 */
  users: PeopleItem[]
}

/**
 * PeopleSelectDialog 配置选项（兼容旧版）
 *
 * @deprecated 将在新版本中重构
 */
export interface PeopleSelectOptions {
  /** 是否多选模式（默认 true） */
  multiple?: boolean
  /** 禁用的人员 ID 列表 */
  disabledIds?: string[]
  /** 已选中的人员 ID 列表 */
  modelValue?: string[]
  /** 弹窗标题 */
  title?: string
  /** 确认按钮文本 */
  confirmText?: string
  /** 组织树 API 请求函数 */
  loadOrgNodes: (parentId?: string) => Promise<OrgTreeNode[]>
  /** 人员搜索 API 函数 */
  searchPeople: (keyword: string) => Promise<PeopleItem[]>
  /** 加载组织下人员 API 函数 */
  loadOrgPeople: (orgId: string) => Promise<PeopleItem[]>
}

/**
 * usePeopleTree 返回值（兼容旧版）
 *
 * @deprecated 将在新版本中重构
 */
export interface UsePeopleTreeReturn {
  /** 组织树数据 */
  treeData: OrgTreeNode[]
  /** 选中的人员 ID 集合 */
  selectedIds: Set<string>
  /** 选中的人员列表 */
  selectedPeople: PeopleItem[]
  /** 右侧显示的人员列表 */
  displayPeople: PeopleItem[]
  /** 搜索关键词 */
  searchKeyword: string
  /** 是否加载中 */
  loading: boolean
  /** 当前选中的组织 ID */
  currentOrgId: string | null
  /** 切换人员选中状态 */
  togglePerson: (person: PeopleItem) => void
  /** 加载子组织 */
  loadChildren: (orgId: string) => Promise<void>
  /** 搜索 */
  handleSearch: (keyword: string) => void
  /** 选中组织 */
  selectOrg: (orgId: string) => void
  /** 清空选择 */
  clearSelection: () => void
}
