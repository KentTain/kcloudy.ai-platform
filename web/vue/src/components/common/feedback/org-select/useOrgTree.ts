/**
 * useOrgTree — 组织选择树核心逻辑 Composable
 *
 * 封装组织树的加载、展开/折叠、选择状态、搜索过滤等核心逻辑。
 * 内部使用 useTreeExpand 和 useTreeCheck 实现树操作能力。
 */

import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { useTreeExpand } from '@/framework/composables/useTreeExpand'
import { useTreeCheck } from '@/framework/composables/useTreeCheck'
import { loadOrgUserTree } from '../people-select/service'
import type {
  OrgSelectNode,
  OrgFlatNode,
  OrganizationItem,
  CheckState,
} from './types'
import type { OrgTreeNode } from '../people-select/types'

// ==============================================================================
// 类型定义
// ==============================================================================

/**
 * useOrgTree 配置选项
 */
export interface UseOrgTreeOptions {
  /** 是否多选模式（默认 true） */
  multiple?: boolean
  /** 是否启用级联选择（默认 true） */
  cascade?: boolean
  /** 禁用的组织 ID 列表 */
  disabledIds?: string[]
  /** 已选中的组织 ID 列表 */
  modelValue?: string[]
  /** 默认展开层级 */
  defaultExpandLevel?: number
}

/**
 * useOrgTree 返回值
 */
export interface UseOrgTreeReturn {
  // ========== 状态 ==========
  /** 树形数据 */
  treeData: Ref<OrgSelectNode[]>
  /** 扁平化可见节点（用于渲染优化） */
  flatVisibleNodes: ComputedRef<OrgFlatNode[]>
  /** 选中的节点 ID 集合 */
  checkedIds: Ref<Set<string>>
  /** 展开的节点 ID 集合 */
  expandedIds: Ref<Set<string>>
  /** 加载状态 */
  loading: Ref<boolean>
  /** 搜索关键词 */
  searchKeyword: Ref<string>

  // ========== 方法 ==========
  /** 加载根节点 */
  loadRoot: () => Promise<void>
  /** 切换节点展开状态 */
  toggleExpand: (id: string) => void
  /** 切换节点选中状态 */
  toggleCheck: (id: string) => void
  /** 设置搜索关键词 */
  setSearchKeyword: (keyword: string) => void
  /** 清空选择 */
  clearSelection: () => void
  /** 获取选中的组织列表 */
  getSelectedOrgs: () => OrganizationItem[]
}

// ==============================================================================
// 辅助函数
// ==============================================================================

/**
 * 将 OrgTreeNode 转换为 OrgSelectNode
 *
 * @param node - 原始组织树节点
 * @returns 组织选择节点
 */
function toOrgSelectNode(node: OrgTreeNode): OrgSelectNode {
  const selectNode: OrgSelectNode = {
    id: node.id,
    parent_id: node.parent_id,
    name: node.name,
    tree_level: node.tree_level,
    tree_leaf: node.tree_leaf,
    tree_sort: node.tree_sort,
    tree_sorts: node.tree_sorts,
    tree_names: node.tree_names,
    parent_ids: node.parent_ids,
    tenant_id: node.tenant_id,
    code: node.code,
    status: node.status,
    has_children: !node.tree_leaf && (node.has_org_num > 0 || !node.tree_leaf),
  }

  // 递归转换子节点
  if (node.children?.length) {
    selectNode.children = node.children.map(toOrgSelectNode)
  }

  return selectNode
}

/**
 * 扁平化树节点（仅展开状态可见的节点）
 *
 * @param nodes - 树节点列表
 * @param expandedIds - 展开的节点 ID 集合
 * @param getCheckState - 获取复选框状态的函数
 * @param keyword - 搜索关键词（可选）
 * @returns 扁平化节点列表
 */
function flattenVisibleNodes(
  nodes: OrgSelectNode[],
  expandedIds: Set<string>,
  getCheckState: (id: string) => CheckState,
  keyword?: string
): OrgFlatNode[] {
  const result: OrgFlatNode[] = []
  const lowerKeyword = keyword?.toLowerCase()

  function traverse(
    nodeList: OrgSelectNode[],
    parentExpanded: boolean,
    matchedParent: boolean
  ): void {
    for (const node of nodeList) {
      // 搜索过滤：检查当前节点或子节点是否匹配
      const nodeMatches = lowerKeyword
        ? node.name.toLowerCase().includes(lowerKeyword) ||
          (node.code?.toLowerCase().includes(lowerKeyword) ?? false)
        : true

      // 如果父节点匹配或当前节点匹配，则显示
      const shouldShow = matchedParent || nodeMatches

      if (!shouldShow) {
        // 检查子节点是否有匹配的
        if (node.children?.length) {
          const hasMatchingChild = checkMatchingChildren(
            node.children,
            lowerKeyword
          )
          if (!hasMatchingChild) continue
        } else {
          continue
        }
      }

      // 只有父节点展开时才添加到结果
      if (parentExpanded) {
        result.push({
          id: node.id,
          name: node.name,
          parent_id: node.parent_id,
          tree_level: node.tree_level,
          tree_leaf: node.tree_leaf,
          expanded: expandedIds.has(node.id),
          checkState: getCheckState(node.id),
          data: node,
        })
      }

      // 递归处理子节点
      if (node.children?.length) {
        const isExpanded = expandedIds.has(node.id) || !!lowerKeyword // 搜索时自动展开
        traverse(
          node.children,
          parentExpanded && isExpanded,
          matchedParent || nodeMatches
        )
      }
    }
  }

  traverse(nodes, true, false)
  return result
}

/**
 * 检查子节点是否有匹配搜索关键词的
 */
function checkMatchingChildren(
  children: OrgSelectNode[],
  keyword?: string
): boolean {
  if (!keyword) return true

  const lowerKeyword = keyword.toLowerCase()

  for (const child of children) {
    if (
      child.name.toLowerCase().includes(lowerKeyword) ||
      (child.code?.toLowerCase().includes(lowerKeyword) ?? false)
    ) {
      return true
    }
    if (child.children?.length && checkMatchingChildren(child.children, keyword)) {
      return true
    }
  }

  return false
}

/**
 * 收集匹配搜索关键词的节点及其祖先节点 ID
 */
function collectMatchingNodeIds(
  nodes: OrgSelectNode[],
  keyword: string
): Set<string> {
  const matchingIds = new Set<string>()
  const lowerKeyword = keyword.toLowerCase()

  function traverse(nodeList: OrgSelectNode[], ancestors: string[]): void {
    for (const node of nodeList) {
      const currentPath = [...ancestors, node.id]
      const isMatch =
        node.name.toLowerCase().includes(lowerKeyword) ||
        (node.code?.toLowerCase().includes(lowerKeyword) ?? false)

      if (isMatch) {
        // 将匹配节点及其祖先加入结果
        currentPath.forEach((id) => matchingIds.add(id))
      }

      if (node.children?.length) {
        traverse(node.children, currentPath)
      }
    }
  }

  traverse(nodes, [])
  return matchingIds
}

/**
 * 将 OrgSelectNode 转换为 OrganizationItem
 */
function toOrganizationItem(node: OrgSelectNode): OrganizationItem {
  return {
    id: node.id,
    parent_id: node.parent_id,
    name: node.name,
    tree_level: node.tree_level,
    tree_leaf: node.tree_leaf,
    tree_sort: node.tree_sort,
    tree_sorts: node.tree_sorts,
    tree_names: node.tree_names,
    parent_ids: node.parent_ids,
    tenant_id: node.tenant_id,
    code: node.code,
    status: node.status,
  }
}

// ==============================================================================
// Composable 实现
// ==============================================================================

/**
 * 组织选择树 Composable
 *
 * @description 提供组织树的加载、展开/折叠、选择状态、搜索过滤等功能
 *
 * @example
 * ```ts
 * const {
 *   treeData,
 *   flatVisibleNodes,
 *   checkedIds,
 *   loadRoot,
 *   toggleExpand,
 *   toggleCheck,
 *   setSearchKeyword,
 *   getSelectedOrgs,
 * } = useOrgTree({
 *   multiple: true,
 *   cascade: true,
 *   defaultExpandLevel: 1,
 * })
 *
 * // 加载根节点
 * await loadRoot()
 *
 * // 搜索
 * setSearchKeyword('研发')
 *
 * // 获取选中项
 * const selectedOrgs = getSelectedOrgs()
 * ```
 */
export function useOrgTree(options: UseOrgTreeOptions = {}): UseOrgTreeReturn {
  const {
    multiple = true,
    cascade = true,
    disabledIds = [],
    modelValue = [],
    defaultExpandLevel = 1,
  } = options

  // ========== 响应式状态 ==========

  /** 树形数据 */
  const treeData = ref<OrgSelectNode[]>([])

  /** 加载状态 */
  const loading = ref(false)

  /** 搜索关键词 */
  const searchKeyword = ref('')

  /** 匹配搜索的节点 ID 集合 */
  const matchingNodeIds = ref<Set<string>>(new Set())

  // ========== useTreeExpand 集成 ==========

  /**
   * 懒加载子节点
   */
  async function loadChildren(parentId: string): Promise<OrgSelectNode[]> {
    const nodes = await loadOrgUserTree(parentId)
    return nodes.map(toOrgSelectNode)
  }

  const {
    expandedIds,
    toggleExpand: toggleExpandInternal,
    expandNode,
    expandToLevel,
  } = useTreeExpand<OrgSelectNode>({
    treeData,
    loadChildren,
    defaultExpandLevel,
  })

  // ========== useTreeCheck 集成 ==========

  const {
    checkedIds,
    getCheckState,
    toggleCheck: toggleCheckInternal,
    checkNodes,
    clearChecked,
    getCheckedIds,
  } = useTreeCheck<OrgSelectNode>({
    treeData,
    cascade,
    modelValue: ref(modelValue),
    disabledIds,
  })

  // ========== 计算属性 ==========

  /**
   * 扁平化可见节点
   */
  const flatVisibleNodes = computed<OrgFlatNode[]>(() => {
    const keyword = searchKeyword.value.trim()

    // 搜索模式：展开所有匹配节点的路径
    if (keyword) {
      return flattenVisibleNodes(
        treeData.value,
        expandedIds.value,
        getCheckState,
        keyword
      )
    }

    // 正常模式：仅显示展开状态的节点
    return flattenVisibleNodes(
      treeData.value,
      expandedIds.value,
      getCheckState
    )
  })

  // ========== 方法实现 ==========

  /**
   * 加载根节点
   */
  async function loadRoot(): Promise<void> {
    loading.value = true

    try {
      // 调用 loadOrgUserTree 获取根节点
      const nodes = await loadOrgUserTree('root')

      // 转换为 OrgSelectNode
      treeData.value = nodes.map(toOrgSelectNode)

      // 初始化选中状态（如果有 modelValue）
      if (modelValue.length > 0) {
        checkNodes(modelValue)
      }

      // 展开到指定层级
      if (defaultExpandLevel > 0) {
        expandToLevel(defaultExpandLevel)
      }
    } catch (error) {
      console.error('Failed to load organization tree:', error)
      treeData.value = []
    } finally {
      loading.value = false
    }
  }

  /**
   * 切换节点展开状态
   */
  async function toggleExpand(id: string): Promise<void> {
    const node = findNode(treeData.value, id)
    if (node) {
      await toggleExpandInternal(node)
    }
  }

  /**
   * 切换节点选中状态
   */
  function toggleCheck(id: string): void {
    const node = findNode(treeData.value, id)
    if (node) {
      // 单选模式：先清空再选中
      if (!multiple) {
        clearChecked()
      }
      toggleCheckInternal(node)
    }
  }

  /**
   * 设置搜索关键词
   */
  function setSearchKeyword(keyword: string): void {
    searchKeyword.value = keyword

    // 如果有搜索关键词，展开匹配节点的路径
    if (keyword.trim()) {
      const matchingIds = collectMatchingNodeIds(
        treeData.value,
        keyword.trim()
      )
      matchingNodeIds.value = matchingIds

      // 自动展开匹配节点及其祖先
      matchingIds.forEach((id) => {
        const node = findNode(treeData.value, id)
        if (node && !node.tree_leaf) {
          expandNode(id)
        }
      })
    } else {
      matchingNodeIds.value.clear()
    }
  }

  /**
   * 清空选择
   */
  function clearSelection(): void {
    clearChecked()
  }

  /**
   * 获取选中的组织列表
   */
  function getSelectedOrgs(): OrganizationItem[] {
    const checkedIdList = getCheckedIds()
    const result: OrganizationItem[] = []

    function collectSelected(nodes: OrgSelectNode[]): void {
      for (const node of nodes) {
        if (checkedIdList.includes(node.id)) {
          result.push(toOrganizationItem(node))
        }
        if (node.children?.length) {
          collectSelected(node.children)
        }
      }
    }

    collectSelected(treeData.value)
    return result
  }

  // ========== 辅助函数 ==========

  /**
   * 查找节点
   */
  function findNode(nodes: OrgSelectNode[], id: string): OrgSelectNode | null {
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children?.length) {
        const found = findNode(node.children, id)
        if (found) return found
      }
    }
    return null
  }

  // ========== 返回 ==========

  return {
    // 状态
    treeData,
    flatVisibleNodes,
    checkedIds,
    expandedIds,
    loading,
    searchKeyword,

    // 方法
    loadRoot,
    toggleExpand,
    toggleCheck,
    setSearchKeyword,
    clearSelection,
    getSelectedOrgs,
  }
}
