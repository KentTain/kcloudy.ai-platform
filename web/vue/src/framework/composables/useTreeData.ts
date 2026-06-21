/**
 * useTreeData composable
 * 提供树形数据的转换、选中状态管理、搜索过滤等功能
 */

import {
  computed,
  ref,
  toRef,
  type Ref,
  type ComputedRef,
  unref,
} from 'vue'
import type { TreeSelectNode, TreeNodeTree, TreeNode } from '@/framework/types/tree'

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 字段映射配置
 * 用于将输入数据的字段映射到标准字段名
 */
export interface FieldMapping {
  /** ID 字段名，默认 'id' */
  id?: string
  /** 名称字段名，默认 'name' */
  name?: string
  /** 子节点字段名，默认 'children' */
  children?: string
}

/**
 * useTreeData 配置选项
 */
export interface UseTreeDataOptions<TInput> {
  /** 数据源，支持 getter 函数、Ref 或原始数组 */
  source: (() => TInput[]) | Ref<TInput[]> | TInput[]

  /** 字段映射配置 */
  fieldMapping?: FieldMapping

  /** 选中状态 v-model，支持 Ref 或原始数组 */
  modelValue?: Ref<(string | number)[]> | (string | number)[]

  /** 选择模式：单选或多选 */
  mode?: 'single' | 'multiple'

  /** 是否启用搜索功能 */
  searchable?: boolean

  /** 搜索关键词，支持 Ref */
  searchQuery?: Ref<string>

  /** 默认展开层级，0 表示只展开根节点 */
  defaultExpandLevel?: number
}

/**
 * useTreeData 返回值
 */
export interface UseTreeDataReturn<TNode extends TreeSelectNode> {
  /** 转换后的树数据 */
  treeData: ComputedRef<TNode[]>

  /** 选中节点 ID 列表 */
  selectedIds: Ref<(string | number)[]>

  /** 选中的节点对象列表 */
  selectedNodes: ComputedRef<TNode[]>

  /** 过滤后的树数据（搜索时使用） */
  filteredData: ComputedRef<TNode[]>

  /** 展开的节点 ID 集合 */
  expandedIds: Ref<Set<string | number>>

  /** 切换节点展开状态 */
  toggleExpand: (id: string | number) => void

  /** 展开到指定层级 */
  expandToLevel: (level: number) => void

  /** 查找节点 */
  findNode: (id: string | number) => TNode | undefined

  /** 获取祖先节点 */
  getAncestors: (id: string | number) => TNode[]

  /** 切换选中状态 */
  toggleSelect: (id: string | number) => void

  /** 清空选中状态 */
  clearSelection: () => void
}

// ============================================================================
// 内部工具函数
// ============================================================================

/**
 * 获取对象字段值
 */
function getFieldValue<T extends object>(obj: T, field: string): unknown {
  return (obj as Record<string, unknown>)[field]
}

/**
 * 转换单个节点数据
 */
function transformNode<TInput extends object>(
  input: TInput,
  mapping: Required<FieldMapping>
): TreeSelectNode {
  const id = getFieldValue(input, mapping.id)
  const name = getFieldValue(input, mapping.name)
  const children = getFieldValue(input, mapping.children)

  const node: Record<string, unknown> = {
    id: id as string | number,
    name: name as string,
  }

  // 复制其他属性（排除映射字段）
  const excludeFields = new Set([mapping.id, mapping.name, mapping.children])
  for (const key of Object.keys(input as object)) {
    if (!excludeFields.has(key)) {
      node[key] = getFieldValue(input, key)
    }
  }

  // 递归转换子节点
  if (Array.isArray(children) && children.length > 0) {
    node.children = children.map((child) => transformNode<TInput>(child, mapping))
  }

  return node as unknown as TreeSelectNode
}

/**
 * 转换输入数据为标准树节点格式
 */
function transformTreeData<TInput extends object>(
  source: TInput[],
  mapping: Required<FieldMapping>
): TreeSelectNode[] {
  if (!source || source.length === 0) return []
  return source.map((item) => transformNode<TInput>(item, mapping))
}

/**
 * 在树中递归搜索匹配的节点
 * 返回包含匹配节点的完整树（包含匹配节点的祖先路径）
 */
function searchInTree<TNode extends TreeSelectNode>(
  tree: TNode[],
  query: string,
  fieldMapping: Required<FieldMapping>
): TNode[] {
  if (!query.trim()) return tree

  const lowerQuery = query.toLowerCase()
  const result: TNode[] = []

  for (const node of tree) {
    const name = String(node.name).toLowerCase()
    const isMatch = name.includes(lowerQuery)
    const children = node.children as TNode[] | undefined

    // 递归搜索子节点
    let matchedChildren: TNode[] = []
    if (children && children.length > 0) {
      matchedChildren = searchInTree(children, query, fieldMapping)
    }

    // 如果当前节点匹配或有匹配的子节点，则包含该节点
    if (isMatch || matchedChildren.length > 0) {
      const newNode: TNode = {
        ...node,
        children: matchedChildren.length > 0 ? matchedChildren : children,
      } as TNode
      result.push(newNode)
    }
  }

  return result
}

/**
 * 在树中查找节点（支持 string | number 类型的 id）
 */
function findNodeInTree<TNode extends TreeSelectNode>(
  tree: TNode[],
  id: string | number
): TNode | undefined {
  for (const node of tree) {
    if (node.id === id) return node
    if (node.children?.length) {
      const found = findNodeInTree(node.children as TNode[], id)
      if (found) return found
    }
  }
  return undefined
}

/**
 * 获取节点的祖先节点
 */
function getAncestorsInTree<TNode extends TreeSelectNode>(
  tree: TNode[],
  targetId: string | number
): TNode[] {
  const ancestors: TNode[] = []

  function walk(nodes: TNode[], target: string | number): boolean {
    for (const node of nodes) {
      if (node.id === target) {
        return true
      }
      if (node.children?.length) {
        if (walk(node.children as TNode[], target)) {
          ancestors.unshift(node)
          return true
        }
      }
    }
    return false
  }

  walk(tree, targetId)
  return ancestors
}

// ============================================================================
// Composable 实现
// ============================================================================

/**
 * 树数据处理 composable
 *
 * @description 提供树形数据的转换、选中状态管理、搜索过滤等功能
 *
 * @example
 * ```ts
 * // 基础用法
 * const { treeData, selectedIds, toggleSelect } = useTreeData({
 *   source: rawDepartments,
 *   mode: 'multiple'
 * })
 *
 * // 带搜索功能
 * const { treeData, filteredData, selectedNodes } = useTreeData({
 *   source: rawDepartments,
 *   searchable: true,
 *   searchQuery: searchKeyword
 * })
 *
 * // 自定义字段映射
 * const { treeData } = useTreeData({
 *   source: customData,
 *   fieldMapping: { id: 'code', name: 'title', children: 'items' }
 * })
 * ```
 */
export function useTreeData<
  TInput extends object = Record<string, unknown>,
  TNode extends TreeSelectNode = TreeSelectNode,
>(options: UseTreeDataOptions<TInput>): UseTreeDataReturn<TNode> {
  const {
    source,
    fieldMapping,
    modelValue,
    mode = 'single',
    searchable = false,
    searchQuery,
    defaultExpandLevel = 0,
  } = options

  // 默认字段映射
  const mapping: Required<FieldMapping> = {
    id: fieldMapping?.id ?? 'id',
    name: fieldMapping?.name ?? 'name',
    children: fieldMapping?.children ?? 'children',
  }

  // ============================================================================
  // 响应式状态
  // ============================================================================

  // 内部选中状态
  const internalSelectedIds = ref<(string | number)[]>([])

  // 选中状态（支持 v-model）
  const selectedIds = modelValue
    ? ('value' in modelValue ? modelValue : toRef(modelValue))
    : internalSelectedIds

  // 展开状态
  const expandedIds = ref<Set<string | number>>(new Set())

  // ============================================================================
  // 计算属性
  // ============================================================================

  /**
   * 转换后的树数据
   */
  const treeData = computed<TNode[]>(() => {
    // 支持 getter 函数、Ref 或原始数组
    const sourceValue = typeof source === 'function' ? source() : unref(source)
    if (!sourceValue || sourceValue.length === 0) return []
    return transformTreeData<TInput>(sourceValue, mapping) as TNode[]
  })

  /**
   * 过滤后的树数据（搜索功能）
   */
  const filteredData = computed<TNode[]>(() => {
    if (!searchable) return treeData.value

    const query = searchQuery ? unref(searchQuery) : ''
    if (!query.trim()) return treeData.value

    return searchInTree(treeData.value, query, mapping)
  })

  /**
   * 选中的节点对象列表
   */
  const selectedNodes = computed<TNode[]>(() => {
    const ids = selectedIds.value
    if (!ids || ids.length === 0) return []

    const nodes: TNode[] = []
    for (const id of ids) {
      const node = findNodeInTree(treeData.value, id)
      if (node) {
        nodes.push(node)
      }
    }
    return nodes
  })

  // ============================================================================
  // 方法
  // ============================================================================

  /**
   * 在树中查找指定节点
   * @param id 节点 ID
   * @returns 找到的节点，未找到返回 undefined
   */
  function findNode(id: string | number): TNode | undefined {
    return findNodeInTree(treeData.value, id)
  }

  /**
   * 获取指定节点的所有祖先节点
   * @param id 节点 ID
   * @returns 祖先节点数组（从根到父节点顺序）
   */
  function getAncestors(id: string | number): TNode[] {
    return getAncestorsInTree(treeData.value, id)
  }

  /**
   * 切换节点的选中状态
   * @param id 节点 ID
   */
  function toggleSelect(id: string | number): void {
    const currentIds = [...selectedIds.value]
    const index = currentIds.indexOf(id)

    if (mode === 'single') {
      // 单选模式：替换选中项
      if (index === -1) {
        selectedIds.value = [id]
      } else {
        selectedIds.value = []
      }
    } else {
      // 多选模式：切换选中状态
      if (index === -1) {
        selectedIds.value = [...currentIds, id]
      } else {
        currentIds.splice(index, 1)
        selectedIds.value = currentIds
      }
    }
  }

  /**
   * 清空所有选中状态
   */
  function clearSelection(): void {
    selectedIds.value = []
  }

  /**
   * 切换节点展开状态
   * @param id 节点 ID
   */
  function toggleExpand(id: string | number): void {
    if (expandedIds.value.has(id)) {
      expandedIds.value.delete(id)
    } else {
      expandedIds.value.add(id)
    }
  }

  /**
   * 展开到指定层级
   * @param level 目标层级（0 = 仅根节点）
   */
  function expandToLevel(level: number): void {
    expandedIds.value.clear()

    if (level < 0) return

    function collectNodesToLevel(nodes: TNode[], currentLevel: number): void {
      for (const node of nodes) {
        if (currentLevel < level && node.children?.length) {
          expandedIds.value.add(node.id)
          collectNodesToLevel(node.children as TNode[], currentLevel + 1)
        }
      }
    }

    collectNodesToLevel(treeData.value, 0)
  }

  // ============================================================================
  // 初始化
  // ============================================================================

  // 根据 defaultExpandLevel 初始化展开状态
  if (defaultExpandLevel > 0) {
    // 使用 watchEffect 在 treeData 就绪后初始化
    const stopWatch = computed(() => {
      if (treeData.value.length > 0) {
        expandToLevel(defaultExpandLevel)
        return true
      }
      return false
    })
    // 立即执行一次
    if (treeData.value.length > 0) {
      expandToLevel(defaultExpandLevel)
    }
  }

  // ============================================================================
  // 返回
  // ============================================================================

  return {
    treeData,
    selectedIds,
    selectedNodes,
    filteredData,
    expandedIds,
    toggleExpand,
    expandToLevel,
    findNode,
    getAncestors,
    toggleSelect,
    clearSelection,
  }
}

// ============================================================================
// 辅助类型导出
// ============================================================================

export type { TreeSelectNode, TreeNodeTree, TreeNode }
