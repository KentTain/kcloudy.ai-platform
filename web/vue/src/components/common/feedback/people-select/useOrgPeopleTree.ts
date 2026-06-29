/**
 * useOrgPeopleTree - 组织人员树业务逻辑
 *
 * 整合树展开、三态复选框、扁平化渲染等功能。
 * 专门用于组织+人员树的场景（PeopleSelect、OrgSelect 组件）。
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import type { OrgTreeNode, UserItem, CheckState } from './types'
import { loadOrgUserTree } from './service'

/**
 * 扁平化节点类型
 */
export interface FlatOrgNode {
  /** 节点 ID */
  id: string
  /** 节点名称 */
  name: string
  /** 节点类型：org（组织）或 user（用户） */
  type: 'org' | 'user'
  /** 父节点 ID */
  parent_id: string | null
  /** 树层级 */
  tree_level: number
  /** 是否是叶子节点 */
  tree_leaf: boolean
  /** 是否展开（仅组织节点有效） */
  expanded: boolean
  /** 复选框状态 */
  checkState: CheckState
  /** 原始节点数据 */
  data: OrgTreeNode | UserItem
  /** 子组织数量（仅组织节点有效） */
  has_org_num?: number
  /** 子用户数量（仅组织节点有效） */
  has_user_num?: number
}

/**
 * useOrgPeopleTree 配置选项
 */
export interface UseOrgPeopleTreeOptions {
  /** 是否多选模式（默认 true） */
  multiple?: boolean

  /** 已选中的用户 ID（v-model） */
  modelValue?: Ref<string[]>

  /** 禁用的用户 ID 列表 */
  disabledIds?: Ref<string[]> | string[]

  /** 默认展开层级（默认 1） */
  defaultExpandLevel?: number
}

/**
 * useOrgPeopleTree 返回值
 */
export interface UseOrgPeopleTreeReturn {
  // ========== 状态 ==========
  /** 树数据 */
  treeData: Ref<OrgTreeNode[]>

  /** 扁平化的可见节点列表（用于渲染） */
  flatVisibleNodes: ComputedRef<FlatOrgNode[]>

  /** 选中的用户 ID 集合 */
  checkedUserIds: Ref<Set<string>>

  /** 半选的用户 ID 集合 */
  indeterminateUserIds: Ref<Set<string>>

  /** 展开的组织 ID 集合 */
  expandedOrgIds: Ref<Set<string>>

  /** 正在加载的组织 ID 集合 */
  loadingOrgIds: Ref<Set<string>>

  /** 是否正在加载 */
  loading: Ref<boolean>

  // ========== 方法 ==========
  /** 初始化树（加载根节点） */
  initTree: () => Promise<void>

  /** 切换组织展开状态 */
  toggleOrgExpand: (orgId: string) => Promise<void>

  /** 切换用户选中状态 */
  toggleUserCheck: (userId: string) => void

  /** 切换组织选中状态（批量选择组织下所有用户） */
  toggleOrgCheck: (orgId: string) => void

  /** 获取节点的复选框状态 */
  getCheckState: (id: string) => CheckState

  /** 获取所有选中的用户 ID */
  getCheckedUserIds: () => string[]

  /** 清空所有选中 */
  clearChecked: () => void
}

/**
 * 组织人员树 Composable
 *
 * @description 提供组织人员树的懒加载、三态复选框、扁平化渲染功能
 *
 * @example
 * ```ts
 * const {
 *   flatVisibleNodes,
 *   checkedUserIds,
 *   initTree,
 *   toggleOrgExpand,
 *   toggleUserCheck,
 *   getCheckedUserIds
 * } = useOrgPeopleTree({
 *   multiple: true,
 *   cascade: true,
 *   defaultExpandLevel: 1
 * })
 *
 * // 初始化树
 * await initTree()
 *
 * // 渲染扁平化节点
 * flatVisibleNodes.value.forEach(node => {
 *   // 渲染节点...
 * })
 *
 * // 获取选中的用户 ID
 * const userIds = getCheckedUserIds()
 * ```
 */
export function useOrgPeopleTree(
  options: UseOrgPeopleTreeOptions = {}
): UseOrgPeopleTreeReturn {
  const {
    multiple = true,
    modelValue,
    disabledIds = [],
    defaultExpandLevel = 1,
  } = options

  // ========== 状态 ==========

  /** 树数据 */
  const treeData = ref<OrgTreeNode[]>([])

  /** 展开的组织 ID 集合 */
  const expandedOrgIds = ref<Set<string>>(new Set())

  /** 正在加载的组织 ID 集合 */
  const loadingOrgIds = ref<Set<string>>(new Set())

  /** 选中的用户 ID 集合 */
  const checkedUserIds = ref<Set<string>>(new Set(modelValue?.value || []))

  /** 半选的用户 ID 集合 */
  const indeterminateUserIds = ref<Set<string>>(new Set())

  /** 全局加载状态 */
  const loading = ref(false)

  /** 禁用的用户 ID 集合 */
  const disabledIdSet = computed<Set<string>>(() => {
    const ids = Array.isArray(disabledIds) ? disabledIds : disabledIds.value
    return new Set(ids)
  })

  // ========== 辅助函数 ==========

  /**
   * 在树中查找组织节点
   */
  function findOrgNode(nodes: OrgTreeNode[], orgId: string): OrgTreeNode | null {
    for (const node of nodes) {
      if (node.id === orgId) return node
      if (node.children?.length) {
        const found = findOrgNode(node.children, orgId)
        if (found) return found
      }
    }
    return null
  }

  /**
   * 获取组织下的所有用户 ID
   */
  function getOrgUserIds(org: OrgTreeNode): string[] {
    const ids: string[] = []

    // 添加直属用户
    org.users?.forEach((user: UserItem) => {
      ids.push(user.id)
    })

    // 递归添加子组织的用户
    org.children?.forEach((child: OrgTreeNode) => {
      ids.push(...getOrgUserIds(child))
    })

    return ids
  }

  /**
   * 计算组织的复选框状态
   */
  function calculateOrgCheckState(org: OrgTreeNode): CheckState {
    const userIds = getOrgUserIds(org)

    if (userIds.length === 0) {
      return 'unchecked'
    }

    let checkedCount = 0
    let uncheckedCount = 0

    for (const userId of userIds) {
      if (checkedUserIds.value.has(userId)) {
        checkedCount++
      } else {
        uncheckedCount++
      }
    }

    if (checkedCount === userIds.length) {
      return 'checked'
    }

    if (checkedCount === 0) {
      return 'unchecked'
    }

    return 'indeterminate'
  }

  /**
   * 更新所有组织的半选状态
   */
  function updateIndeterminateStates(): void {
    indeterminateUserIds.value.clear()

    function updateOrg(org: OrgTreeNode): void {
      const state = calculateOrgCheckState(org)

      if (state === 'indeterminate') {
        indeterminateUserIds.value.add(org.id)
      }

      org.children?.forEach((child: OrgTreeNode) => updateOrg(child))
    }

    treeData.value.forEach((org: OrgTreeNode) => updateOrg(org))
  }

  /**
   * 判断用户是否禁用
   */
  function isUserDisabled(userId: string): boolean {
    return disabledIdSet.value.has(userId)
  }

  // ========== 扁平化计算 ==========

  /**
   * 扁平化可见节点
   *
   * 只包含展开路径上的节点
   */
  const flatVisibleNodes = computed<FlatOrgNode[]>(() => {
    const result: FlatOrgNode[] = []

    function flattenOrg(org: OrgTreeNode, level: number): void {
      const isExpanded = expandedOrgIds.value.has(org.id)
      const checkState = calculateOrgCheckState(org)

      // 添加组织节点
      result.push({
        id: org.id,
        name: org.name,
        type: 'org',
        parent_id: org.parent_id,
        tree_level: level,
        tree_leaf: org.tree_leaf,
        expanded: isExpanded,
        checkState,
        data: org,
        has_org_num: org.has_org_num,
        has_user_num: org.has_user_num,
      })

      // 如果展开，递归添加子节点
      if (isExpanded) {
        // 先添加子组织
        org.children?.forEach((child: OrgTreeNode) => {
          flattenOrg(child, level + 1)
        })

        // 再添加直属用户
        org.users?.forEach((user: UserItem) => {
          const userCheckState: CheckState = checkedUserIds.value.has(user.id)
            ? 'checked'
            : 'unchecked'

          result.push({
            id: user.id,
            name: user.nickname || user.username,
            type: 'user',
            parent_id: org.id,
            tree_level: level + 1,
            tree_leaf: true,
            expanded: false,
            checkState: userCheckState,
            data: user,
          })
        })
      }
    }

    treeData.value.forEach((org: OrgTreeNode) => flattenOrg(org, 0))
    return result
  })

  // ========== 操作方法 ==========

  /**
   * 初始化树（加载根节点）
   */
  async function initTree(): Promise<void> {
    loading.value = true

    try {
      const nodes = await loadOrgUserTree()
      treeData.value = nodes

      // 根据 defaultExpandLevel 初始化展开状态
      if (defaultExpandLevel > 0) {
        expandToLevel(defaultExpandLevel)
      }
    } catch (error) {
      console.error('Failed to load org user tree:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 展开到指定层级
   */
  function expandToLevel(level: number): void {
    if (level < 0) return

    expandedOrgIds.value.clear()

    function collectNodesToLevel(orgs: OrgTreeNode[], currentLevel: number): void {
      for (const org of orgs) {
        if (currentLevel < level && !org.tree_leaf) {
          expandedOrgIds.value.add(org.id)

          if (org.children?.length) {
            collectNodesToLevel(org.children, currentLevel + 1)
          }
        }
      }
    }

    collectNodesToLevel(treeData.value, 0)
  }

  /**
   * 切换组织展开状态
   */
  async function toggleOrgExpand(orgId: string): Promise<void> {
    // 已展开 -> 折叠
    if (expandedOrgIds.value.has(orgId)) {
      expandedOrgIds.value.delete(orgId)
      return
    }

    // 查找组织节点
    const org = findOrgNode(treeData.value, orgId)
    if (!org) return

    // 叶子节点不需要加载子节点
    if (org.tree_leaf) {
      expandedOrgIds.value.add(orgId)
      return
    }

    // 有子节点且已加载 -> 直接展开
    if (org.children && org.children.length > 0) {
      expandedOrgIds.value.add(orgId)
      return
    }

    // 需要懒加载子节点
    loadingOrgIds.value.add(orgId)

    try {
      const children = await loadOrgUserTree(orgId)

      // 将子节点挂载到当前组织
      org.children = children

      // 展开组织
      expandedOrgIds.value.add(orgId)
    } catch (error) {
      console.error(`Failed to load children for org ${orgId}:`, error)
    } finally {
      loadingOrgIds.value.delete(orgId)
    }
  }

  /**
   * 切换用户选中状态
   */
  function toggleUserCheck(userId: string): void {
    if (isUserDisabled(userId)) return

    if (checkedUserIds.value.has(userId)) {
      checkedUserIds.value.delete(userId)
    } else {
      if (!multiple) {
        // 单选模式：清空之前的选择
        checkedUserIds.value.clear()
      }
      checkedUserIds.value.add(userId)
    }

    // 更新半选状态
    updateIndeterminateStates()
  }

  /**
   * 切换组织选中状态（批量选择组织下所有用户）
   */
  function toggleOrgCheck(orgId: string): void {
    const org = findOrgNode(treeData.value, orgId)
    if (!org) return

    const userIds = getOrgUserIds(org)
    const currentState = calculateOrgCheckState(org)

    if (currentState === 'checked' || currentState === 'indeterminate') {
      // 取消选中所有用户
      userIds.forEach(userId => {
        if (!isUserDisabled(userId)) {
          checkedUserIds.value.delete(userId)
        }
      })
    } else {
      // 选中所有用户
      userIds.forEach(userId => {
        if (!isUserDisabled(userId)) {
          if (!multiple) {
            // 单选模式：清空之前的选择
            checkedUserIds.value.clear()
          }
          checkedUserIds.value.add(userId)
        }
      })
    }

    // 更新半选状态
    updateIndeterminateStates()
  }

  /**
   * 获取节点的复选框状态
   */
  function getCheckState(id: string): CheckState {
    // 用户节点
    if (checkedUserIds.value.has(id)) {
      return 'checked'
    }
    return 'unchecked'
  }

  /**
   * 获取所有选中的用户 ID
   */
  function getCheckedUserIds(): string[] {
    return Array.from(checkedUserIds.value)
  }

  /**
   * 清空所有选中
   */
  function clearChecked(): void {
    checkedUserIds.value.clear()
    indeterminateUserIds.value.clear()
  }

  // ========== 初始化 ==========

  // 更新初始半选状态
  updateIndeterminateStates()

  return {
    // 状态
    treeData,
    flatVisibleNodes,
    checkedUserIds,
    indeterminateUserIds,
    expandedOrgIds,
    loadingOrgIds,
    loading,

    // 方法
    initTree,
    toggleOrgExpand,
    toggleUserCheck,
    toggleOrgCheck,
    getCheckState,
    getCheckedUserIds,
    clearChecked,
  }
}
