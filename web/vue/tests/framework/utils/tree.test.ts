import { describe, it, expect } from 'vitest'
import {
  buildTree,
  flattenTree,
  findNodeById,
  getAncestors,
  sortByTreeSorts,
} from '@/framework/utils/tree'
import type { TreeNode, TreeNodeTree, TreeComponentNode } from '@/framework/types/tree'

// 测试数据
const flatNodes: TreeNode[] = [
  { id: '1', parent_id: null, name: '研发部', tree_level: 0, tree_leaf: false, tree_sort: 10, tree_sorts: '00000010,', tree_names: '研发部', parent_ids: 'root,' },
  { id: '2', parent_id: '1', name: '前端组', tree_level: 1, tree_leaf: true, tree_sort: 10, tree_sorts: '00000010,00000010,', tree_names: '研发部/前端组', parent_ids: 'root,1,' },
  { id: '3', parent_id: '1', name: '后端组', tree_level: 1, tree_leaf: true, tree_sort: 20, tree_sorts: '00000010,00000020,', tree_names: '研发部/后端组', parent_ids: 'root,1,' },
  { id: '4', parent_id: null, name: '市场部', tree_level: 0, tree_leaf: true, tree_sort: 20, tree_sorts: '00000020,', tree_names: '市场部', parent_ids: 'root,' },
]

const componentNodes: TreeComponentNode[] = [
  { id: '1', name: '研发部', children: [
    { id: '2', name: '前端组' },
    { id: '3', name: '后端组' },
  ] },
  { id: '4', name: '市场部' },
]

describe('buildTree', () => {
  it('构建完整树', () => {
    const tree = buildTree(flatNodes)
    expect(tree.length).toBe(2)
    expect(tree[0].id).toBe('1')
    expect(tree[0].name).toBe('研发部')
    expect(tree[0].children?.length).toBe(2)
    expect(tree[0].children![0].id).toBe('2')
    expect(tree[1].id).toBe('4')
  })

  it('构建子树', () => {
    const tree = buildTree(flatNodes, '1')
    expect(tree.length).toBe(2)
    expect(tree[0].id).toBe('2')
    expect(tree[1].id).toBe('3')
  })

  it('空列表返回空数组', () => {
    const tree = buildTree([])
    expect(tree).toEqual([])
  })
})

describe('flattenTree', () => {
  it('扁平化树结构', () => {
    const tree = buildTree(flatNodes)
    const flat = flattenTree(tree)
    expect(flat.length).toBe(4)
  })

  it('按 tree_sorts 排序', () => {
    const tree = buildTree(flatNodes)
    const flat = flattenTree(tree)
    expect(flat[0].tree_sorts).toBe('00000010,')
  })
})

describe('findNodeById', () => {
  it('查找存在的节点', () => {
    const tree = buildTree(flatNodes)
    const found = findNodeById(tree, '2')
    expect(found?.id).toBe('2')
    expect(found?.name).toBe('前端组')
  })

  it('查找不存在的节点返回 undefined', () => {
    const tree = buildTree(flatNodes)
    const found = findNodeById(tree, 'nonexistent')
    expect(found).toBeUndefined()
  })
})

describe('getAncestors', () => {
  it('获取祖先节点', () => {
    const ancestors = getAncestors(flatNodes, '2')
    expect(ancestors.length).toBe(1)
    expect(ancestors[0].id).toBe('1')
  })

  it('根节点无祖先', () => {
    const ancestors = getAncestors(flatNodes, '1')
    expect(ancestors.length).toBe(0)
  })
})

describe('sortByTreeSorts', () => {
  it('按 tree_sorts 排序节点列表', () => {
    const unsorted = [...flatNodes].reverse()
    const sorted = sortByTreeSorts(unsorted)
    expect(sorted[0].tree_sorts).toBe('00000010,')
    expect(sorted[1].tree_sorts).toBe('00000010,00000010,')
    expect(sorted[2].tree_sorts).toBe('00000010,00000020,')
    expect(sorted[3].tree_sorts).toBe('00000020,')
  })
})