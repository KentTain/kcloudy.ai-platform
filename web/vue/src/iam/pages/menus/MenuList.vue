<script setup lang="ts">
/**
 * MenuList — 菜单管理页面
 *
 * 布局参照 OrganizationPage.vue:
 * - Header: 左侧标题 + 描述
 * - Body: 左侧 300px 菜单树 + 右侧 Tabs（菜单信息、权限列表）
 */

import { ref, computed, onMounted, h, defineComponent, type PropType, type VNodeChild } from "vue"
import type { ColumnDef } from "@tanstack/vue-table"
import {
  Menu,
  Info,
  Shield,
  Search,
  FolderOpen,
  Users,
  Building2,
  Badge as BadgeIcon,
  Lock,
  Puzzle,
  Settings,
} from "@lucide/vue"
import type { LucideIcon } from "@lucide/vue"
import AppPage from "@/framework/layouts/components/AppPage.vue"
import {
  Button,
  Badge,
  Skeleton,
  DescriptionList,
  type DescriptionItem,
  DataTable,
  useDataTable,
  Input,
} from "@/components"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useMenuStore } from "@/iam/stores/menu"
import { getMenuPermissions } from "@/iam/api/menu"
import type { MenuTreeNode, Permission } from "@/iam/types"
import { notifyError, getErrorMessage } from "@/framework/utils/feedback"

const menuStore = useMenuStore()

// ========== 图标映射 ==========

const iconMap: Record<string, LucideIcon> = {
  Menu,
  Users,
  Building: Building2,
  Building2,
  Badge: BadgeIcon,
  Lock,
  Puzzle,
  Settings,
  Organization: Building2,
}

// ========== 递归树节点组件 ==========

const MenuTreeNodeComponent = defineComponent({
  name: "MenuTreeNodeComponent",
  props: {
    menus: { type: Array as PropType<MenuTreeNode[]>, required: true },
    selectedId: { type: String as PropType<string | null>, default: null },
    depth: { type: Number, default: 0 },
  },
  emits: ["select"],
  setup(props, { emit }) {
    return (): VNodeChild[] => {
      const nodes: VNodeChild[] = []
      for (const menu of props.menus) {
        const isSelected = props.selectedId === menu.id
        const indent = 12 + props.depth * 20

        // 动态选择图标
        const IconComponent = menu.icon ? iconMap[menu.icon] || Menu : Menu

        nodes.push(
          h(
            "button",
            {
              class: [
                "flex items-center w-full px-3 py-2 text-sm hover:bg-accent transition-colors text-left",
                { "bg-accent": isSelected },
              ],
              style: { paddingLeft: `${indent}px` },
              onClick: () => emit("select", menu),
            },
            [
              h(IconComponent, { class: "h-4 w-4 mr-2 shrink-0 text-blue-500" }),
              h("span", { class: "truncate" }, menu.name),
              menu.children?.length
                ? h(
                    Badge,
                    { variant: "secondary", class: "ml-auto shrink-0 text-xs" },
                    () => String(menu.children!.length),
                  )
                : null,
            ],
          ),
        )
        if (menu.children?.length) {
          nodes.push(
            h(MenuTreeNodeComponent, {
              menus: menu.children,
              selectedId: props.selectedId,
              depth: props.depth + 1,
              onSelect: (menu: MenuTreeNode) => emit("select", menu),
            }),
          )
        }
      }
      return nodes
    }
  },
})

// ========== 状态 ==========

const loading = computed(() => menuStore.loading)
const selectedId = ref<string | null>(null)

// Tabs
const activeTab = ref("info")

// 权限列表
const permissions = ref<Permission[]>([])
const permissionsLoading = ref(false)

// 搜索
const searchKeyword = ref("")

// ========== 计算属性 ==========

const hasSelection = computed(() => !!selectedId.value)

// 当前选中的菜单对象
const selectedMenu = computed<MenuTreeNode | null>(() => {
  if (!selectedId.value) return null
  return findMenuById(menuStore.menus, selectedId.value)
})

// 搜索过滤
const filteredTree = computed(() => {
  if (!searchKeyword.value.trim()) return menuStore.menus

  const keyword = searchKeyword.value.toLowerCase()

  function filterNodes(nodes: MenuTreeNode[]): MenuTreeNode[] {
    return nodes.reduce<MenuTreeNode[]>((acc, node) => {
      const matches = node.name.toLowerCase().includes(keyword) || node.code.toLowerCase().includes(keyword)
      const filteredChildren = node.children ? filterNodes(node.children) : []

      if (matches || filteredChildren.length > 0) {
        acc.push({ ...node, children: filteredChildren.length > 0 ? filteredChildren : node.children })
      }

      return acc
    }, [])
  }

  return filterNodes(menuStore.menus)
})

// 菜单信息描述项
const infoItems = computed<DescriptionItem[]>(() => {
  const menu = selectedMenu.value
  if (!menu) return []
  return [
    { label: "菜单名称", value: menu.name },
    { label: "菜单编码", value: menu.code },
    { label: "路由路径", value: menu.path || "--" },
    { label: "所属模块", value: menu.module },
    { label: "图标", value: menu.icon || "未设置" },
    { label: "是否可见", value: menu.is_visible ? "可见" : "隐藏" },
    { label: "排序号", value: String(menu.tree_sort) },
    { label: "层级", value: `第 ${menu.tree_level} 级` },
  ]
})

// ========== 权限列表 DataTable ==========

const permissionColumns: ColumnDef<Permission>[] = [
  {
    accessorKey: "name",
    header: "权限名称",
    size: 160,
    cell: ({ row }) => h("span", { class: "font-medium" }, row.original.name),
  },
  {
    accessorKey: "code",
    header: "权限编码",
    size: 140,
    cell: ({ row }) => h("span", { class: "font-mono text-sm" }, row.original.code),
  },
  {
    accessorKey: "resource",
    header: "资源",
    size: 100,
  },
  {
    accessorKey: "action",
    header: "操作",
    size: 80,
  },
  {
    accessorKey: "description",
    header: "描述",
    size: 200,
    cell: ({ row }) => row.original.description || "--",
  },
]

const permissionTable = useDataTable<Permission>({
  columns: permissionColumns,
  remoteFetchFn: async () => {
    return {
      code: 200,
      msg: "OK",
      data: permissions.value,
      total: permissions.value.length,
      page: 1,
      page_size: 100,
    }
  },
  enabled: () => !!selectedId.value && activeTab.value === "permissions",
})

// ========== 方法 ==========

/** 选择菜单节点 */
async function selectMenu(menu: MenuTreeNode) {
  selectedId.value = menu.id
  await loadMenuPermissions(menu.id)
}

/** 加载菜单权限 */
async function loadMenuPermissions(menuId: string) {
  permissionsLoading.value = true
  activeTab.value = "info"
  try {
    const res = await getMenuPermissions(menuId)
    permissions.value = res.data || []
    await permissionTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, "加载权限列表失败"))
    permissions.value = []
  } finally {
    permissionsLoading.value = false
  }
}

/** 查找菜单 */
function findMenuById(menus: MenuTreeNode[], id: string): MenuTreeNode | null {
  for (const menu of menus) {
    if (menu.id === id) return menu
    if (menu.children) {
      const found = findMenuById(menu.children, id)
      if (found) return found
    }
  }
  return null
}

// 初始化
onMounted(() => {
  menuStore.fetchMenus().then(() => {
    // 默认选中第一个菜单
    if (menuStore.menus.length > 0 && !selectedId.value) {
      selectMenu(menuStore.menus[0])
    }
  })
})
</script>

<template>
  <AppPage title="菜单管理" variant="workbench" description="查看系统菜单树结构与关联权限">
    <!-- Body -->
    <div class="flex gap-4 h-[calc(100vh-200px)]">
      <!-- 左侧：菜单树 -->
      <div class="w-[300px] shrink-0 flex flex-col border rounded-lg overflow-hidden">
        <div class="p-3 border-b bg-muted/30">
          <div class="relative">
            <Search class="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              v-model="searchKeyword"
              placeholder="搜索菜单..."
              class="pl-8"
            />
          </div>
        </div>

        <ScrollArea class="flex-1">
          <div v-if="loading" class="p-3 space-y-2">
            <Skeleton v-for="i in 8" :key="i" class="h-6 w-full" />
          </div>

          <div v-else-if="filteredTree.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            {{ searchKeyword ? "未找到匹配的菜单" : "暂无菜单数据" }}
          </div>

          <div v-else class="py-1">
            <MenuTreeNodeComponent
              :menus="filteredTree"
              :selected-id="selectedId"
              :depth="0"
              @select="selectMenu"
            />
          </div>
        </ScrollArea>
      </div>

      <!-- 右侧：详情 + Tabs -->
      <div class="flex-1 flex flex-col border rounded-lg overflow-hidden">
        <template v-if="selectedMenu">
          <!-- 头部信息 -->
          <div class="p-4 border-b bg-muted/20">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-lg font-semibold">{{ selectedMenu.name }}</h2>
                <p class="text-sm text-muted-foreground mt-1">
                  编码：{{ selectedMenu.code }}
                </p>
              </div>
              <Badge variant="outline">
                {{ selectedMenu.module }}
              </Badge>
            </div>
          </div>

          <!-- Tabs -->
          <Tabs v-model="activeTab" class="flex-1 flex flex-col">
            <div class="px-4 pt-2 border-b">
              <TabsList>
                <TabsTrigger value="info">
                  <Info class="h-4 w-4 mr-1" />
                  菜单信息
                </TabsTrigger>
                <TabsTrigger value="permissions">
                  <Shield class="h-4 w-4 mr-1" />
                  权限列表
                </TabsTrigger>
              </TabsList>
            </div>

            <ScrollArea class="flex-1">
              <!-- 菜单信息 Tab -->
              <TabsContent value="info" class="p-4 m-0">
                <DescriptionList :items="infoItems" :columns="2" bordered />
              </TabsContent>

              <!-- 权限列表 Tab -->
              <TabsContent value="permissions" class="p-4 m-0">
                <div v-if="permissionsLoading" class="py-4">
                  <Skeleton v-for="i in 5" :key="i" class="h-10 w-full mb-2" />
                </div>

                <div v-else-if="permissions.length === 0" class="py-8 text-center text-muted-foreground">
                  该菜单暂无关联权限
                </div>

                <DataTable v-else :data-table="permissionTable" :fixed-layout="true" />
              </TabsContent>
            </ScrollArea>
          </Tabs>
        </template>

        <div v-else class="flex-1 flex items-center justify-center text-muted-foreground">
          <div class="text-center">
            <FolderOpen class="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>请选择左侧菜单查看详情</p>
          </div>
        </div>
      </div>
    </div>
  </AppPage>
</template>
