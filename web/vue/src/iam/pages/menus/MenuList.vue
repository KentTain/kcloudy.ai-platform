<script setup lang="ts">
/**
 * MenuList 菜单管理页面
 * 左侧菜单树 + 右侧 Tabs（菜单信息、权限列表）
 * 参照 OrganizationPage.vue 布局设计
 */
import { computed, onMounted, ref, h } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import { FolderOpen, Info, Shield, Search } from '@lucide/vue'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import {
  Card,
  Badge,
  Skeleton,
  DescriptionList,
  type DescriptionItem,
  DataTable,
  useDataTable,
  Input,
} from '@/components'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useMenuStore } from '@/iam/stores/menu'
import { getMenuPermissions } from '@/iam/api/menu'
import type { MenuTreeNode, Permission } from '@/iam/types'
import { findMenuById } from '@/iam/utils/menu'
import { notifyError, getErrorMessage } from '@/framework/utils/feedback'
import MenuTree from '@/iam/components/MenuTree.vue'

const menuStore = useMenuStore()

// 状态
const selectedMenuId = ref<string | null>(null)
const activeTab = ref('info')
const permissions = ref<Permission[]>([])
const permissionsLoading = ref(false)
const searchKeyword = ref('')

// 当前选中的菜单对象
const selectedMenu = computed<MenuTreeNode | null>(() => {
  if (!selectedMenuId.value) return null
  return findMenuById(menuStore.menus, selectedMenuId.value)
})

// 搜索过滤
const filteredMenus = computed(() => {
  if (!searchKeyword.value.trim()) return menuStore.menus

  const keyword = searchKeyword.value.toLowerCase()

  function filterNodes(nodes: MenuTreeNode[]): MenuTreeNode[] {
    return nodes.reduce<MenuTreeNode[]>((acc, node) => {
      const matches = node.name.toLowerCase().includes(keyword) ||
        node.code.toLowerCase().includes(keyword)
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
    { label: '菜单名称', value: menu.name },
    { label: '菜单编码', value: menu.code },
    { label: '路由路径', value: menu.path || '--' },
    { label: '所属模块', value: menu.module },
    { label: '图标', value: menu.icon || '未设置' },
    { label: '是否可见', value: menu.is_visible ? '可见' : '隐藏' },
    { label: '排序号', value: String(menu.tree_sort) },
    { label: '层级', value: `第 ${menu.tree_level} 级` },
  ]
})

// 权限列表 DataTable 列定义
const permissionColumns: ColumnDef<Permission>[] = [
  {
    accessorKey: 'name',
    header: '权限名称',
    size: 160,
    cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name),
  },
  {
    accessorKey: 'code',
    header: '权限编码',
    size: 140,
    cell: ({ row }) => h('span', { class: 'font-mono text-sm' }, row.original.code),
  },
  {
    accessorKey: 'resource',
    header: '资源',
    size: 100,
  },
  {
    accessorKey: 'action',
    header: '操作',
    size: 80,
  },
  {
    accessorKey: 'description',
    header: '描述',
    size: 200,
    cell: ({ row }) => row.original.description || '--',
  },
]

const permissionTable = useDataTable<Permission>({
  columns: permissionColumns,
  remoteFetchFn: async () => {
    return {
      code: 200,
      msg: 'OK',
      data: permissions.value,
      total: permissions.value.length,
      page: 1,
      page_size: 100,
    }
  },
  enabled: () => !!selectedMenuId.value && activeTab.value === 'permissions',
})

// 加载菜单权限
async function loadMenuPermissions(menuId: string) {
  permissionsLoading.value = true
  try {
    const res = await getMenuPermissions(menuId)
    permissions.value = res.data || []
    await permissionTable.refresh(true)
  } catch (error) {
    notifyError(getErrorMessage(error, '加载权限列表失败'))
    permissions.value = []
  } finally {
    permissionsLoading.value = false
  }
}

// 处理菜单选中
async function handleMenuSelect(id: string | null) {
  selectedMenuId.value = id
  if (id) {
    activeTab.value = 'info'
    await loadMenuPermissions(id)
  } else {
    permissions.value = []
  }
}

// 加载菜单数据
onMounted(async () => {
  await menuStore.fetchMenus()
})
</script>

<template>
  <AppPage title="菜单管理" description="查看系统菜单树结构与关联权限" variant="workbench">
    <div class="flex gap-4 h-[calc(100vh-200px)]">
      <!-- 左侧：菜单树 -->
      <Card class="w-[300px] shrink-0 flex flex-col overflow-hidden py-0">
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
          <div v-if="menuStore.loading" class="p-3 space-y-2">
            <Skeleton v-for="i in 8" :key="i" class="h-6 w-full" />
          </div>

          <div v-else-if="filteredMenus.length === 0" class="p-4 text-center text-muted-foreground text-sm">
            {{ searchKeyword ? '未找到匹配的菜单' : '暂无菜单数据' }}
          </div>

          <div v-else class="py-1">
            <MenuTree
              :menus="filteredMenus"
              :selected-id="selectedMenuId"
              :loading="menuStore.loading"
              @update:selected-id="handleMenuSelect"
            />
          </div>
        </ScrollArea>
      </Card>

      <!-- 右侧：详情 + Tabs -->
      <Card class="flex-1 flex flex-col overflow-hidden py-0">
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

        <!-- 未选中状态 -->
        <div v-else class="flex-1 flex items-center justify-center text-muted-foreground">
          <div class="text-center">
            <FolderOpen class="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>请选择左侧菜单查看详情</p>
          </div>
        </div>
      </Card>
    </div>
  </AppPage>
</template>
