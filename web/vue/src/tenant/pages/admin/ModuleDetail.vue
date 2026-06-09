<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getModule, getModuleMenus, createModuleMenu, updateModuleMenu, deleteModuleMenu } from '@/tenant/api/module'
import type { Module, ModuleMenu, CreateMenuParams, UpdateMenuParams } from '@/tenant/types/admin'
import { notifyError, notifySuccess, notifyWarning } from '@/framework/utils/feedback'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tree } from '@/components/ui/tree'
import type { TreeNodeType } from '@/components/ui/tree'
import { ArrowLeft, Pencil, Package, Menu, Key, Users, Plus, Trash2, FolderOpen, FileText } from '@lucide/vue'

const route = useRoute()
const router = useRouter()

const moduleId = computed(() => route.params.id as string)
const moduleData = ref<Module | null>(null)
const loading = ref(false)

// 当前激活的 Tab
const activeTab = ref('info')

// ==================== 菜单管理状态 ====================
const menus = ref<ModuleMenu[]>([])
const menusLoading = ref(false)
const selectedMenuId = ref<string | null>(null)
const expandedMenuIds = ref<string[]>([])
const menuDialogOpen = ref(false)
const menuDialogMode = ref<'create' | 'edit'>('create')
const deleteMenuDialogOpen = ref(false)

// 菜单表单
const menuForm = ref({
  name: '',
  code: '',
  path: '',
  parent_id: '',
  icon: '',
  sort: 10,
})

// 加载模块详情
const loadModule = async () => {
  loading.value = true
  try {
    const response = await getModule(moduleId.value)
    if (response.data) {
      moduleData.value = response.data
    }
  } catch (error) {
    console.error('加载模块详情失败:', error)
    notifyError('加载模块详情失败')
  } finally {
    loading.value = false
  }
}

// 返回列表
const handleBack = () => {
  router.push('/admin/modules')
}

// 编辑模块
const handleEdit = () => {
  router.push(`/admin/modules/${moduleId.value}/edit`)
}

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString()
}

// ==================== 菜单管理方法 ====================

// 将 ModuleMenu 转换为 TreeNodeType
const convertToTreeNode = (menuList: ModuleMenu[]): TreeNodeType[] => {
  return menuList.map(menu => ({
    value: menu.id,
    label: menu.name,
    children: menu.children ? convertToTreeNode(menu.children) : [],
  }))
}

// 菜单树数据
const menuTreeData = computed<TreeNodeType[]>(() => convertToTreeNode(menus.value))

// 选中的菜单节点值（用于 Tree 组件）
const selectedMenuValues = computed<string[]>(() => selectedMenuId.value ? [selectedMenuId.value] : [])

// 当前选中的菜单对象
const selectedMenu = computed<ModuleMenu | null>(() => {
  if (!selectedMenuId.value) return null
  return findMenuById(menus.value, selectedMenuId.value)
})

// 递归查找菜单
const findMenuById = (menuList: ModuleMenu[], id: string): ModuleMenu | null => {
  for (const menu of menuList) {
    if (menu.id === id) return menu
    if (menu.children) {
      const found = findMenuById(menu.children, id)
      if (found) return found
    }
  }
  return null
}

// 获取所有菜单的扁平列表（用于父菜单选择）
const flattenMenus = (menuList: ModuleMenu[], level = 0): Array<{ id: string; name: string; level: number }> => {
  const result: Array<{ id: string; name: string; level: number }> = []
  for (const menu of menuList) {
    result.push({ id: menu.id, name: menu.name, level })
    if (menu.children) {
      result.push(...flattenMenus(menu.children, level + 1))
    }
  }
  return result
}

// 可选的父菜单列表（编辑时排除当前菜单及其子菜单）
const parentMenuOptions = computed(() => {
  const allMenus = flattenMenus(menus.value)
  if (menuDialogMode.value === 'edit' && selectedMenuId.value) {
    // 获取当前菜单及其所有子菜单的 ID
    const excludeIds = new Set<string>()
    const collectChildren = (menu: ModuleMenu) => {
      excludeIds.add(menu.id)
      if (menu.children) {
        menu.children.forEach(collectChildren)
      }
    }
    const currentMenu = findMenuById(menus.value, selectedMenuId.value)
    if (currentMenu) collectChildren(currentMenu)
    return allMenus.filter(m => !excludeIds.has(m.id))
  }
  return allMenus
})

// 加载菜单数据
const loadMenus = async () => {
  if (!moduleId.value) return
  menusLoading.value = true
  try {
    const response = await getModuleMenus(moduleId.value)
    if (response.data) {
      menus.value = response.data
      // 默认展开第一级
      expandedMenuIds.value = menus.value.map(m => m.id)
    }
  } catch (error) {
    console.error('加载菜单失败:', error)
    notifyError('加载菜单失败')
  } finally {
    menusLoading.value = false
  }
}

// 处理菜单树节点点击
const handleMenuNodeClick = (node: TreeNodeType) => {
  selectedMenuId.value = node.value as string
}

// 打开新增菜单弹窗
const openCreateMenuDialog = () => {
  menuDialogMode.value = 'create'
  menuForm.value = {
    name: '',
    code: '',
    path: '',
    parent_id: selectedMenuId.value || '',
    icon: '',
    sort: 10,
  }
  menuDialogOpen.value = true
}

// 打开编辑菜单弹窗
const openEditMenuDialog = () => {
  if (!selectedMenu.value) return
  menuDialogMode.value = 'edit'
  menuForm.value = {
    name: selectedMenu.value.name,
    code: selectedMenu.value.code,
    path: selectedMenu.value.path,
    parent_id: selectedMenu.value.parent_id || '',
    icon: selectedMenu.value.icon || '',
    sort: selectedMenu.value.sort,
  }
  menuDialogOpen.value = true
}

// 检查菜单是否有子菜单
const hasChildren = (menu: ModuleMenu): boolean => {
  return !!(menu.children && menu.children.length > 0)
}

// 打开删除确认弹窗
const openDeleteMenuDialog = () => {
  if (!selectedMenu.value) return
  if (hasChildren(selectedMenu.value)) {
    notifyWarning('该菜单存在子菜单，无法删除')
    return
  }
  deleteMenuDialogOpen.value = true
}

// 保存菜单
const saveMenu = async () => {
  if (!menuForm.value.name.trim()) {
    notifyWarning('请输入菜单名称')
    return
  }
  if (!menuForm.value.code.trim()) {
    notifyWarning('请输入菜单编码')
    return
  }
  if (!menuForm.value.path.trim()) {
    notifyWarning('请输入菜单路径')
    return
  }

  try {
    const params: CreateMenuParams | UpdateMenuParams = {
      name: menuForm.value.name.trim(),
      code: menuForm.value.code.trim(),
      path: menuForm.value.path.trim(),
      parent_id: menuForm.value.parent_id || undefined,
      icon: menuForm.value.icon.trim() || undefined,
      sort: menuForm.value.sort,
    }

    if (menuDialogMode.value === 'create') {
      await createModuleMenu(moduleId.value, params as CreateMenuParams)
      notifySuccess('菜单创建成功')
    } else if (selectedMenuId.value) {
      // 编辑模式下不修改 code
      delete params.code
      await updateModuleMenu(moduleId.value, selectedMenuId.value, params as UpdateMenuParams)
      notifySuccess('菜单更新成功')
    }

    menuDialogOpen.value = false
    await loadMenus()
  } catch (error) {
    console.error('保存菜单失败:', error)
    notifyError('保存菜单失败')
  }
}

// 删除菜单
const deleteMenu = async () => {
  if (!selectedMenuId.value) return
  try {
    await deleteModuleMenu(moduleId.value, selectedMenuId.value)
    notifySuccess('菜单删除成功')
    deleteMenuDialogOpen.value = false
    selectedMenuId.value = null
    await loadMenus()
  } catch (error) {
    console.error('删除菜单失败:', error)
    notifyError('删除菜单失败')
  }
}

// 监听 Tab 切换，加载菜单数据
watch(activeTab, (newTab) => {
  if (newTab === 'menus' && menus.value.length === 0) {
    loadMenus()
  }
})

onMounted(() => {
  loadModule()
})
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="flex items-center gap-3">
        <Button variant="ghost" size="icon" @click="handleBack">
          <ArrowLeft class="h-4 w-4" />
        </Button>
        <div>
          <h2 class="text-xl font-semibold">
            <span v-if="loading"><Skeleton class="h-6 w-32" /></span>
            <span v-else>{{ moduleData?.name || '模块详情' }}</span>
          </h2>
          <p class="text-muted-foreground mt-1 text-sm">
            <span v-if="loading"><Skeleton class="h-4 w-24" /></span>
            <span v-else>{{ moduleData?.code || '--' }}</span>
          </p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <Button @click="handleEdit">
          <Pencil class="mr-1 h-4 w-4" />
          编辑模块
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Package class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">模块状态</span>
        </div>
        <div class="mt-2">
          <Badge v-if="moduleData" :variant="moduleData.is_active ? 'default' : 'secondary'">
            {{ moduleData.is_active ? '启用' : '停用' }}
          </Badge>
          <Skeleton v-else class="h-5 w-12" />
        </div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Key class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">必须模块</span>
        </div>
        <div class="mt-2">
          <Badge v-if="moduleData" :variant="moduleData.is_need ? 'default' : 'outline'">
            {{ moduleData.is_need ? '是' : '否' }}
          </Badge>
          <Skeleton v-else class="h-5 w-12" />
        </div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Users class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">分配租户</span>
        </div>
        <div class="text-2xl font-semibold">
          <span v-if="moduleData">{{ moduleData.tenant_count || 0 }}</span>
          <Skeleton v-else class="h-7 w-8" />
        </div>
      </Card>
    </div>

    <!-- Tab 切换区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <Tabs v-model="activeTab" class="flex h-full flex-col">
        <div class="border-b px-5 pt-4">
          <TabsList>
            <TabsTrigger value="info">
              <Package class="mr-1 h-4 w-4" />
              基本信息
            </TabsTrigger>
            <TabsTrigger value="menus">
              <Menu class="mr-1 h-4 w-4" />
              菜单管理
            </TabsTrigger>
            <TabsTrigger value="permissions">
              <Key class="mr-1 h-4 w-4" />
              权限管理
            </TabsTrigger>
            <TabsTrigger value="roles">
              <Users class="mr-1 h-4 w-4" />
              角色管理
            </TabsTrigger>
          </TabsList>
        </div>

        <div class="min-h-0 flex-1 overflow-auto px-5 py-5">
          <!-- 基本信息 Tab -->
          <TabsContent value="info" class="mt-0">
            <div v-if="loading" class="space-y-4">
              <div v-for="n in 6" :key="n" class="grid gap-4 md:grid-cols-2">
                <Skeleton class="h-16 w-full" />
                <Skeleton class="h-16 w-full" />
              </div>
            </div>
            <div v-else-if="moduleData" class="grid gap-4 md:grid-cols-2">
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块名称</div>
                <div class="mt-2 font-medium">{{ moduleData.name }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块编码</div>
                <div class="mt-2 font-medium">{{ moduleData.code }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块图标</div>
                <div class="mt-2 font-medium">{{ moduleData.icon || '未设置' }}</div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">模块状态</div>
                <div class="mt-2">
                  <Badge :variant="moduleData.is_active ? 'default' : 'secondary'">
                    {{ moduleData.is_active ? '启用' : '停用' }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">是否必须模块</div>
                <div class="mt-2">
                  <Badge :variant="moduleData.is_need ? 'default' : 'outline'">
                    {{ moduleData.is_need ? '是' : '否' }}
                  </Badge>
                </div>
              </div>
              <div class="rounded-lg border p-4">
                <div class="text-muted-foreground text-xs">创建时间</div>
                <div class="mt-2 font-medium">{{ formatDate(moduleData.created_at) }}</div>
              </div>
              <div class="rounded-lg border p-4 md:col-span-2">
                <div class="text-muted-foreground text-xs">模块描述</div>
                <div class="mt-2 text-sm leading-6">{{ moduleData.description || '暂无描述' }}</div>
              </div>
            </div>
          </TabsContent>

          <!-- 菜单管理 Tab -->
          <TabsContent value="menus" class="mt-0">
            <div v-if="menusLoading" class="flex h-full items-center justify-center py-12">
              <Skeleton class="h-8 w-8 rounded-full" />
            </div>
            <div v-else class="flex h-full min-h-[400px] gap-4">
              <!-- 左侧菜单树 -->
              <Card class="flex min-h-0 w-[300px] shrink-0 flex-col gap-0 overflow-hidden py-0">
                <div class="border-b px-4 py-4">
                  <div class="flex items-center justify-between">
                    <div class="font-medium">菜单树</div>
                    <Button size="sm" @click="openCreateMenuDialog">
                      <Plus class="mr-1 h-4 w-4" />
                      新增
                    </Button>
                  </div>
                  <div class="text-muted-foreground mt-1 text-xs">点击菜单项查看详情</div>
                </div>
                <ScrollArea class="min-h-0 flex-1 px-3 py-3">
                  <div v-if="menus.length === 0" class="text-muted-foreground py-8 text-center text-sm">
                    暂无菜单数据
                  </div>
                  <Tree
                    v-else
                    v-model="selectedMenuValues"
                    :data="menuTreeData"
                    :expanded-value="expandedMenuIds"
                    :multiple="false"
                    :show-line="true"
                    @on-node-click="handleMenuNodeClick"
                  >
                    <template #leaf-icon>
                      <FileText class="h-4 w-4 text-muted-foreground" />
                    </template>
                  </Tree>
                </ScrollArea>
              </Card>

              <!-- 右侧菜单详情 -->
              <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
                <div class="border-b px-5 py-4">
                  <div class="flex items-center justify-between">
                    <div class="font-medium">{{ selectedMenu?.name || '菜单详情' }}</div>
                    <div v-if="selectedMenu" class="flex items-center gap-2">
                      <Button size="sm" variant="outline" @click="openEditMenuDialog">
                        <Pencil class="mr-1 h-4 w-4" />
                        编辑
                      </Button>
                      <Button size="sm" variant="destructive" @click="openDeleteMenuDialog">
                        <Trash2 class="mr-1 h-4 w-4" />
                        删除
                      </Button>
                    </div>
                  </div>
                  <div v-if="selectedMenu" class="text-muted-foreground mt-1 text-xs">
                    编码：{{ selectedMenu.code }}
                  </div>
                </div>
                <div v-if="selectedMenu" class="flex-1 overflow-auto px-5 py-5">
                  <div class="grid gap-4 md:grid-cols-2">
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单名称</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.name }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单编码</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.code }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单路径</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.path }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">菜单图标</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.icon || '未设置' }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">排序</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.sort }}</div>
                    </div>
                    <div class="rounded-lg border p-4">
                      <div class="text-muted-foreground text-xs">子菜单数量</div>
                      <div class="mt-2 font-medium">{{ selectedMenu.children?.length || 0 }}</div>
                    </div>
                    <div class="rounded-lg border p-4 md:col-span-2">
                      <div class="text-muted-foreground text-xs">创建时间</div>
                      <div class="mt-2 font-medium">{{ formatDate(selectedMenu.created_at) }}</div>
                    </div>
                  </div>
                </div>
                <div v-else class="flex flex-1 flex-col items-center justify-center gap-4 py-12">
                  <FolderOpen class="text-muted-foreground h-12 w-12" />
                  <div class="text-center">
                    <div class="font-medium">请选择菜单</div>
                    <div class="text-muted-foreground mt-1 text-sm">从左侧树中选择一个菜单查看详情</div>
                  </div>
                </div>
              </Card>
            </div>
          </TabsContent>

          <!-- 权限管理 Tab -->
          <TabsContent value="permissions" class="mt-0">
            <div class="flex h-full flex-col items-center justify-center gap-4 py-12">
              <Key class="text-muted-foreground h-16 w-16" />
              <div class="text-center">
                <div class="font-medium">权限管理功能开发中</div>
                <div class="text-muted-foreground mt-1 text-sm">权限管理功能将在后续实现</div>
              </div>
            </div>
          </TabsContent>

          <!-- 角色管理 Tab -->
          <TabsContent value="roles" class="mt-0">
            <div class="flex h-full flex-col items-center justify-center gap-4 py-12">
              <Users class="text-muted-foreground h-16 w-16" />
              <div class="text-center">
                <div class="font-medium">角色管理功能开发中</div>
                <div class="text-muted-foreground mt-1 text-sm">角色管理功能将在后续实现</div>
              </div>
            </div>
          </TabsContent>
        </div>
      </Tabs>
    </Card>

    <!-- 菜单表单弹窗 -->
    <Dialog v-model:open="menuDialogOpen">
      <DialogContent class="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>{{ menuDialogMode === 'create' ? '新增菜单' : '编辑菜单' }}</DialogTitle>
        </DialogHeader>
        <div class="grid gap-4 py-4">
          <div class="grid gap-2">
            <Label>菜单名称 <span class="text-destructive">*</span></Label>
            <Input v-model="menuForm.name" placeholder="请输入菜单名称" />
          </div>
          <div class="grid gap-2">
            <Label>菜单编码 <span class="text-destructive">*</span></Label>
            <Input
              v-model="menuForm.code"
              placeholder="请输入菜单编码"
              :disabled="menuDialogMode === 'edit'"
            />
            <p v-if="menuDialogMode === 'edit'" class="text-muted-foreground text-xs">编码不可修改</p>
          </div>
          <div class="grid gap-2">
            <Label>菜单路径 <span class="text-destructive">*</span></Label>
            <Input v-model="menuForm.path" placeholder="请输入菜单路径，如 /system/users" />
          </div>
          <div class="grid gap-2">
            <Label>父菜单</Label>
            <Select v-model="menuForm.parent_id">
              <SelectTrigger>
                <SelectValue placeholder="请选择父菜单（不选则为顶级菜单）" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">无（顶级菜单）</SelectItem>
                <SelectItem
                  v-for="option in parentMenuOptions"
                  :key="option.id"
                  :value="option.id"
                >
                  {{ '-- '.repeat(option.level) }}{{ option.name }}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="grid gap-2">
            <Label>菜单图标</Label>
            <Input v-model="menuForm.icon" placeholder="请输入图标名称" />
          </div>
          <div class="grid gap-2">
            <Label>排序</Label>
            <Input v-model.number="menuForm.sort" type="number" placeholder="数字越小越靠前" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="menuDialogOpen = false">取消</Button>
          <Button @click="saveMenu">保存</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除确认弹窗 -->
    <Dialog v-model:open="deleteMenuDialogOpen">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>确认删除菜单</DialogTitle>
          <DialogDescription>
            确定要删除菜单「{{ selectedMenu?.name }}」吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="deleteMenuDialogOpen = false">取消</Button>
          <Button
            variant="destructive"
            @click="deleteMenu"
          >
            确认删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
