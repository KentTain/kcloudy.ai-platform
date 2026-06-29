/**
 * useTreeCheck - 树节点三态复选框逻辑
 *
 * 提供树节点的三态复选框状态管理（checked / indeterminate / unchecked）。
 * 支持级联选择：选中父节点时自动选中所有子节点。
 */

import { ref, computed, type Ref } from 'vue'

/**
 * 复选框状态
 */
export type CheckState = 'checked' | 'unchecked' | 'indeterminate'

/**
 * 树节点基础接口（最小约束）
 */
export interface CheckableTreeNode {
  /** 节点 ID */
  id: string
  /** 是否是叶子节点 */
  tree_leaf?: boolean
  /** 子节点（可选） */
  children?: CheckableTreeNode[]
}

/**
 * useTreeCheck 配置选项
 */
export interface UseTreeCheckOptions<TNode extends CheckableTreeNode> {
  /** 数据源 */
  treeData: Ref<TNode[]>

  /** 已选中的节点 ID（v-model） */
  modelValue?: Ref<string[]>

  /** 是否启用级联选择（选中父节点时自动选中所有子节点） */
  cascade?: boolean

  /** 禁用的节点 ID 列表 */
  disabledIds?: Ref<string[]> | string[]
}

/**
 * useTreeCheck 返回值
 */
export interface UseTreeCheckReturn<TNode extends CheckableTreeNode> {
  /** 选中的节点 ID 集合 */
  checkedIds: Ref<Set<string>>

  /** 半选的节点 ID 集合 */
  indeterminateIds: Ref<Set<string>>

  /** 获取节点的复选框状态 */
  getCheckState: (id: string) => CheckState

  /** 判断节点是否选中 */
  isChecked: (id: string) => boolean

  /** 判断节点是否半选 */
  isIndeterminate: (id: string) => boolean

  /** 判断节点是否禁用 */
  isDisabled: (id: string) => boolean

  /** 切换节点选中状态 */
  toggleCheck: (node: TNode) => void

  /** 选中节点 */
  checkNode: (id: string) => void

  /** 取消选中节点 */
  uncheckNode: (id: string) => void

  /** 批量选中节点 */
  checkNodes: (ids: string[]) => void

  /** 批量取消选中 */
  uncheckNodes: (ids: string[]) => void

  /** 清空所有选中 */
  clearChecked: () => void

  /** 获取所有选中的节点 ID（如果是级联模式，只返回叶子节点） */
  getCheckedIds: () => string[]
}

/**
 * 树节点三态复选框 Composable
 *
 * @description 提供树节点的三态复选框状态管理和级联选择支持
 *
 * @example
 * ```ts
 * const treeData = ref<OrgTreeNode[]>([])
 *
 * const {
 *   checkedIds,
 *   getCheckState,
 *   toggleCheck,
 *   getCheckedIds
 * } = useTreeCheck({
 *   treeData,
 *   cascade: true
 * })
 *
 * // 切换选中状态
 * toggleCheck(node)
 *
 * // 获取选中状态
 * const state = getCheckState(node.id) // 'checked' | 'unchecked' | 'indeterminate'
 *
 * // 获取所有选中的 ID
 * const ids = getCheckedIds()
 * ```
 */
export function useTreeCheck<TNode extends CheckableTreeNode>(
  options: UseTreeCheckOptions<TNode>
): UseTreeCheckReturn<TNode> {
  const {
    treeData,
    modelValue,
    cascade = true,
    disabledIds = [],
  } = options

  // ========== 状态 ==========

  /** 选中的节点 ID 集合 */
  const checkedIds = ref<Set<string>>(new Set(modelValue?.value || []))

  /** 半选的节点 ID 集合 */
  const indeterminateIds = ref<Set<string>>(new Set())

  /** 禁用的节点 ID 集合 */
  const disabledIdSet = computed<Set<string>>(() => {
    const ids = Array.isArray(disabledIds)
      ? disabledIds
      : disabledIds.value
    return new Set(ids)
  })

  // ========== 辅助函数 ==========

  /**
   * 判断节点是否禁用
   */
  function isDisabled(id: string): boolean {
    return disabledIdSet.value.has(id)
  }

  /**
   * 判断节点是否选中
   */
  function isChecked(id: string): boolean {
    return checkedIds.value.has(id)
  }

  /**
   * 判断节点是否半选
   */
  function isIndeterminate(id: string): boolean {
    return indeterminateIds.value.has(id)
  }

  /**
   * 在树中查找节点
   */
  function findNode(nodes: TNode[], id: string): TNode | null {
    for (const node of nodes) {
      if (node.id === id) return node
      if (node.children?.length) {
        const found = findNode(node.children as TNode[], id)
        if (found) return found
      }
    }
    return null
  }

  /**
   * 获取节点的所有后代节点 ID
   */
  function getDescendantIds(node: TNode): string[] {
    const ids: string[] = []

    function collect(n: TNode): void {
      ids.push(n.id)
      if (n.children?.length) {
        n.children.forEach(child => collect(child as TNode))
      }
    }

    collect(node)
    return ids
  }

  /**
   * 计算节点的复选框状态
   */
  function calculateCheckState(node: TNode): CheckState {
    // 如果节点本身被选中，返回 checked
    if (checkedIds.value.has(node.id)) {
      return 'checked'
    }

    // 叶子节点或没有子节点
    if (node.tree_leaf || !node.children?.length) {
      return 'unchecked'
    }

    // 计算子节点的选中状态
    const children = node.children as TNode[]
    let hasChecked = false
    let hasUnchecked = false
    let hasIndeterminate = false

    for (const child of children) {
      const childState = calculateCheckState(child)

      if (childState === 'checked') {
        hasChecked = true
      } else if (childState === 'unchecked') {
        hasUnchecked = true
      } else {
        hasIndeterminate = true
      }
    }

    // 所有子节点都选中
    if (hasChecked && !hasUnchecked && !hasIndeterminate) {
      return 'checked'
    }

    // 所有子节点都未选中
    if (!hasChecked && !hasIndeterminate) {
      return 'unchecked'
    }

    // 部分子节点选中
    return 'indeterminate'
  }

  /**
   * 更新所有节点的半选状态
   */
  function updateIndeterminateStates(): void {
    indeterminateIds.value.clear()

    function updateNode(node: TNode): void {
      const state = calculateCheckState(node)

      if (state === 'indeterminate') {
        indeterminateIds.value.add(node.id)
      }

      if (node.children?.length) {
        node.children.forEach(child => updateNode(child as TNode))
      }
    }

    treeData.value.forEach(node => updateNode(node))
  }

  /**
   * 获取节点的复选框状态
   */
  function getCheckState(id: string): CheckState {
    const node = findNode(treeData.value, id)

    if (!node) {
      return checkedIds.value.has(id) ? 'checked' : 'unchecked'
    }

    return calculateCheckState(node)
  }

  // ========== 操作方法 ==========

  /**
   * 选中节点
   */
  function checkNode(id: string): void {
    if (isDisabled(id)) return

    checkedIds.value.add(id)
    indeterminateIds.value.delete(id)

    // 如果启用级联，选中所有子节点
    if (cascade) {
      const node = findNode(treeData.value, id)
      if (node) {
        const descendantIds = getDescendantIds(node)
        descendantIds.forEach(descId => {
          if (!isDisabled(descId)) {
            checkedIds.value.add(descId)
          }
        })
      }
    }

    // 更新半选状态
    updateIndeterminateStates()
  }

  /**
   * 取消选中节点
   */
  function uncheckNode(id: string): void {
    if (isDisabled(id)) return

    checkedIds.value.delete(id)
    indeterminateIds.value.delete(id)

    // 如果启用级联，取消选中所有子节点
    if (cascade) {
      const node = findNode(treeData.value, id)
      if (node) {
        const descendantIds = getDescendantIds(node)
        descendantIds.forEach(descId => {
          checkedIds.value.delete(descId)
          indeterminateIds.value.delete(descId)
        })
      }
    }

    // 更新半选状态
    updateIndeterminateStates()
  }

  /**
   * 切换节点选中状态
   */
  function toggleCheck(node: TNode): void {
    const id = node.id

    if (isDisabled(id)) return

    if (checkedIds.value.has(id) || indeterminateIds.value.has(id)) {
      uncheckNode(id)
    } else {
      checkNode(id)
    }
  }

  /**
   * 批量选中节点
   */
  function checkNodes(ids: string[]): void {
    ids.forEach(id => {
      if (!isDisabled(id)) {
        checkedIds.value.add(id)
      }
    })
    updateIndeterminateStates()
  }

  /**
   * 批量取消选中
   */
  function uncheckNodes(ids: string[]): void {
    ids.forEach(id => {
      checkedIds.value.delete(id)
      indeterminateIds.value.delete(id)
    })
    updateIndeterminateStates()
  }

  /**
   * 清空所有选中
   */
  function clearChecked(): void {
    checkedIds.value.clear()
    indeterminateIds.value.clear()
  }

  /**
   * 获取所有选中的节点 ID
   *
   * 如果启用级联模式，只返回叶子节点 ID
   */
  function getCheckedIds(): string[] {
    if (!cascade) {
      return Array.from(checkedIds.value)
    }

    // 级联模式：只返回叶子节点
    const leafIds: string[] = []

    function collectLeafIds(nodes: TNode[]): void {
      for (const node of nodes) {
        if (checkedIds.value.has(node.id)) {
          // 如果是叶子节点，直接添加
          if (node.tree_leaf || !node.children?.length) {
            leafIds.push(node.id)
          } else {
            // 如果是非叶子节点，递归收集叶子节点
            collectLeafIds(node.children as TNode[])
          }
        }
      }
    }

    collectLeafIds(treeData.value)
    return leafIds
  }

  // ========== 初始化 ==========

  // 更新初始半选状态
  updateIndeterminateStates()

  return {
    checkedIds,
    indeterminateIds,
    getCheckState,
    isChecked,
    isIndeterminate,
    isDisabled,
    toggleCheck,
    checkNode,
    uncheckNode,
    checkNodes,
    uncheckNodes,
    clearChecked,
    getCheckedIds,
  }
}
