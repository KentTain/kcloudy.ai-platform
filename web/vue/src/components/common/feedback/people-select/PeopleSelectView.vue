<script setup lang="ts">
/**
 * PeopleSelectView — 人员选择视图
 *
 * 左右布局：左侧组织树 + 右侧人员列表
 */

import { ref, onMounted, watch } from "vue"
import { Search, Users, User, Building2, ChevronRight, ChevronDown } from "@lucide/vue"
import { Input, Badge, Skeleton, Button } from "@/components"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Checkbox } from "@/components/ui/checkbox"
import { cn } from "@/lib/utils"
import type { OrgTreeNode, PeopleItem } from "./types"
import { usePeopleTree } from "./usePeopleTree"

interface Props {
  /** 是否多选模式 */
  multiple?: boolean
  /** 禁用的人员 ID 列表 */
  disabledIds?: string[]
  /** 已选中的人员 ID 列表 */
  modelValue?: string[]
  /** 加载组织子节点 API */
  loadOrgNodes: (parentId?: string) => Promise<OrgTreeNode[]>
  /** 搜索人员 API */
  searchPeople: (keyword: string) => Promise<PeopleItem[]>
  /** 加载组织下人员 API */
  loadOrgPeople: (orgId: string) => Promise<PeopleItem[]>
}

const props = withDefaults(defineProps<Props>(), {
  multiple: true,
  disabledIds: () => [],
  modelValue: () => [],
})

const emit = defineEmits<{
  "update:modelValue": [value: string[]]
  select: [people: PeopleItem[]]
}>()

const {
  treeData,
  loading,
  searchKeyword,
  currentOrgId,
  selectedIds,
  selectedPeople,
  displayPeople,
  disabledIdSet,
  initTree,
  loadChildren,
  selectOrg,
  togglePerson,
  handleSearch,
  isSelected,
} = usePeopleTree({
  multiple: props.multiple,
  disabledIds: props.disabledIds,
  modelValue: props.modelValue,
  loadOrgNodes: props.loadOrgNodes,
  searchPeople: props.searchPeople,
  loadOrgPeople: props.loadOrgPeople,
})

// 搜索防抖
let searchTimer: ReturnType<typeof setTimeout> | null = null
const searchInput = ref("")

function onSearchInput(value: string) {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    handleSearch(value)
  }, 300)
}

// 组织树展开状态
const expandedOrgs = ref<Set<string>>(new Set())

function toggleOrg(node: OrgTreeNode) {
  if (expandedOrgs.value.has(node.id)) {
    expandedOrgs.value.delete(node.id)
  } else {
    expandedOrgs.value.add(node.id)
    // 懒加载子节点
    if (!node.children || node.children.length === 0) {
      loadChildren(node.id)
    }
  }
  selectOrg(node.id)
}

function isOrgExpanded(nodeId: string): boolean {
  return expandedOrgs.value.has(nodeId)
}

// 切换人员选中
function onTogglePerson(person: PeopleItem) {
  togglePerson(person)
  emit("update:modelValue", Array.from(selectedIds.value))
  emit("select", selectedPeople.value)
}

onMounted(() => {
  initTree()
})
</script>

<template>
  <div class="flex h-[460px] border rounded-lg overflow-hidden">
    <!-- 左侧：组织树 -->
    <div class="w-[240px] border-r flex flex-col bg-muted/20">
      <!-- 搜索框 -->
      <div class="p-2 border-b">
        <div class="relative">
          <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            v-model="searchInput"
            placeholder="搜索组织或人员..."
            class="pl-8 h-8 text-sm"
            @update:model-value="onSearchInput"
          />
        </div>
      </div>

      <!-- 组织树 -->
      <ScrollArea class="flex-1">
        <div v-if="loading" class="p-3 space-y-2">
          <Skeleton v-for="i in 6" :key="i" class="h-6 w-full" />
        </div>
        <div v-else class="py-1">
          <div
            v-for="node in treeData"
            :key="node.id"
          >
            <button
              class="flex items-center w-full px-3 py-1.5 text-sm hover:bg-accent transition-colors text-left"
              :class="{
                'bg-accent': currentOrgId === node.id,
              }"
              @click="toggleOrg(node)"
            >
              <!-- 展开/折叠图标 -->
              <ChevronDown
                v-if="isOrgExpanded(node.id)"
                class="h-4 w-4 shrink-0 text-muted-foreground"
              />
              <ChevronRight
                v-else
                class="h-4 w-4 shrink-0 text-muted-foreground"
                :class="{ 'invisible': !node.tree_leaf !== true && !node.children?.length }"
              />
              <Building2 class="h-3.5 w-3.5 ml-1 mr-2 text-blue-500 shrink-0" />
              <span class="truncate">{{ node.name }}</span>
              <Badge v-if="node.has_user_num" variant="secondary" class="ml-auto shrink-0 text-xs">
                {{ node.has_user_num }}
              </Badge>
            </button>
            <!-- 递归渲染子节点 -->
            <div v-if="isOrgExpanded(node.id) && node.children" class="ml-4">
              <button
                v-for="child in node.children"
                :key="child.id"
                class="flex items-center w-full px-3 py-1.5 text-sm hover:bg-accent transition-colors text-left"
                :class="{
                  'bg-accent': currentOrgId === child.id,
                }"
                @click="selectOrg(child.id)"
              >
                <Building2 class="h-3.5 w-3.5 ml-4 mr-2 text-blue-500 shrink-0" />
                <span class="truncate">{{ child.name }}</span>
                <Badge v-if="child.has_user_num" variant="secondary" class="ml-auto shrink-0 text-xs">
                  {{ child.has_user_num }}
                </Badge>
              </button>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>

    <!-- 右侧：人员列表 -->
    <div class="flex-1 flex flex-col">
      <!-- 已选人员 -->
      <div v-if="selectedPeople.length > 0" class="p-2 border-b bg-muted/10">
        <div class="flex flex-wrap gap-1">
          <Badge
            v-for="p in selectedPeople"
            :key="p.user_id"
            variant="secondary"
            class="cursor-pointer"
            @click="onTogglePerson(p)"
          >
            {{ p.nickname || p.username }}
            <span class="ml-1 text-muted-foreground">×</span>
          </Badge>
        </div>
      </div>

      <!-- 人员列表 -->
      <ScrollArea class="flex-1">
        <div v-if="loading" class="p-3 space-y-3">
          <div v-for="i in 8" :key="i" class="flex items-center gap-3">
            <Skeleton class="h-8 w-8 rounded-full" />
            <Skeleton class="h-4 w-32" />
          </div>
        </div>
        <div v-else-if="displayPeople.length === 0" class="flex flex-col items-center justify-center h-full text-muted-foreground">
          <Users class="h-12 w-12 mb-2 opacity-50" />
          <p class="text-sm">请选择左侧组织查看人员</p>
        </div>
        <div v-else class="py-1">
          <div
            v-for="person in displayPeople"
            :key="person.user_id"
            class="flex items-center gap-3 px-3 py-2 hover:bg-accent transition-colors cursor-pointer"
            :class="{
              'opacity-50 cursor-not-allowed': disabledIdSet.has(person.user_id),
            }"
            @click="disabledIdSet.has(person.user_id) ? undefined : onTogglePerson(person)"
          >
            <Checkbox
              :checked="isSelected(person.user_id)"
              :disabled="disabledIdSet.has(person.user_id)"
              class="shrink-0"
            />
            <User class="h-4 w-4 text-muted-foreground shrink-0" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">
                {{ person.nickname || person.username }}
              </p>
              <p class="text-xs text-muted-foreground truncate">
                {{ person.username }}
                <template v-if="person.email">
                  · {{ person.email }}
                </template>
              </p>
            </div>
            <Badge
              v-if="person.status === 'inactive'"
              variant="outline"
              class="text-xs shrink-0"
            >
              停用
            </Badge>
          </div>
        </div>
      </ScrollArea>
    </div>
  </div>
</template>
