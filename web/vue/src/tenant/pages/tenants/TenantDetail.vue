<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTenantStore } from '@/tenant/stores/tenant'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Badge, Skeleton, Input, Label, DescriptionList, type DescriptionItem } from '@/components'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from '@/components'
import {
  Pencil,
  ShieldCheck,
  ShieldOff,
  Database,
  HardDrive,
  Zap,
  Mail,
  Radio,
  Package,
  Plus,
  Trash2,
  Loader2,
} from '@lucide/vue'
import { notifyError, notifySuccess } from '@/framework/utils/feedback'
import {
  getTenantResources,
  updateTenantResources,
  getTenantModules,
  assignModuleToTenant,
  unassignModuleFromTenant,
  getDatabaseConfigs,
  getStorageConfigs,
  getCacheConfigs,
  getQueueConfigs,
  getPubsubConfigs,
  testDatabaseConnection,
  testStorageConnection,
  testCacheConnection,
  testQueueConnection,
  testPubsubConnection,
  getModules,
} from '@/tenant/api'
import type {
  TenantResource,
  TenantModule,
  Module,
  DatabaseConfig,
  StorageConfig,
  CacheConfig,
  QueueConfig,
  PubsubConfig,
} from '@/tenant/types'

const route = useRoute()
const router = useRouter()
const tenantStore = useTenantStore()

const tenantId = computed(() => route.params.id as string)
const loading = ref(false)
const activeTab = ref('info')

// ==================== 资源绑定状态 ====================
const tenantResource = ref<TenantResource | null>(null)
const resourceLoading = ref(false)
const resourceSaving = ref(false)

// 资源配置列表
const databaseConfigs = ref<DatabaseConfig[]>([])
const storageConfigs = ref<StorageConfig[]>([])
const cacheConfigs = ref<CacheConfig[]>([])
const queueConfigs = ref<QueueConfig[]>([])
const pubsubConfigs = ref<PubsubConfig[]>([])

// 资源表单
const resourceForm = ref({
  database_id: '',
  storage_id: '',
  cache_id: '',
  queue_id: '',
  pubsub_id: '',
})

// 测试连接状态
const testingConnection = ref({
  database: false,
  storage: false,
  cache: false,
  queue: false,
  pubsub: false,
})

// ==================== 模块分配状态 ====================
const tenantModules = ref<TenantModule[]>([])
const modulesLoading = ref(false)
const allModules = ref<Module[]>([])
const assignModuleDialogOpen = ref(false)
const assignModuleLoading = ref(false)
const unassignDialogOpen = ref(false)
const unassigningModule = ref<TenantModule | null>(null)
const unassignLoading = ref(false)

// 模块选择表单
const moduleSelectForm = ref({
  module_id: '',
  expired_at: '',
})

const loadTenantDetail = async () => {
  loading.value = true
  try {
    await tenantStore.fetchTenant(tenantId.value)
  } finally {
    loading.value = false
  }
}

const handleEdit = () => {
  router.push(`/admin/tenants/${tenantId.value}/edit`)
}

const handleBack = () => {
  router.back()
}

const handleActivate = async () => {
  await tenantStore.activate(tenantId.value)
  await loadTenantDetail()
}

const handleDeactivate = async () => {
  await tenantStore.deactivate(tenantId.value)
  await loadTenantDetail()
}

// ==================== 资源绑定方法 ====================
const loadTenantResources = async () => {
  resourceLoading.value = true
  try {
    const res = await getTenantResources(tenantId.value)
    if (res.data) {
      tenantResource.value = res.data
      resourceForm.value = {
        database_id: res.data.database_id || '',
        storage_id: res.data.storage_id || '',
        cache_id: res.data.cache_id || '',
        queue_id: res.data.queue_id || '',
        pubsub_id: res.data.pubsub_id || '',
      }
    }
  } catch (error) {
    notifyError('加载资源绑定失败')
  } finally {
    resourceLoading.value = false
  }
}

const loadResourceConfigs = async () => {
  try {
    const [dbRes, storageRes, cacheRes, queueRes, pubsubRes] = await Promise.all([
      getDatabaseConfigs({ page_size: 100 }),
      getStorageConfigs({ page_size: 100 }),
      getCacheConfigs({ page_size: 100 }),
      getQueueConfigs({ page_size: 100 }),
      getPubsubConfigs({ page_size: 100 }),
    ])
    databaseConfigs.value = dbRes.data || []
    storageConfigs.value = storageRes.data || []
    cacheConfigs.value = cacheRes.data || []
    queueConfigs.value = queueRes.data || []
    pubsubConfigs.value = pubsubRes.data || []
  } catch (error) {
    notifyError('加载资源配置列表失败')
  }
}

const handleTestConnection = async (type: 'database' | 'storage' | 'cache' | 'queue' | 'pubsub') => {
  const configId = resourceForm.value[`${type}_id` as keyof typeof resourceForm.value]
  if (!configId) {
    notifyError('请先选择配置')
    return
  }

  testingConnection.value[type] = true
  try {
    const testFunctions = {
      database: testDatabaseConnection,
      storage: testStorageConnection,
      cache: testCacheConnection,
      queue: testQueueConnection,
      pubsub: testPubsubConnection,
    }
    const res = await testFunctions[type](configId)
    if (res.data?.success) {
      notifySuccess(`连接成功，延迟: ${res.data.latency}ms`)
    } else {
      notifyError(`连接失败: ${res.data?.error || '未知错误'}`)
    }
  } catch (error) {
    notifyError('测试连接失败')
  } finally {
    testingConnection.value[type] = false
  }
}

const handleSaveResources = async () => {
  resourceSaving.value = true
  try {
    await updateTenantResources(tenantId.value, {
      database_id: resourceForm.value.database_id === 'none' ? undefined : resourceForm.value.database_id || undefined,
      storage_id: resourceForm.value.storage_id === 'none' ? undefined : resourceForm.value.storage_id || undefined,
      cache_id: resourceForm.value.cache_id === 'none' ? undefined : resourceForm.value.cache_id || undefined,
      queue_id: resourceForm.value.queue_id === 'none' ? undefined : resourceForm.value.queue_id || undefined,
      pubsub_id: resourceForm.value.pubsub_id === 'none' ? undefined : resourceForm.value.pubsub_id || undefined,
    })
    notifySuccess('资源绑定保存成功')
    await loadTenantResources()
  } catch (error) {
    notifyError('保存资源绑定失败')
  } finally {
    resourceSaving.value = false
  }
}

// ==================== 模块分配方法 ====================
const loadTenantModules = async () => {
  modulesLoading.value = true
  try {
    const res = await getTenantModules(tenantId.value)
    tenantModules.value = res.data || []
  } catch (error) {
    notifyError('加载租户模块失败')
  } finally {
    modulesLoading.value = false
  }
}

const loadAllModules = async () => {
  try {
    const res = await getModules({ page_size: 100, is_active: true })
    allModules.value = res.data || []
  } catch (error) {
    notifyError('加载模块列表失败')
  }
}

const handleOpenAssignModuleDialog = () => {
  moduleSelectForm.value = {
    module_id: '',
    expired_at: '',
  }
  assignModuleDialogOpen.value = true
}

const handleAssignModule = async () => {
  if (!moduleSelectForm.value.module_id) {
    notifyError('请选择要分配的模块')
    return
  }

  assignModuleLoading.value = true
  try {
    await assignModuleToTenant(tenantId.value, {
      module_id: moduleSelectForm.value.module_id,
      expired_at: moduleSelectForm.value.expired_at || undefined,
    })
    notifySuccess('模块分配成功')
    assignModuleDialogOpen.value = false
    await loadTenantModules()
  } catch (error) {
    notifyError('模块分配失败')
  } finally {
    assignModuleLoading.value = false
  }
}

const handleOpenUnassignDialog = (module: TenantModule) => {
  unassigningModule.value = module
  unassignDialogOpen.value = true
}

const handleUnassignModule = async () => {
  if (!unassigningModule.value) return

  unassignLoading.value = true
  try {
    await unassignModuleFromTenant(tenantId.value, unassigningModule.value.module_id)
    notifySuccess('取消模块分配成功')
    unassignDialogOpen.value = false
    unassigningModule.value = null
    await loadTenantModules()
  } catch (error) {
    notifyError('取消模块分配失败')
  } finally {
    unassignLoading.value = false
  }
}

// 已分配的模块 ID 集合
const assignedModuleIds = computed(() => {
  return new Set(tenantModules.value.map((m) => m.module_id))
})

// 可分配的模块列表（排除已分配的）
const availableModules = computed(() => {
  return allModules.value.filter((m) => !assignedModuleIds.value.has(m.id))
})

// Tab 切换时加载数据
watch(activeTab, async (newTab) => {
  if (newTab === 'resources' && !tenantResource.value) {
    await Promise.all([loadTenantResources(), loadResourceConfigs()])
  } else if (newTab === 'modules' && tenantModules.value.length === 0) {
    await Promise.all([loadTenantModules(), loadAllModules()])
  }
})

const descriptionItems = computed<DescriptionItem[]>(() => {
  const tenant = tenantStore.currentTenant
  if (!tenant) return []

  return [
    { label: '租户名称', value: tenant.name },
    { label: '租户编码', value: tenant.code },
    { label: '联系人', value: tenant.contact_name },
    { label: '联系人邮箱', value: tenant.contact_email },
    { label: '联系人电话', value: tenant.contact_phone },
    {
      label: '状态',
      value: tenant.status === 'active' ? '激活' : '停用',
      type: 'badge',
      badgeVariant: tenant.status === 'active' ? 'default' : 'secondary',
    },
    {
      label: '过期时间',
      value: tenant.expired_at ? new Date(tenant.expired_at).toLocaleString() : '永久',
    },
    { label: '创建时间', value: new Date(tenant.created_at).toLocaleString() },
  ]
})

// 资源类型配置
const resourceTypes = [
  { key: 'database', label: '数据库', icon: Database, configs: databaseConfigs, testFn: testDatabaseConnection },
  { key: 'storage', label: '存储', icon: HardDrive, configs: storageConfigs, testFn: testStorageConnection },
  { key: 'cache', label: '缓存', icon: Zap, configs: cacheConfigs, testFn: testCacheConnection },
  { key: 'queue', label: '队列', icon: Mail, configs: queueConfigs, testFn: testQueueConnection },
  { key: 'pubsub', label: '发布订阅', icon: Radio, configs: pubsubConfigs, testFn: testPubsubConnection },
] as const

onMounted(() => {
  loadTenantDetail()
})
</script>

<template>
  <AppPage title="租户详情" variant="detail">
    <template #actions>
      <div class="flex gap-2">
        <Button variant="outline" @click="handleBack" data-testid="back-button">返回</Button>
        <Button @click="handleEdit" data-testid="edit-button">
          <Pencil class="mr-1 h-4 w-4" />
          编辑
        </Button>
        <Button
          v-if="tenantStore.currentTenant?.status === 'inactive'"
          variant="outline"
          data-testid="activate-button"
          @click="handleActivate"
        >
          <ShieldCheck class="mr-1 h-4 w-4" />
          激活
        </Button>
        <Button
          v-if="tenantStore.currentTenant?.status === 'active'"
          variant="outline"
          data-testid="deactivate-button"
          @click="handleDeactivate"
        >
          <ShieldOff class="mr-1 h-4 w-4" />
          停用
        </Button>
      </div>
    </template>

    <Tabs v-model="activeTab" class="w-full">
      <TabsList>
        <TabsTrigger value="info" data-testid="tab-info">基本信息</TabsTrigger>
        <TabsTrigger value="resources" data-testid="tab-resources">资源绑定</TabsTrigger>
        <TabsTrigger value="modules" data-testid="tab-modules">模块分配</TabsTrigger>
      </TabsList>

      <!-- 基本信息 Tab -->
      <TabsContent value="info">
        <div v-if="loading" class="flex flex-col gap-3">
          <div v-for="n in 4" :key="n" class="h-5">
            <div class="h-5 w-full bg-muted animate-pulse rounded" />
          </div>
        </div>
        <DescriptionList v-else :items="descriptionItems" :columns="2" bordered data-testid="tenant-info" />
      </TabsContent>

      <!-- 资源绑定 Tab -->
      <TabsContent value="resources">
        <div v-if="resourceLoading" class="space-y-4">
          <div v-for="n in 5" :key="n" class="h-16">
            <Skeleton class="h-16 w-full" />
          </div>
        </div>
        <div v-else class="space-y-6">
          <Card v-for="resourceType in resourceTypes" :key="resourceType.key">
            <CardHeader class="pb-3">
              <CardTitle class="flex items-center gap-2 text-base">
                <component :is="resourceType.icon" class="h-5 w-5" />
                {{ resourceType.label }}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div class="flex items-end gap-4">
                <div class="flex-1">
                  <Label :for="`${resourceType.key}-select`" class="mb-2 block">
                    选择{{ resourceType.label }}配置
                  </Label>
                  <Select
                    :id="`${resourceType.key}-select`"
                    v-model="resourceForm[`${resourceType.key}_id`]"
                  >
                    <SelectTrigger>
                      <SelectValue :placeholder="`选择${resourceType.label}配置`" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">不绑定</SelectItem>
                      <SelectItem
                        v-for="config in resourceType.configs.value"
                        :key="config.id"
                        :value="config.id"
                      >
                        {{ config.name }}
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button
                  variant="outline"
                  :disabled="!resourceForm[`${resourceType.key}_id`] || testingConnection[resourceType.key]"
                  @click="handleTestConnection(resourceType.key)"
                >
                  <Loader2 v-if="testingConnection[resourceType.key]" class="mr-1 h-4 w-4 animate-spin" />
                  测试连接
                </Button>
              </div>
              <!-- 显示当前绑定的配置信息 -->
              <div
                v-if="tenantResource?.[`${resourceType.key}_config` as keyof TenantResource]"
                class="mt-3 text-sm text-muted-foreground"
              >
                <span class="font-medium">当前绑定：</span>
                {{ (tenantResource[`${resourceType.key}_config` as keyof TenantResource] as any)?.name || '未绑定' }}
              </div>
            </CardContent>
          </Card>

          <div class="flex justify-end">
            <Button :disabled="resourceSaving" @click="handleSaveResources">
              <Loader2 v-if="resourceSaving" class="mr-1 h-4 w-4 animate-spin" />
              保存资源绑定
            </Button>
          </div>
        </div>
      </TabsContent>

      <!-- 模块分配 Tab -->
      <TabsContent value="modules">
        <Card>
          <CardHeader>
            <div class="flex items-center justify-between">
              <CardTitle class="flex items-center gap-2 text-base">
                <Package class="h-5 w-5" />
                已分配模块
              </CardTitle>
              <Button @click="handleOpenAssignModuleDialog">
                <Plus class="mr-1 h-4 w-4" />
                分配模块
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div v-if="modulesLoading" class="space-y-2">
              <div v-for="n in 3" :key="n">
                <Skeleton class="h-12 w-full" />
              </div>
            </div>
            <Table v-else-if="tenantModules.length > 0">
              <TableHeader>
                <TableRow>
                  <TableHead>模块名称</TableHead>
                  <TableHead>模块编码</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>分配时间</TableHead>
                  <TableHead>过期时间</TableHead>
                  <TableHead class="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="tm in tenantModules" :key="tm.id">
                  <TableCell>
                    <Button
                      variant="ghost"
                      class="h-auto p-0 font-medium"
                      @click="router.push(`/admin/modules/${tm.module_id}`)"
                    >
                      {{ tm.module?.name || tm.module_id }}
                    </Button>
                  </TableCell>
                  <TableCell>{{ tm.module?.code || '-' }}</TableCell>
                  <TableCell>
                    <Badge :variant="tm.is_active ? 'default' : 'secondary'">
                      {{ tm.is_active ? '启用' : '禁用' }}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {{ new Date(tm.assigned_at).toLocaleString() }}
                  </TableCell>
                  <TableCell>
                    {{ tm.expired_at ? new Date(tm.expired_at).toLocaleString() : '永久' }}
                  </TableCell>
                  <TableCell class="text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      @click="handleOpenUnassignDialog(tm)"
                    >
                      <Trash2 class="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
            <div v-else class="text-center py-8 text-muted-foreground">
              暂未分配任何模块
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>

    <!-- 分配模块对话框 -->
    <Dialog v-model:open="assignModuleDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>分配模块</DialogTitle>
          <DialogDescription>
            选择要分配给该租户的模块
          </DialogDescription>
        </DialogHeader>
        <div class="space-y-4 py-4">
          <div class="space-y-2">
            <Label>选择模块</Label>
            <Select v-model="moduleSelectForm.module_id">
              <SelectTrigger>
                <SelectValue placeholder="选择模块" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem
                  v-for="module in availableModules"
                  :key="module.id"
                  :value="module.id"
                >
                  {{ module.name }} ({{ module.code }})
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div v-if="availableModules.length === 0" class="text-sm text-muted-foreground">
            所有可用模块已分配完毕
          </div>
          <div class="space-y-2">
            <Label>过期时间（可选）</Label>
            <Input
              v-model="moduleSelectForm.expired_at"
              type="datetime-local"
              placeholder="不设置则为永久有效"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="assignModuleDialogOpen = false">
            取消
          </Button>
          <Button
            :disabled="assignModuleLoading || !moduleSelectForm.module_id"
            @click="handleAssignModule"
          >
            <Loader2 v-if="assignModuleLoading" class="mr-1 h-4 w-4 animate-spin" />
            确认分配
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 取消分配确认对话框 -->
    <Dialog v-model:open="unassignDialogOpen">
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认取消分配</DialogTitle>
          <DialogDescription>
            确定要取消租户对模块「{{ unassigningModule?.module?.name || unassigningModule?.module_id }}」的分配吗？此操作不可撤销。
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" @click="unassignDialogOpen = false">
            取消
          </Button>
          <Button
            variant="ghost"
            :disabled="unassignLoading"
            @click="handleUnassignModule"
          >
            <Loader2 v-if="unassignLoading" class="mr-1 h-4 w-4 animate-spin" />
            确认取消
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </AppPage>
</template>

