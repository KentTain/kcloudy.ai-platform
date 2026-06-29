/**
 * useTreeExpand - 树节点展开/折叠逻辑
 *
 * 提供树节点的展开状态管理和懒加载支持。
 * 可用于组织树、菜单树等需要懒加载子节点的场景。
 */

import { ref, type Ref } from 'vue'

/**
 * 树节点基础接口（最小约束）
 */
export interface ExpandableTreeNode {
  /** 节点 ID */
  id: string
  /** 是否是叶子节点 */
  tree_leaf?: boolean
  /** 子节点（可选） */
  children?: ExpandableTreeNode[]
}

/**
 * useTreeExpand 配置选项
 */
export interface UseTreeExpandOptions<TNode extends ExpandableTreeNode> {
  /** 数据源 */
  treeData: Ref<TNode[]>

  /** 懒加载函数 */
  loadChildren?: (parentId: string) => Promise<TNode[]>

  /** 默认展开层级 */
  defaultExpandLevel?: number
}

/**
 * useTreeExpand 返回值
 */
export interface UseTreeExpandReturn<TNode extends ExpandableTreeNode> {
  /** 展开的节点 ID 集合 */
  expandedIds: Ref<Set<string>>

  /** 正在加载的节点 ID 集合 */
  loadingIds: Ref<Set<string>>

  /** 判断节点是否展开 */
  isExpanded: (id: string) => boolean

  /** 判断节点是否正在加载 */
  isLoading: (id: string) => boolean

  /** 切换节点展开状态 */
  toggleExpand: (node: TNode) => Promise<void>

  /** 展开节点 */
  expandNode: (id: string) => void

  /** 折叠节点 */
  collapseNode: (id: string) => void

  /** 展开到指定层级 */
  expandToLevel: (level: number) => void

  /** 折叠所有节点 */
  collapseAll: () => void

  /** 加载根节点 */
  loadRoot: () => Promise<void>
}

/**
 * 树节点展开/折叠 Composable
 *
 * @description 提供树节点的展开状态管理和懒加载支持
 *
 * @example
 * ```ts
 * const treeData = ref<OrgTreeNode[]>([])
 *
 * const { expandedIds, toggleExpand, loadRoot } = useTreeExpand({
 *   treeData,
 *   loadChildren: async (parentId) => {
 *     return await loadOrgUserTree(parentId)
 *   },
 *   defaultExpandLevel: 1
 * })
 *
 * // 加载根节点
 * await loadRoot()
 *
 * // 切换展开状态
 * await toggleExpand(node)
 * ```
 */
export function useTreeExpand<TNode extends ExpandableTreeNode>(
  options: UseTreeExpandOptions<TNode>
): UseTreeExpandReturn<TNode> {
  const {
    treeData,
    loadChildren,
    defaultExpandLevel = 0,
  } = options

  // ========== 状态 ==========

  /** 展开的节点 ID 集合 */
  const expandedIds = ref<Set<string>>(new Set())

  /** 正在加载的节点 ID 集合 */
  const loadingIds = ref<Set<string>>(new Set())

  // ========== 方法 ==========

  /**
   * 判断节点是否展开
   */
  function isExpanded(id: string): boolean {
    return expandedIds.value.has(id)
  }

  /**
   * 判断节点是否正在加载
   */
  function isLoading(id: string): boolean {
    return loadingIds.value.has(id)
  }

  /**
   * 展开节点
   */
  function expandNode(id: string): void {
    expandedIds.value.add(id)
  }

  /**
   * 折叠节点
   */
  function collapseNode(id: string): void {
    expandedIds.value.delete(id)
  }

  /**
   * 折叠所有节点
   */
  function collapseAll(): void {
    expandedIds.value.clear()
  }

  /**
   * 切换节点展开状态
   *
   * 如果节点已展开，则折叠；如果节点已折叠，则展开。
   * 如果配置了 loadChildren 且节点未加载子节点，则懒加载子节点。
   */
  async function toggleExpand(node: TNode): Promise<void> {
    const nodeId = node.id

    // 已展开 -> 折叠
    if (expandedIds.value.has(nodeId)) {
      expandedIds.value.delete(nodeId)
      return
    }

    // 叶子节点不需要加载子节点
    if (node.tree_leaf) {
      expandedIds.value.add(nodeId)
      return
    }

    // 有子节点且已加载 -> 直接展开
    if (node.children && node.children.length > 0) {
      expandedIds.value.add(nodeId)
      return
    }

    // 需要懒加载子节点
    if (loadChildren) {
      loadingIds.value.add(nodeId)

      try {
        const children = await loadChildren(nodeId)

        // 将子节点挂载到当前节点
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(node as any).children = children

        // 展开节点
        expandedIds.value.add(nodeId)
      } catch (error) {
        console.error(`Failed to load children for node ${nodeId}:`, error)
      } finally {
        loadingIds.value.delete(nodeId)
      }
    } else {
      // 没有配置懒加载函数，直接展开
      expandedIds.value.add(nodeId)
    }
  }

  /**
   * 展开到指定层级
   *
   * @param level 目标层级（0 = 仅根节点）
   */
  function expandToLevel(level: number): void {
    if (level < 0) return

    expandedIds.value.clear()

    function collectNodesToLevel(nodes: TNode[], currentLevel: number): void {
      for (const node of nodes) {
        if (currentLevel < level && !node.tree_leaf) {
          expandedIds.value.add(node.id)

          if (node.children && node.children.length > 0) {
            collectNodesToLevel(node.children as TNode[], currentLevel + 1)
          }
        }
      }
    }

    collectNodesToLevel(treeData.value, 0)
  }

  /**
   * 加载根节点
   *
   * 调用 loadChildren 加载根节点数据
   */
  async function loadRoot(): Promise<void> {
    if (!loadChildren) {
      console.warn('loadChildren is not configured')
      return
    }

    const rootId = 'root'
    loadingIds.value.add(rootId)

    try {
      const nodes = await loadChildren(rootId)
      treeData.value = nodes

      // 根据 defaultExpandLevel 初始化展开状态
      if (defaultExpandLevel > 0) {
        expandToLevel(defaultExpandLevel)
      }
    } catch (error) {
      console.error('Failed to load root nodes:', error)
    } finally {
      loadingIds.value.delete(rootId)
    }
  }

  // ========== 初始化 ==========

  // 根据 defaultExpandLevel 初始化展开状态
  if (defaultExpandLevel > 0 && treeData.value.length > 0) {
    expandToLevel(defaultExpandLevel)
  }

  return {
    expandedIds,
    loadingIds,
    isExpanded,
    isLoading,
    toggleExpand,
    expandNode,
    collapseNode,
    expandToLevel,
    collapseAll,
    loadRoot,
  }
}
