/**
 * usePeopleTree — 组织+人员树的无头逻辑 composable
 *
 * 封装三态复选、懒加载、搜索等核心逻辑。
 * 基于项目现有 Tree 组件的 checkbox/cascade/loadData 能力封装。
 */

import { ref, computed, reactive } from "vue"
import type { OrgTreeNode, PeopleItem, PeopleSelectOptions } from "./types"

export function usePeopleTree(options: PeopleSelectOptions) {
  const {
    multiple = true,
    disabledIds = [],
    modelValue = [],
    loadOrgNodes,
    searchPeople,
    loadOrgPeople,
  } = options

  // ========== 状态 ==========
  const treeData = ref<OrgTreeNode[]>([])
  const loading = ref(false)
  const searchKeyword = ref("")
  const currentOrgId = ref<string | null>(null)
  const selectedIds = ref<Set<string>>(new Set(modelValue))
  const selectedPeople = ref<PeopleItem[]>([])
  const displayPeople = ref<PeopleItem[]>([])

  // 组织下人员缓存
  const orgPeopleCache = reactive<Map<string, PeopleItem[]>>(new Map())

  // ========== 计算属性 ==========
  const disabledIdSet = computed(() => new Set(disabledIds))

  // ========== 方法 ==========

  /** 初始化树根节点 */
  async function initTree() {
    loading.value = true
    try {
      const nodes = await loadOrgNodes()
      treeData.value = nodes
    } finally {
      loading.value = false
    }
  }

  /** 懒加载子组织节点 */
  async function loadChildren(orgId: string) {
    const nodes = await loadOrgNodes(orgId)
    // 将子节点合并到对应组织节点的 children
    function mergeChildren(list: OrgTreeNode[]): boolean {
      for (const item of list) {
        if (item.id === orgId) {
          item.children = nodes
          return true
        }
        if (item.children && mergeChildren(item.children)) {
          return true
        }
      }
      return false
    }
    mergeChildren(treeData.value)
  }

  /** 选中组织，加载其直属人员 */
  async function selectOrg(orgId: string) {
    currentOrgId.value = orgId

    // 检查缓存
    if (orgPeopleCache.has(orgId)) {
      displayPeople.value = orgPeopleCache.get(orgId)!
      return
    }

    loading.value = true
    try {
      const people = await loadOrgPeople(orgId)
      orgPeopleCache.set(orgId, people)
      displayPeople.value = people
    } finally {
      loading.value = false
    }
  }

  /** 切换人员选中状态 */
  function togglePerson(person: PeopleItem) {
    // 禁用的人员不可选
    if (disabledIdSet.value.has(person.user_id)) return

    const idSet = selectedIds.value

    if (idSet.has(person.user_id)) {
      // 取消选中
      idSet.delete(person.user_id)
      selectedPeople.value = selectedPeople.value.filter(
        (p) => p.user_id !== person.user_id
      )
    } else {
      // 添加选中
      if (!multiple) {
        // 单选模式：清空之前的选择
        idSet.clear()
        selectedPeople.value = []
      }
      idSet.add(person.user_id)
      selectedPeople.value.push(person)
    }
  }

  /** 搜索处理 */
  async function handleSearch(keyword: string) {
    searchKeyword.value = keyword

    if (!keyword.trim()) {
      // 清空搜索，恢复组织选择视图
      if (currentOrgId.value) {
        await selectOrg(currentOrgId.value)
      } else {
        displayPeople.value = []
      }
      return
    }

    loading.value = true
    try {
      const people = await searchPeople(keyword)
      displayPeople.value = people
    } finally {
      loading.value = false
    }
  }

  /** 清空选择 */
  function clearSelection() {
    selectedIds.value.clear()
    selectedPeople.value = []
  }

  /** 获取选中的人员 ID 列表 */
  function getSelectedIds(): string[] {
    return Array.from(selectedIds.value)
  }

  /** 是否已选中某人 */
  function isSelected(userId: string): boolean {
    return selectedIds.value.has(userId)
  }

  return {
    // 状态
    treeData,
    loading,
    searchKeyword,
    currentOrgId,
    selectedIds,
    selectedPeople,
    displayPeople,
    disabledIdSet,
    // 方法
    initTree,
    loadChildren,
    selectOrg,
    togglePerson,
    handleSearch,
    clearSelection,
    getSelectedIds,
    isSelected,
  }
}
