/**
 * PeopleSelect 组件类型定义
 *
 * 提供组织树节点、人员项、选择事件等类型，
 * 与后端 API 响应对齐。
 */

/** 组织树节点（用于 PeopleSelect 左侧树） */
export interface OrgTreeNode {
  /** 节点唯一标识 */
  id: string
  /** 节点名称 */
  name: string
  /** 组织编码 */
  code?: string
  /** 父节点 ID */
  parent_id?: string
  /** 树层级 */
  tree_level?: number
  /** 是否是叶子节点 */
  tree_leaf?: boolean
  /** 排序号 */
  tree_sort?: number
  /** 下级组织数量 */
  has_org_num?: number
  /** 下级人员数量 */
  has_user_num?: number
  /** 子节点 */
  children?: OrgTreeNode[]
}

/** 人员项 */
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

/** 人员选择确认事件 */
export interface PeopleSelectEvent {
  /** 选中的人员 ID 列表 */
  userIds: string[]
  /** 选中的人员对象列表 */
  users: PeopleItem[]
}

/** PeopleSelectDialog 配置选项 */
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

/** usePeopleTree 返回值 */
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
