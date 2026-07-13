<script setup lang="ts">
import { ref, computed, h } from 'vue'
import type { ColumnDef } from '@tanstack/vue-table'
import {
  getDatabaseConfigs,
  createDatabaseConfig,
  updateDatabaseConfig,
  deleteDatabaseConfig,
  testDatabaseConnection,
  getStorageConfigs,
  createStorageConfig,
  updateStorageConfig,
  deleteStorageConfig,
  testStorageConnection,
  getCacheConfigs,
  createCacheConfig,
  updateCacheConfig,
  deleteCacheConfig,
  testCacheConnection,
  getQueueConfigs,
  createQueueConfig,
  updateQueueConfig,
  deleteQueueConfig,
  testQueueConnection,
  getPubsubConfigs,
  createPubsubConfig,
  updatePubsubConfig,
  deletePubsubConfig,
  testPubsubConnection,
} from '@/tenant/api/resourceConfig'
import type {
  ResourceConfig,
  DatabaseConfig,
  StorageConfig,
  CacheConfig,
  QueueConfig,
  PubsubConfig,
  ResourceCreate,
  ResourceUpdate,
} from '@/tenant/types/resource'
import { notifySuccess, notifyError } from '@/framework/utils/feedback'
import { Button, Input, Label, Card, Badge, DataTable, useDataTable } from '@/components'
import { ResourceConfigRowActions } from '@/tenant/components'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components'
import { Plus, RefreshCw, Search, Layers, CheckCircle, Ban } from '@lucide/vue'

// 资源类型定义
type ResourceType = 'database' | 'storage' | 'cache' | 'queue' | 'pubsub'

const resourceTypes: { label: string; value: ResourceType }[] = [
  { label: '数据库', value: 'database' },
  { label: '存储', value: 'storage' },
  { label: '缓存', value: 'cache' },
  { label: '队列', value: 'queue' },
  { label: '发布订阅', value: 'pubsub' },
]

// 当前选中的资源类型
const currentType = ref<ResourceType>('database')

// 搜索关键字
const keyword = ref('')

// 弹窗状态
const dialogOpen = ref(false)
const deleteDialogOpen = ref(false)
const editingId = ref<string | null>(null)
const deletingId = ref<string | null>(null)
const testingId = ref<string | null>(null)
const formLoading = ref(false)
const testLoading = ref(false)

// 表单数据
const form = ref({
  name: '',
  config: {} as Record<string, any>,
})

// 数据库配置表单默认值
const databaseFormDefault = {
  host: '',
  port: 5432,
  database: '',
  username: '',
  password: '',
  ssl_mode: 'disable',
}

// 存储配置表单默认值
const storageFormDefault = {
  endpoint: '',
  bucket: '',
  access_key: '',
  secret_key: '',
  region: '',
}

// 缓存配置表单默认值
const cacheFormDefault = {
  host: '',
  port: 6379,
  password: '',
  db: 0,
}

// 队列配置表单默认值
const queueFormDefault = {
  host: '',
  port: 5672,
  username: '',
  password: '',
  vhost: '/',
}

// 发布订阅配置表单默认值
const pubsubFormDefault = {
  type: 'kafka' as 'kafka' | 'rabbitmq' | 'redis',
  brokers: '',
  host: '',
  port: 9092,
  username: '',
  password: '',
}

// 根据类型获取默认表单配置
const getDefaultConfig = (type: ResourceType): Record<string, any> => {
  switch (type) {
    case 'database':
      return { ...databaseFormDefault }
    case 'storage':
      return { ...storageFormDefault }
    case 'cache':
      return { ...cacheFormDefault }
    case 'queue':
      return { ...queueFormDefault }
    case 'pubsub':
      return { ...pubsubFormDefault }
    default:
      return {}
  }
}

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString()
}

// 获取状态徽章
const getStatusBadge = (row: ResourceConfig) => {
  if ((row.tenant_count || 0) > 0) {
    return { label: '已引用', variant: 'default' as const }
  }
  return { label: '未使用', variant: 'secondary' as const }
}

// ==================== 测试连接 ====================
const handleTestConnection = async (row: ResourceConfig, type: ResourceType) => {
  testingId.value = row.id
  testLoading.value = true
  try {
    let response
    switch (type) {
      case 'database':
        response = await testDatabaseConnection(row.id)
        break
      case 'storage':
        response = await testStorageConnection(row.id)
        break
      case 'cache':
        response = await testCacheConnection(row.id)
        break
      case 'queue':
        response = await testQueueConnection(row.id)
        break
      case 'pubsub':
        response = await testPubsubConnection(row.id)
        break
    }

    if (response?.data?.success) {
      notifySuccess(`连接成功，延迟 ${response.data.latency}ms`)
    } else {
      notifyError(response?.data?.error || '连接失败')
    }
  } catch (error) {
    console.error('测试连接失败:', error)
    notifyError('测试连接失败')
  } finally {
    testingId.value = null
    testLoading.value = false
  }
}

// ==================== 列定义 ====================

// 数据库列定义
const databaseColumns: ColumnDef<DatabaseConfig>[] = [
  { accessorKey: 'name', header: '配置名称', size: 200, cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name) },
  { accessorKey: 'host', header: '主机地址', size: 120 },
  { accessorKey: 'port', header: '端口', size: 80 },
  { accessorKey: 'database', header: '数据库名', size: 120 },
  {
    accessorKey: 'tenant_count',
    header: '状态',
    size: 80,
    cell: ({ row }) => h(Badge, { variant: getStatusBadge(row.original).variant }, () => getStatusBadge(row.original).label),
  },
  { accessorKey: 'tenant_count', header: '引用租户', size: 80, cell: ({ row }) => row.original.tenant_count || 0 },
  { accessorKey: 'created_at', header: '创建时间', size: 120, cell: ({ row }) => formatDate(row.original.created_at) },
  {
    id: 'actions',
    header: '操作',
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      return h(ResourceConfigRowActions, {
        row: item,
        resourceType: 'database',
        isTesting: testingId.value === item.id && testLoading.value,
        onTest: handleTestConnection,
        onEdit: openEditDialog,
        onDelete: openDeleteDialog,
      })
    },
  },
]

// 存储列定义
const storageColumns: ColumnDef<StorageConfig>[] = [
  { accessorKey: 'name', header: '配置名称', size: 130, cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name) },
  { accessorKey: 'endpoint', header: 'Endpoint', size: 180 },
  { accessorKey: 'bucket', header: 'Bucket', size: 100 },
  { accessorKey: 'region', header: 'Region', size: 80, cell: ({ row }) => row.original.region || '--' },
  {
    accessorKey: 'tenant_count',
    header: '状态',
    size: 80,
    cell: ({ row }) => h(Badge, { variant: getStatusBadge(row.original).variant }, () => getStatusBadge(row.original).label),
  },
  { accessorKey: 'tenant_count', header: '引用租户', size: 80, cell: ({ row }) => row.original.tenant_count || 0 },
  { accessorKey: 'created_at', header: '创建时间', size: 120, cell: ({ row }) => formatDate(row.original.created_at) },
  {
    id: 'actions',
    header: '操作',
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      return h(ResourceConfigRowActions, {
        row: item,
        resourceType: 'storage',
        isTesting: testingId.value === item.id && testLoading.value,
        onTest: handleTestConnection,
        onEdit: openEditDialog,
        onDelete: openDeleteDialog,
      })
    },
  },
]

// 缓存列定义
const cacheColumns: ColumnDef<CacheConfig>[] = [
  { accessorKey: 'name', header: '配置名称', size: 130, cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name) },
  { accessorKey: 'host', header: '主机地址', size: 120 },
  { accessorKey: 'port', header: '端口', size: 80 },
  { accessorKey: 'db', header: '数据库', size: 80, cell: ({ row }) => row.original.db || 0 },
  {
    accessorKey: 'tenant_count',
    header: '状态',
    size: 80,
    cell: ({ row }) => h(Badge, { variant: getStatusBadge(row.original).variant }, () => getStatusBadge(row.original).label),
  },
  { accessorKey: 'tenant_count', header: '引用租户', size: 80, cell: ({ row }) => row.original.tenant_count || 0 },
  { accessorKey: 'created_at', header: '创建时间', size: 120, cell: ({ row }) => formatDate(row.original.created_at) },
  {
    id: 'actions',
    header: '操作',
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      return h(ResourceConfigRowActions, {
        row: item,
        resourceType: 'cache',
        isTesting: testingId.value === item.id && testLoading.value,
        onTest: handleTestConnection,
        onEdit: openEditDialog,
        onDelete: openDeleteDialog,
      })
    },
  },
]

// 队列列定义
const queueColumns: ColumnDef<QueueConfig>[] = [
  { accessorKey: 'name', header: '配置名称', size: 130, cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name) },
  { accessorKey: 'host', header: '主机地址', size: 150 },
  { accessorKey: 'port', header: '端口', size: 80 },
  { accessorKey: 'username', header: '用户名', size: 100, cell: ({ row }) => row.original.username || '--' },
  { accessorKey: 'vhost', header: 'VHost', size: 80, cell: ({ row }) => row.original.vhost || '/' },
  {
    accessorKey: 'tenant_count',
    header: '状态',
    size: 80,
    cell: ({ row }) => h(Badge, { variant: getStatusBadge(row.original).variant }, () => getStatusBadge(row.original).label),
  },
  { accessorKey: 'tenant_count', header: '引用租户', size: 80, cell: ({ row }) => row.original.tenant_count || 0 },
  {
    id: 'actions',
    header: '操作',
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      return h(ResourceConfigRowActions, {
        row: item,
        resourceType: 'queue',
        isTesting: testingId.value === item.id && testLoading.value,
        onTest: handleTestConnection,
        onEdit: openEditDialog,
        onDelete: openDeleteDialog,
      })
    },
  },
]

// 发布订阅列定义
const pubsubColumns: ColumnDef<PubsubConfig>[] = [
  { accessorKey: 'name', header: '配置名称', size: 130, cell: ({ row }) => h('span', { class: 'font-medium' }, row.original.name) },
  {
    accessorKey: 'type_name',
    header: '类型',
    size: 100,
    cell: ({ row }) => h(Badge, { variant: 'outline' }, () => row.original.type_name),
  },
  {
    id: 'address',
    header: '地址信息',
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      if (item.brokers?.length) {
        return item.brokers.join(', ')
      }
      if (item.host) {
        return `${item.host}:${item.port}`
      }
      return '--'
    },
  },
  { accessorKey: 'username', header: '用户名', size: 100, cell: ({ row }) => row.original.username || '--' },
  {
    accessorKey: 'tenant_count',
    header: '状态',
    size: 80,
    cell: ({ row }) => h(Badge, { variant: getStatusBadge(row.original).variant }, () => getStatusBadge(row.original).label),
  },
  { accessorKey: 'tenant_count', header: '引用租户', size: 80, cell: ({ row }) => row.original.tenant_count || 0 },
  { accessorKey: 'created_at', header: '创建时间', size: 120, cell: ({ row }) => formatDate(row.original.created_at) },
  {
    id: 'actions',
    header: '操作',
    size: 200,
    cell: ({ row }) => {
      const item = row.original
      return h(ResourceConfigRowActions, {
        row: item,
        resourceType: 'pubsub',
        isTesting: testingId.value === item.id && testLoading.value,
        onTest: handleTestConnection,
        onEdit: openEditDialog,
        onDelete: openDeleteDialog,
      })
    },
  },
]

// ==================== DataTable 实例 ====================

const databaseDataTable = useDataTable<DatabaseConfig>({
  columns: databaseColumns,
  enabled: () => currentType.value === 'database',
  remoteFetchFn: async ({ page, page_size }) => {
    return await getDatabaseConfigs({ page, page_size, keyword: keyword.value || undefined })
  },
})

const storageDataTable = useDataTable<StorageConfig>({
  columns: storageColumns,
  enabled: () => currentType.value === 'storage',
  remoteFetchFn: async ({ page, page_size }) => {
    return await getStorageConfigs({ page, page_size, keyword: keyword.value || undefined })
  },
})

const cacheDataTable = useDataTable<CacheConfig>({
  columns: cacheColumns,
  enabled: () => currentType.value === 'cache',
  remoteFetchFn: async ({ page, page_size }) => {
    return await getCacheConfigs({ page, page_size, keyword: keyword.value || undefined })
  },
})

const queueDataTable = useDataTable<QueueConfig>({
  columns: queueColumns,
  enabled: () => currentType.value === 'queue',
  remoteFetchFn: async ({ page, page_size }) => {
    return await getQueueConfigs({ page, page_size, keyword: keyword.value || undefined })
  },
})

const pubsubDataTable = useDataTable<PubsubConfig>({
  columns: pubsubColumns,
  enabled: () => currentType.value === 'pubsub',
  remoteFetchFn: async ({ page, page_size }) => {
    return await getPubsubConfigs({ page, page_size, keyword: keyword.value || undefined })
  },
})

// DataTable 实例映射
// 注意：由于 TypeScript 泛型的不变性，这里使用 any 类型
const dataTableMap: Record<ResourceType, ReturnType<typeof useDataTable<any>>> = {
  database: databaseDataTable,
  storage: storageDataTable,
  cache: cacheDataTable,
  queue: queueDataTable,
  pubsub: pubsubDataTable,
}

// 获取当前 DataTable 的数据列表（用于统计）
const currentDataList = computed<ResourceConfig[]>(() => {
  switch (currentType.value) {
    case 'database':
      return (databaseDataTable.table.getRowModel().rows || []).map(r => r.original)
    case 'storage':
      return (storageDataTable.table.getRowModel().rows || []).map(r => r.original)
    case 'cache':
      return (cacheDataTable.table.getRowModel().rows || []).map(r => r.original)
    case 'queue':
      return (queueDataTable.table.getRowModel().rows || []).map(r => r.original)
    case 'pubsub':
      return (pubsubDataTable.table.getRowModel().rows || []).map(r => r.original)
    default:
      return []
  }
})

// 统计数据
const stats = computed(() => {
  const dt = dataTableMap[currentType.value]
  const total = dt.table.getRowCount()
  const data = currentDataList.value
  const used = data.filter(item => (item.tenant_count || 0) > 0).length
  const unused = total - used
  return { total, used, unused }
})

// ==================== 搜索 ====================

// 全局搜索：刷新所有 DataTable（切换 Tab 时数据已预加载）
const handleSearch = () => {
  for (const dt of Object.values(dataTableMap)) {
    dt.refresh(true)
  }
}

// 刷新当前表格
const handleRefresh = () => {
  dataTableMap[currentType.value].refresh()
}

// ==================== 弹窗操作 ====================

// 打开新增弹窗
const openCreateDialog = () => {
  editingId.value = null
  form.value = {
    name: '',
    config: getDefaultConfig(currentType.value),
  }
  dialogOpen.value = true
}

// 打开编辑弹窗
const openEditDialog = (row: ResourceConfig) => {
  editingId.value = row.id
  form.value = {
    name: row.name,
    config: extractConfig(row),
  }
  dialogOpen.value = true
}

// 从扁平数据中提取 config 对象
const extractConfig = (row: ResourceConfig): Record<string, any> => {
  const { id, name, tenant_count, is_default, created_at, updated_at, type, ...config } = row as any
  return config
}

// 打开删除确认
const openDeleteDialog = (row: ResourceConfig) => {
  deletingId.value = row.id
  deleteDialogOpen.value = true
}

// 保存配置
const handleSave = async () => {
  // 验证配置名称
  if (!form.value.name.trim()) {
    notifyError('请输入配置名称')
    return
  }

  // 根据不同类型验证必填字段
  switch (currentType.value) {
    case 'database':
      if (!form.value.config.host?.trim()) {
        notifyError('请输入数据库主机')
        return
      }
      if (!form.value.config.port) {
        notifyError('请输入数据库端口')
        return
      }
      if (!form.value.config.database?.trim()) {
        notifyError('请输入数据库名称')
        return
      }
      if (!form.value.config.username?.trim()) {
        notifyError('请输入用户名')
        return
      }
      break
    case 'storage':
      if (!form.value.config.endpoint?.trim()) {
        notifyError('请输入存储端点')
        return
      }
      if (!form.value.config.bucket?.trim()) {
        notifyError('请输入 Bucket 名称')
        return
      }
      if (!form.value.config.access_key?.trim()) {
        notifyError('请输入 Access Key')
        return
      }
      break
    case 'cache':
      if (!form.value.config.host?.trim()) {
        notifyError('请输入缓存主机')
        return
      }
      if (!form.value.config.port) {
        notifyError('请输入缓存端口')
        return
      }
      break
    case 'queue':
      if (!form.value.config.host?.trim()) {
        notifyError('请输入队列主机')
        return
      }
      if (!form.value.config.port) {
        notifyError('请输入队列端口')
        return
      }
      break
    case 'pubsub':
      if (form.value.config.type === 'kafka') {
        if (!form.value.config.brokers || !form.value.config.brokers.trim()) {
          notifyError('请输入 Kafka Brokers')
          return
        }
      } else {
        if (!form.value.config.host?.trim()) {
          notifyError('请输入主机地址')
          return
        }
        if (!form.value.config.port) {
          notifyError('请输入端口')
          return
        }
      }
      break
  }

  formLoading.value = true
  try {
    // 构建扁平化的提交数据
    const payload: Record<string, any> = {
      name: form.value.name,
      ...form.value.config,
    }

    // 根据资源类型添加 type 字段
    const typeValues: Record<ResourceType, string | undefined> = {
      database: 'postgresql',
      storage: 'minio',
      cache: undefined,
      queue: 'rabbitmq',
      pubsub: 'kafka',
    }
    if (typeValues[currentType.value]) {
      payload.type = typeValues[currentType.value]
    }

    if (editingId.value) {
      const updatePayload = {
        name: form.value.name,
        ...form.value.config,
      }
      switch (currentType.value) {
        case 'database':
          await updateDatabaseConfig(editingId.value, updatePayload)
          break
        case 'storage':
          await updateStorageConfig(editingId.value, updatePayload)
          break
        case 'cache':
          await updateCacheConfig(editingId.value, updatePayload)
          break
        case 'queue':
          await updateQueueConfig(editingId.value, updatePayload)
          break
        case 'pubsub':
          await updatePubsubConfig(editingId.value, updatePayload)
          break
      }
      notifySuccess('配置已更新')
    } else {
      switch (currentType.value) {
        case 'database':
          await createDatabaseConfig(payload)
          break
        case 'storage':
          await createStorageConfig(payload)
          break
        case 'cache':
          await createCacheConfig(payload)
          break
        case 'queue':
          await createQueueConfig(payload)
          break
        case 'pubsub':
          await createPubsubConfig(payload)
          break
      }
      notifySuccess('配置已创建')
    }

    dialogOpen.value = false
    dataTableMap[currentType.value].refresh()
  } catch (error) {
    console.error('保存失败:', error)
    notifyError('保存失败')
  } finally {
    formLoading.value = false
  }
}

// 确认删除
const confirmDelete = async () => {
  if (!deletingId.value) return

  formLoading.value = true
  try {
    switch (currentType.value) {
      case 'database':
        await deleteDatabaseConfig(deletingId.value)
        break
      case 'storage':
        await deleteStorageConfig(deletingId.value)
        break
      case 'cache':
        await deleteCacheConfig(deletingId.value)
        break
      case 'queue':
        await deleteQueueConfig(deletingId.value)
        break
      case 'pubsub':
        await deletePubsubConfig(deletingId.value)
        break
    }

    notifySuccess('配置已删除')
    deleteDialogOpen.value = false
    dataTableMap[currentType.value].refresh()
  } catch (error: any) {
    console.error('删除失败:', error)
    // 解析错误信息
    const errorMessage = error?.response?.data?.msg || error?.message || '删除失败'

    // 针对性错误提示
    if (errorMessage.includes('已被') || errorMessage.includes('引用') || errorMessage.includes('关联')) {
      notifyError('该配置已被租户引用，无法删除。请先解除与租户的绑定关系')
    } else {
      notifyError(errorMessage)
    }
  } finally {
    formLoading.value = false
  }
}
</script>

<template>
  <div class="flex h-full min-h-0 flex-col gap-4 p-4">
    <!-- 页面标题区 -->
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div>
        <h2 class="text-xl font-semibold">资源配置管理</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理平台级资源连接配置，支持数据库、存储、缓存、队列和发布订阅服务。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Input
          v-model="keyword"
          data-testid="search-input"
          class="w-56"
          placeholder="搜索配置名称"
          @keydown.enter="handleSearch"
        />
        <Button variant="outline" data-testid="search-button" @click="handleSearch">
          <Search class="mr-1 h-4 w-4" />
          搜索
        </Button>
        <Button variant="outline" data-testid="refresh-button" @click="handleRefresh">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button data-testid="create-button" @click="openCreateDialog">
          <Plus class="mr-1 h-4 w-4" />
          新增配置
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">配置总数</p>
            <p class="text-2xl font-bold mt-1">{{ stats.total }}</p>
            <p class="text-xs text-muted-foreground mt-1">当前类型的资源配置数量</p>
          </div>
          <Layers class="h-8 w-8 opacity-20 text-blue-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">已被引用</p>
            <p class="text-2xl font-bold mt-1">{{ stats.used }}</p>
            <p class="text-xs text-muted-foreground mt-1">已被租户使用的配置数量</p>
          </div>
          <CheckCircle class="h-8 w-8 opacity-20 text-green-500" />
        </div>
      </div>
      <div class="border rounded-lg p-4 bg-card">
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm text-muted-foreground">未被使用</p>
            <p class="text-2xl font-bold mt-1">{{ stats.unused }}</p>
            <p class="text-xs text-muted-foreground mt-1">尚未分配给租户的配置</p>
          </div>
          <Ban class="h-8 w-8 opacity-20 text-gray-400" />
        </div>
      </div>
    </div>

    <!-- Tab 切换区 + 数据表格区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <Tabs v-model="currentType" class="flex h-full flex-col">
        <div class="border-b px-5 py-3">
          <TabsList>
            <TabsTrigger
              v-for="item in resourceTypes"
              :key="item.value"
              :value="item.value"
              :data-testid="`tab-${item.value}`"
            >
              {{ item.label }}
            </TabsTrigger>
          </TabsList>
        </div>

        <div class="min-h-0 flex-1 overflow-hidden px-5 py-4">
          <!-- 数据库表格 -->
          <TabsContent value="database" class="mt-0">
            <DataTable :data-table="databaseDataTable" :fixed-layout="true" />
          </TabsContent>

          <!-- 存储表格 -->
          <TabsContent value="storage" class="mt-0">
            <DataTable :data-table="storageDataTable" :fixed-layout="true" />
          </TabsContent>

          <!-- 缓存表格 -->
          <TabsContent value="cache" class="mt-0">
            <DataTable :data-table="cacheDataTable" :fixed-layout="true" />
          </TabsContent>

          <!-- 队列表格 -->
          <TabsContent value="queue" class="mt-0">
            <DataTable :data-table="queueDataTable" :fixed-layout="true" />
          </TabsContent>

          <!-- 发布订阅表格 -->
          <TabsContent value="pubsub" class="mt-0">
            <DataTable :data-table="pubsubDataTable" :fixed-layout="true" />
          </TabsContent>
        </div>
      </Tabs>
    </Card>

    <!-- 新增/编辑弹窗 -->
    <Dialog :open="dialogOpen" @update:open="dialogOpen = $event">
      <DialogContent class="sm:max-w-[600px]" data-testid="resource-dialog">
        <DialogHeader>
          <DialogTitle data-testid="dialog-title">{{ editingId ? '编辑配置' : '新增配置' }}</DialogTitle>
        </DialogHeader>

        <div class="grid gap-4 py-4">
          <!-- 基础信息 -->
          <div class="space-y-2">
            <Label>配置名称</Label>
            <Input v-model="form.name" data-testid="form-name" placeholder="请输入配置名称" />
          </div>

          <!-- 数据库配置 -->
          <template v-if="currentType === 'database'">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>主机地址</Label>
                <Input v-model="form.config.host" data-testid="form-host" placeholder="localhost" />
              </div>
              <div class="space-y-2">
                <Label>端口</Label>
                <Input v-model.number="form.config.port" data-testid="form-port" type="number" placeholder="5432" />
              </div>
            </div>
            <div class="space-y-2">
              <Label>数据库名</Label>
              <Input v-model="form.config.database" data-testid="form-database" placeholder="请输入数据库名" />
            </div>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>用户名</Label>
                <Input v-model="form.config.username" data-testid="form-username" placeholder="请输入用户名" />
              </div>
              <div class="space-y-2">
                <Label>密码</Label>
                <Input v-model="form.config.password" data-testid="form-password" type="password" placeholder="请输入密码" />
              </div>
            </div>
            <div class="space-y-2">
              <Label>SSL 模式</Label>
              <Select v-model="form.config.ssl_mode">
                <SelectTrigger>
                  <SelectValue placeholder="选择 SSL 模式" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="disable">禁用</SelectItem>
                  <SelectItem value="allow">允许</SelectItem>
                  <SelectItem value="prefer">优先</SelectItem>
                  <SelectItem value="require">要求</SelectItem>
                  <SelectItem value="verify-ca">验证 CA</SelectItem>
                  <SelectItem value="verify-full">完全验证</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </template>

          <!-- 存储配置 -->
          <template v-if="currentType === 'storage'">
            <div class="space-y-2">
              <Label>Endpoint</Label>
              <Input v-model="form.config.endpoint" placeholder="https://s3.amazonaws.com" />
            </div>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>Bucket</Label>
                <Input v-model="form.config.bucket" placeholder="请输入 Bucket 名称" />
              </div>
              <div class="space-y-2">
                <Label>Region</Label>
                <Input v-model="form.config.region" placeholder="us-east-1" />
              </div>
            </div>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>Access Key</Label>
                <Input v-model="form.config.access_key" placeholder="请输入 Access Key" />
              </div>
              <div class="space-y-2">
                <Label>Secret Key</Label>
                <Input v-model="form.config.secret_key" type="password" placeholder="请输入 Secret Key" />
              </div>
            </div>
          </template>

          <!-- 缓存配置 -->
          <template v-if="currentType === 'cache'">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>主机地址</Label>
                <Input v-model="form.config.host" placeholder="localhost" />
              </div>
              <div class="space-y-2">
                <Label>端口</Label>
                <Input v-model.number="form.config.port" type="number" placeholder="6379" />
              </div>
            </div>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>密码</Label>
                <Input v-model="form.config.password" type="password" placeholder="请输入密码（可选）" />
              </div>
              <div class="space-y-2">
                <Label>数据库</Label>
                <Input v-model.number="form.config.db" type="number" placeholder="0" />
              </div>
            </div>
          </template>

          <!-- 队列配置 -->
          <template v-if="currentType === 'queue'">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>主机地址</Label>
                <Input v-model="form.config.host" placeholder="localhost" />
              </div>
              <div class="space-y-2">
                <Label>端口</Label>
                <Input v-model.number="form.config.port" type="number" placeholder="5672" />
              </div>
            </div>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>用户名</Label>
                <Input v-model="form.config.username" placeholder="请输入用户名" />
              </div>
              <div class="space-y-2">
                <Label>密码</Label>
                <Input v-model="form.config.password" type="password" placeholder="请输入密码" />
              </div>
            </div>
            <div class="space-y-2">
              <Label>VHost</Label>
              <Input v-model="form.config.vhost" placeholder="/" />
            </div>
          </template>

          <!-- 发布订阅配置 -->
          <template v-if="currentType === 'pubsub'">
            <div class="space-y-2">
              <Label>类型</Label>
              <Select v-model="form.config.type">
                <SelectTrigger>
                  <SelectValue placeholder="选择类型" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="kafka">Kafka</SelectItem>
                  <SelectItem value="rabbitmq">RabbitMQ</SelectItem>
                  <SelectItem value="redis">Redis</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div v-if="form.config.type === 'kafka'" class="space-y-2">
              <Label>Brokers（逗号分隔）</Label>
              <Input v-model="form.config.brokers" placeholder="localhost:9092,localhost:9093" />
            </div>
            <template v-else>
              <div class="grid gap-4 md:grid-cols-2">
                <div class="space-y-2">
                  <Label>主机地址</Label>
                  <Input v-model="form.config.host" placeholder="localhost" />
                </div>
                <div class="space-y-2">
                  <Label>端口</Label>
                  <Input v-model.number="form.config.port" type="number" placeholder="5672" />
                </div>
              </div>
            </template>
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>用户名</Label>
                <Input v-model="form.config.username" placeholder="请输入用户名（可选）" />
              </div>
              <div class="space-y-2">
                <Label>密码</Label>
                <Input v-model="form.config.password" type="password" placeholder="请输入密码（可选）" />
              </div>
            </div>
          </template>
        </div>

        <DialogFooter>
          <Button variant="outline" data-testid="cancel-button" @click="dialogOpen = false">取消</Button>
          <Button data-testid="save-button" :disabled="formLoading" @click="handleSave">
            {{ formLoading ? '保存中...' : '保存' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除确认弹窗 -->
    <Dialog :open="deleteDialogOpen" @update:open="deleteDialogOpen = $event">
      <DialogContent class="sm:max-w-[400px]" data-testid="delete-dialog">
        <DialogHeader>
          <DialogTitle data-testid="delete-dialog-title">确认删除</DialogTitle>
        </DialogHeader>
        <p class="py-4 text-muted-foreground">
          确定要删除此配置吗？如果配置已被租户引用，删除后相关租户将无法正常使用该资源。
        </p>
        <DialogFooter>
          <Button variant="outline" data-testid="delete-cancel-button" @click="deleteDialogOpen = false">取消</Button>
          <Button
            variant="destructive"
            data-testid="delete-confirm-button"
            :disabled="formLoading"
            @click="confirmDelete"
          >
            {{ formLoading ? '删除中...' : '确认删除' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>
