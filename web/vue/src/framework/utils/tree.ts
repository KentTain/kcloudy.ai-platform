/**
 * 树工具函数
 */

import type { TreeNode, TreeNodeTree } from '@/framework/types/tree'

/**
 * 将平铺列表转换为树结构
 */
export function buildTree<T extends TreeNode>(
  nodes: T[],
  parentId: string | null = null
): TreeNodeTree[] {
  if (!nodes.length) return []

  const result: TreeNodeTree[] = []
  const map = new Map<string, TreeNodeTree>()

  // 先创建所有节点的映射
  for (const node of nodes) {
    const treeNode: TreeNodeTree = { ...node, children: [] }
    map.set(node.id, treeNode)
  }

  // 构建父子关系
  for (const node of nodes) {
    const treeNode = map.get(node.id)!
    const pid = node.parent_id ?? null

    if (pid === parentId) {
      result.push(treeNode)
    } else if (pid && map.has(pid)) {
      map.get(pid)!.children!.push(treeNode)
    }
  }

  return result
}

/**
 * 将树结构转换为平铺列表
 */
export function flattenTree<T extends TreeNodeTree>(tree: T[]): T[] {
  const result: T[] = []

  function walk(nodes: T[]) {
    for (const node of nodes) {
      result.push(node)
      if (node.children?.length) {
        walk(node.children as T[])
      }
    }
  }

  walk(tree)
  // 仅当所有节点都有 tree_sorts 时才排序
  if (result.length > 0 && 'tree_sorts' in result[0]) {
    return sortByTreeSorts(result as T[])
  }
  return result
}

/**
 * 在树中查找指定节点
 */
export function findNodeById<T extends TreeNodeTree>(
  tree: T[],
  id: string
): T | undefined {
  for (const node of tree) {
    if (node.id === id) return node
    if (node.children?.length) {
      const found = findNodeById(node.children as T[], id)
      if (found) return found
    }
  }
  return undefined
}

/**
 * 获取指定节点的所有祖先节点
 */
export function getAncestors<T extends TreeNode>(
  nodes: T[],
  nodeId: string
): T[] {
  const node = nodes.find(n => n.id === nodeId)
  if (!node || !node.parent_ids) return []

  const ancestorIds = node.parent_ids.split(',').filter(id => id && id !== 'root')
  return ancestorIds.map(id => nodes.find(n => n.id === id)!).filter(Boolean)
}

/**
 * 按 tree_sorts 字段排序节点列表
 */
export function sortByTreeSorts<T extends TreeNode>(nodes: T[]): T[] {
  return [...nodes].sort((a, b) => a.tree_sorts.localeCompare(b.tree_sorts))
}