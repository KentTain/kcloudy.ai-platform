import { describe, expect, it, vi, beforeEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { useOrgPeopleTree } from '@/components/common/feedback/people-select/useOrgPeopleTree'
import type { OrgTreeNode, UserItem } from '@/components/common/feedback/people-select/types'

// Mock service
vi.mock('@/components/common/feedback/people-select/service', () => ({
  loadOrgUserTree: vi.fn(),
}))

// 测试数据
const createMockUser = (id: string, name: string): UserItem => ({
  id,
  username: name.toLowerCase(),
  nickname: name,
  status: 'active',
})

const createMockOrg = (
  id: string,
  name: string,
  options: {
    parentId?: string
    treeLevel?: number
    treeLeaf?: boolean
    users?: UserItem[]
    children?: OrgTreeNode[]
    hasOrgNum?: number
    hasUserNum?: number
  } = {}
): OrgTreeNode => ({
  id,
  name,
  code: name.toUpperCase(),
  tenant_id: 'tenant-1',
  status: 'active',
  parent_id: options.parentId ?? null,
  tree_level: options.treeLevel ?? 0,
  tree_leaf: options.treeLeaf ?? false,
  tree_sort: 1,
  tree_sorts: '1',
  tree_names: name,
  parent_ids: options.parentId ?? '',
  has_org_num: options.hasOrgNum ?? 0,
  has_user_num: options.hasUserNum ?? (options.users?.length ?? 0),
  users: options.users ?? [],
  children: options.children,
})

describe('useOrgPeopleTree', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('三态复选框逻辑', () => {
    it('应该在所有用户选中时返回 checked 状态', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1', 'user-2'])
      const { initTree, checkedUserIds, flatVisibleNodes } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      // 检查 checkedUserIds
      expect(checkedUserIds.value.has('user-1')).toBe(true)
      expect(checkedUserIds.value.has('user-2')).toBe(true)

      // 检查扁平化节点中组织节点的 checkState
      const orgNode = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNode?.checkState).toBe('checked')
    })

    it('应该在部分用户选中时返回 indeterminate 状态', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1']) // 只选中一个
      const { initTree, flatVisibleNodes, indeterminateUserIds } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      const orgNode = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNode?.checkState).toBe('indeterminate')
      expect(indeterminateUserIds.value.has('org-1')).toBe(true)
    })

    it('应该在无用户选中时返回 unchecked 状态', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>([])
      const { initTree, flatVisibleNodes } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      const orgNode = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNode?.checkState).toBe('unchecked')
    })

    it('应该在没有用户的组织时返回 unchecked 状态', async () => {
      const org = createMockOrg('org-1', '空部门', { users: [], hasUserNum: 0 })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>([])
      const { initTree, flatVisibleNodes } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      const orgNode = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNode?.checkState).toBe('unchecked')
    })
  })

  describe('懒加载逻辑', () => {
    it('应该在展开组织时加载子节点', async () => {
      const rootOrg = createMockOrg('org-1', '总公司', { treeLeaf: false, hasOrgNum: 1 })
      const childOrg = createMockOrg('org-2', '研发部', {
        parentId: 'org-1',
        treeLevel: 1,
        treeLeaf: true,
      })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockImplementation(async (parentId?: string) => {
        if (parentId === 'org-1') {
          return [childOrg]
        }
        return [rootOrg]
      })

      const { initTree, toggleOrgExpand, treeData, expandedOrgIds, loadingOrgIds } =
        useOrgPeopleTree({ defaultExpandLevel: 0 })

      await initTree()
      await nextTick()

      // 初始状态：未展开
      expect(expandedOrgIds.value.has('org-1')).toBe(false)
      expect(treeData.value[0].children).toBeUndefined()

      // 展开组织
      await toggleOrgExpand('org-1')
      await nextTick()

      // 验证展开状态
      expect(expandedOrgIds.value.has('org-1')).toBe(true)
      expect(treeData.value[0].children).toBeDefined()
      expect(treeData.value[0].children?.length).toBe(1)
      expect(treeData.value[0].children?.[0].id).toBe('org-2')
    })

    it('应该正确管理加载状态', async () => {
      const rootOrg = createMockOrg('org-1', '总公司', { treeLeaf: false, hasOrgNum: 1 })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )

      // 使用延迟 mock 模拟网络请求
      let resolveLoad: (value: OrgTreeNode[]) => void
      vi.mocked(loadOrgUserTree).mockImplementation(async (parentId?: string) => {
        if (parentId === 'org-1') {
          return new Promise((resolve) => {
            resolveLoad = resolve
          })
        }
        return [rootOrg]
      })

      const { initTree, toggleOrgExpand, loadingOrgIds } = useOrgPeopleTree({
        defaultExpandLevel: 0,
      })

      await initTree()
      await nextTick()

      // 开始展开，但请求未完成
      const expandPromise = toggleOrgExpand('org-1')
      await nextTick()

      // 此时应该正在加载
      expect(loadingOrgIds.value.has('org-1')).toBe(true)

      // 完成请求
      resolveLoad!([])
      await expandPromise
      await nextTick()

      // 加载完成
      expect(loadingOrgIds.value.has('org-1')).toBe(false)
    })

    it('应该在已加载子节点时直接展开', async () => {
      const childOrg = createMockOrg('org-2', '研发部', { parentId: 'org-1', treeLevel: 1 })
      const rootOrg = createMockOrg('org-1', '总公司', {
        treeLeaf: false,
        hasOrgNum: 1,
        children: [childOrg],
      })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([rootOrg])

      const { initTree, toggleOrgExpand, expandedOrgIds } = useOrgPeopleTree({
        defaultExpandLevel: 0,
      })

      await initTree()
      await nextTick()

      // 子节点已存在，展开时不应该调用 loadOrgUserTree
      await toggleOrgExpand('org-1')
      await nextTick()

      expect(expandedOrgIds.value.has('org-1')).toBe(true)
      // 只在 initTree 时调用一次
      expect(loadOrgUserTree).toHaveBeenCalledTimes(1)
    })
  })

  describe('选择逻辑', () => {
    it('应该正确切换用户选中状态', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>([])
      const { initTree, toggleUserCheck, checkedUserIds, flatVisibleNodes } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      // 选中 user-1
      toggleUserCheck('user-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(true)
      expect(checkedUserIds.value.has('user-2')).toBe(false)

      // 验证用户节点的 checkState
      const userNode = flatVisibleNodes.value.find((n) => n.id === 'user-1')
      expect(userNode?.checkState).toBe('checked')

      // 取消选中 user-1
      toggleUserCheck('user-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(false)
    })

    it('应该正确切换组织选中状态（级联选择）', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>([])
      const { initTree, toggleOrgCheck, checkedUserIds, flatVisibleNodes } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      // 选中组织（应该选中所有用户）
      toggleOrgCheck('org-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(true)
      expect(checkedUserIds.value.has('user-2')).toBe(true)

      // 验证组织节点的 checkState
      const orgNode = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNode?.checkState).toBe('checked')

      // 再次点击取消选中
      toggleOrgCheck('org-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(false)
      expect(checkedUserIds.value.has('user-2')).toBe(false)
    })

    it('应该在部分选中时点击组织取消全部选中', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1']) // 预选一个
      const { initTree, toggleOrgCheck, checkedUserIds, flatVisibleNodes } = useOrgPeopleTree({
        modelValue,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      // 初始状态：部分选中
      const orgNodeBefore = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNodeBefore?.checkState).toBe('indeterminate')

      // 点击组织应该取消全部选中（indeterminate 状态点击会取消选择）
      toggleOrgCheck('org-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(false)
      expect(checkedUserIds.value.has('user-2')).toBe(false)

      const orgNodeAfter = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      expect(orgNodeAfter?.checkState).toBe('unchecked')
    })

    it('应该尊重禁用的用户 ID', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>([])
      const disabledIds = ref<string[]>(['user-1'])

      const { initTree, toggleUserCheck, toggleOrgCheck, checkedUserIds } = useOrgPeopleTree({
        modelValue,
        disabledIds,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      // 尝试选中禁用的用户
      toggleUserCheck('user-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(false)

      // 通过组织选中也应该跳过禁用用户
      toggleOrgCheck('org-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(false)
      expect(checkedUserIds.value.has('user-2')).toBe(true)
    })

    it('应该在单选模式下清空之前的选择', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>([])
      const { initTree, toggleUserCheck, checkedUserIds } = useOrgPeopleTree({
        modelValue,
        multiple: false,
        defaultExpandLevel: 1,
      })

      await initTree()
      await nextTick()

      // 选中第一个用户
      toggleUserCheck('user-1')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(true)
      expect(checkedUserIds.value.size).toBe(1)

      // 选中第二个用户应该清空第一个
      toggleUserCheck('user-2')
      await nextTick()

      expect(checkedUserIds.value.has('user-1')).toBe(false)
      expect(checkedUserIds.value.has('user-2')).toBe(true)
      expect(checkedUserIds.value.size).toBe(1)
    })
  })

  describe('扁平化节点', () => {
    it('应该正确扁平化展开的节点', async () => {
      const users = [createMockUser('user-1', '张三')]
      const childOrg = createMockOrg('org-2', '研发部', {
        parentId: 'org-1',
        treeLevel: 1,
        treeLeaf: true,
        users: [createMockUser('user-2', '李四')],
      })
      const rootOrg = createMockOrg('org-1', '总公司', {
        treeLeaf: false,
        hasOrgNum: 1,
        users,
        children: [childOrg],
      })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([rootOrg])

      const { initTree, flatVisibleNodes } = useOrgPeopleTree({ defaultExpandLevel: 1 })

      await initTree()
      await nextTick()

      // 展开状态下扁平化：org-1, org-2, user-1（嵌套子组织的用户不展开时不显示）
      expect(flatVisibleNodes.value.length).toBe(3)

      // 验证顺序：先组织后用户
      const ids = flatVisibleNodes.value.map((n) => n.id)
      expect(ids).toContain('org-1')
      expect(ids).toContain('org-2')
      expect(ids).toContain('user-1')
    })

    it('应该正确计算节点层级', async () => {
      const childOrg = createMockOrg('org-2', '研发部', {
        parentId: 'org-1',
        treeLevel: 1,
      })
      const rootOrg = createMockOrg('org-1', '总公司', {
        treeLeaf: false,
        hasOrgNum: 1,
        children: [childOrg],
      })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([rootOrg])

      const { initTree, flatVisibleNodes } = useOrgPeopleTree({ defaultExpandLevel: 1 })

      await initTree()
      await nextTick()

      const rootNode = flatVisibleNodes.value.find((n) => n.id === 'org-1')
      const childNode = flatVisibleNodes.value.find((n) => n.id === 'org-2')

      expect(rootNode?.tree_level).toBe(0)
      expect(childNode?.tree_level).toBe(1)
    })
  })

  describe('工具方法', () => {
    it('getCheckedUserIds 应该返回选中的用户 ID 数组', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1', 'user-2'])
      const { initTree, getCheckedUserIds } = useOrgPeopleTree({ modelValue })

      await initTree()

      const ids = getCheckedUserIds()
      expect(ids).toEqual(expect.arrayContaining(['user-1', 'user-2']))
      expect(ids.length).toBe(2)
    })

    it('clearChecked 应该清空所有选中', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1', 'user-2'])
      const { initTree, clearChecked, checkedUserIds, indeterminateUserIds } = useOrgPeopleTree({
        modelValue,
      })

      await initTree()

      clearChecked()

      expect(checkedUserIds.value.size).toBe(0)
      expect(indeterminateUserIds.value.size).toBe(0)
    })

    it('getCheckState 应该返回正确的复选框状态', async () => {
      const users = [createMockUser('user-1', '张三')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1'])
      const { initTree, getCheckState } = useOrgPeopleTree({ modelValue })

      await initTree()

      expect(getCheckState('user-1')).toBe('checked')
      expect(getCheckState('user-2')).toBe('unchecked')
    })
  })

  describe('初始化', () => {
    it('应该根据 defaultExpandLevel 展开节点', async () => {
      const childOrg = createMockOrg('org-2', '研发部', {
        parentId: 'org-1',
        treeLevel: 1,
        treeLeaf: true,
      })
      const rootOrg = createMockOrg('org-1', '总公司', {
        treeLeaf: false,
        hasOrgNum: 1,
        children: [childOrg],
      })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([rootOrg])

      const { initTree, expandedOrgIds } = useOrgPeopleTree({ defaultExpandLevel: 1 })

      await initTree()
      await nextTick()

      // 应该展开第一层
      expect(expandedOrgIds.value.has('org-1')).toBe(true)
      // 第二层不应该展开
      expect(expandedOrgIds.value.has('org-2')).toBe(false)
    })

    it('应该正确加载初始选中状态', async () => {
      const users = [createMockUser('user-1', '张三'), createMockUser('user-2', '李四')]
      const org = createMockOrg('org-1', '研发部', { users })

      const { loadOrgUserTree } = await import(
        '@/components/common/feedback/people-select/service'
      )
      vi.mocked(loadOrgUserTree).mockResolvedValueOnce([org])

      const modelValue = ref<string[]>(['user-1'])
      const { initTree, checkedUserIds } = useOrgPeopleTree({ modelValue })

      await initTree()

      expect(checkedUserIds.value.has('user-1')).toBe(true)
      expect(checkedUserIds.value.has('user-2')).toBe(false)
    })
  })
})
