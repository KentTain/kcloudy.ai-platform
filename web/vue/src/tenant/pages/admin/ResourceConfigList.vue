<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
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
  CreateResourceConfigParams,
  UpdateResourceConfigParams,
} from '@/tenant/types/resource'
import { notifySuccess, notifyError } from '@/framework/utils/feedback'
import { Button, Input, Label, Card, Badge, Skeleton, Pagination } from '@/components'
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components'
import { Plus, Pencil, Trash2, Plug, RefreshCw } from '@lucide/vue'

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

// 数据列表
const dataList = ref<ResourceConfig[]>([])
const loading = ref(false)
const total = ref(0)

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
})

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

// 统计数据
const stats = computed(() => {
  const total = dataList.value.length
  const used = dataList.value.filter(item => (item.tenant_count || 0) > 0).length
  const unused = total - used
  return { total, used, unused }
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
    }

    let response
    switch (currentType.value) {
      case 'database':
        response = await getDatabaseConfigs(params)
        break
      case 'storage':
        response = await getStorageConfigs(params)
        break
      case 'cache':
        response = await getCacheConfigs(params)
        break
      case 'queue':
        response = await getQueueConfigs(params)
        break
      case 'pubsub':
        response = await getPubsubConfigs(params)
        break
    }

    if (response.data) {
      dataList.value = response.data.items || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    notifyError('加载数据失败')
  } finally {
    loading.value = false
  }
}

// 监听类型变化重新加载
watch(currentType, () => {
  pagination.value.page = 1
  loadData()
})

// 分页变化
const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadData()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadData()
}

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
    config: { ...row.config },
  }
  dialogOpen.value = true
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
    const payload: CreateResourceConfigParams = {
      name: form.value.name,
      config: form.value.config,
    }

    if (editingId.value) {
      const updatePayload: UpdateResourceConfigParams = {
        name: form.value.name,
        config: form.value.config,
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
    loadData()
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
    loadData()
  } catch (error: any) {
    console.error('删除失败:', error)
    // 解析错误信息
    const errorMessage = error?.response?.data?.message || error?.message || '删除失败'

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

// 测试连接
const handleTestConnection = async (row: ResourceConfig) => {
  testingId.value = row.id
  testLoading.value = true
  try {
    let response
    switch (currentType.value) {
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

onMounted(() => {
  loadData()
})
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
        <Button variant="outline" @click="loadData">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button @click="openCreateDialog">
          <Plus class="mr-1 h-4 w-4" />
          新增配置
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <Card class="gap-2 px-5 py-4">
        <div class="text-muted-foreground text-sm">配置总数</div>
        <div class="text-2xl font-semibold">{{ stats.total }}</div>
        <div class="text-muted-foreground text-xs">当前类型的资源配置数量</div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="text-muted-foreground text-sm">已被引用</div>
        <div class="text-2xl font-semibold">{{ stats.used }}</div>
        <div class="text-muted-foreground text-xs">已被租户使用的配置数量</div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="text-muted-foreground text-sm">未被使用</div>
        <div class="text-2xl font-semibold">{{ stats.unused }}</div>
        <div class="text-muted-foreground text-xs">尚未分配给租户的配置</div>
      </Card>
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
            >
              {{ item.label }}
            </TabsTrigger>
          </TabsList>
        </div>

        <div class="min-h-0 flex-1 overflow-auto px-5 py-4">
          <!-- 数据库表格 -->
          <TabsContent value="database" class="mt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-[200px]">配置名称</TableHead>
                  <TableHead class="w-[150px]">主机地址</TableHead>
                  <TableHead class="w-[80px]">端口</TableHead>
                  <TableHead class="w-[120px]">数据库名</TableHead>
                  <TableHead class="w-[80px]">状态</TableHead>
                  <TableHead class="w-[80px]">引用租户</TableHead>
                  <TableHead class="w-[160px]">创建时间</TableHead>
                  <TableHead class="w-[160px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading">
                  <TableCell v-for="n in 8" :key="n">
                    <Skeleton class="h-5 w-full" />
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="!dataList.length">
                  <TableCell colspan="8" class="h-24 text-center text-muted-foreground">
                    暂无数据库配置
                  </TableCell>
                </TableRow>
                <TableRow
                  v-else
                  v-for="row in dataList as DatabaseConfig[]"
                  :key="row.id"
                >
                  <TableCell class="font-medium">{{ row.name }}</TableCell>
                  <TableCell>{{ row.config.host }}</TableCell>
                  <TableCell>{{ row.config.port }}</TableCell>
                  <TableCell>{{ row.config.database }}</TableCell>
                  <TableCell>
                    <Badge :variant="getStatusBadge(row).variant">
                      {{ getStatusBadge(row).label }}
                    </Badge>
                  </TableCell>
                  <TableCell>{{ row.tenant_count || 0 }}</TableCell>
                  <TableCell>{{ formatDate(row.created_at) }}</TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        :disabled="testingId === row.id && testLoading"
                        @click="handleTestConnection(row)"
                      >
                        <Plug class="mr-1 h-3.5 w-3.5" />
                        测试
                      </Button>
                      <Button variant="ghost" size="sm" @click="openEditDialog(row)">
                        <Pencil class="mr-1 h-3.5 w-3.5" />
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        class="text-destructive hover:text-destructive"
                        @click="openDeleteDialog(row)"
                      >
                        <Trash2 class="mr-1 h-3.5 w-3.5" />
                        删除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TabsContent>

          <!-- 存储表格 -->
          <TabsContent value="storage" class="mt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-[200px]">配置名称</TableHead>
                  <TableHead class="w-[200px]">Endpoint</TableHead>
                  <TableHead class="w-[120px]">Bucket</TableHead>
                  <TableHead class="w-[100px]">Region</TableHead>
                  <TableHead class="w-[80px]">状态</TableHead>
                  <TableHead class="w-[80px]">引用租户</TableHead>
                  <TableHead class="w-[160px]">创建时间</TableHead>
                  <TableHead class="w-[160px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading">
                  <TableCell v-for="n in 8" :key="n">
                    <Skeleton class="h-5 w-full" />
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="!dataList.length">
                  <TableCell colspan="8" class="h-24 text-center text-muted-foreground">
                    暂无存储配置
                  </TableCell>
                </TableRow>
                <TableRow
                  v-else
                  v-for="row in dataList as StorageConfig[]"
                  :key="row.id"
                >
                  <TableCell class="font-medium">{{ row.name }}</TableCell>
                  <TableCell>{{ row.config.endpoint }}</TableCell>
                  <TableCell>{{ row.config.bucket }}</TableCell>
                  <TableCell>{{ row.config.region || '--' }}</TableCell>
                  <TableCell>
                    <Badge :variant="getStatusBadge(row).variant">
                      {{ getStatusBadge(row).label }}
                    </Badge>
                  </TableCell>
                  <TableCell>{{ row.tenant_count || 0 }}</TableCell>
                  <TableCell>{{ formatDate(row.created_at) }}</TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        :disabled="testingId === row.id && testLoading"
                        @click="handleTestConnection(row)"
                      >
                        <Plug class="mr-1 h-3.5 w-3.5" />
                        测试
                      </Button>
                      <Button variant="ghost" size="sm" @click="openEditDialog(row)">
                        <Pencil class="mr-1 h-3.5 w-3.5" />
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        class="text-destructive hover:text-destructive"
                        @click="openDeleteDialog(row)"
                      >
                        <Trash2 class="mr-1 h-3.5 w-3.5" />
                        删除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TabsContent>

          <!-- 缓存表格 -->
          <TabsContent value="cache" class="mt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-[200px]">配置名称</TableHead>
                  <TableHead class="w-[150px]">主机地址</TableHead>
                  <TableHead class="w-[80px]">端口</TableHead>
                  <TableHead class="w-[80px]">数据库</TableHead>
                  <TableHead class="w-[80px]">状态</TableHead>
                  <TableHead class="w-[80px]">引用租户</TableHead>
                  <TableHead class="w-[160px]">创建时间</TableHead>
                  <TableHead class="w-[160px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading">
                  <TableCell v-for="n in 8" :key="n">
                    <Skeleton class="h-5 w-full" />
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="!dataList.length">
                  <TableCell colspan="8" class="h-24 text-center text-muted-foreground">
                    暂无缓存配置
                  </TableCell>
                </TableRow>
                <TableRow
                  v-else
                  v-for="row in dataList as CacheConfig[]"
                  :key="row.id"
                >
                  <TableCell class="font-medium">{{ row.name }}</TableCell>
                  <TableCell>{{ row.config.host }}</TableCell>
                  <TableCell>{{ row.config.port }}</TableCell>
                  <TableCell>{{ row.config.db || 0 }}</TableCell>
                  <TableCell>
                    <Badge :variant="getStatusBadge(row).variant">
                      {{ getStatusBadge(row).label }}
                    </Badge>
                  </TableCell>
                  <TableCell>{{ row.tenant_count || 0 }}</TableCell>
                  <TableCell>{{ formatDate(row.created_at) }}</TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        :disabled="testingId === row.id && testLoading"
                        @click="handleTestConnection(row)"
                      >
                        <Plug class="mr-1 h-3.5 w-3.5" />
                        测试
                      </Button>
                      <Button variant="ghost" size="sm" @click="openEditDialog(row)">
                        <Pencil class="mr-1 h-3.5 w-3.5" />
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        class="text-destructive hover:text-destructive"
                        @click="openDeleteDialog(row)"
                      >
                        <Trash2 class="mr-1 h-3.5 w-3.5" />
                        删除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TabsContent>

          <!-- 队列表格 -->
          <TabsContent value="queue" class="mt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-[200px]">配置名称</TableHead>
                  <TableHead class="w-[150px]">主机地址</TableHead>
                  <TableHead class="w-[80px]">端口</TableHead>
                  <TableHead class="w-[100px]">用户名</TableHead>
                  <TableHead class="w-[80px]">VHost</TableHead>
                  <TableHead class="w-[80px]">状态</TableHead>
                  <TableHead class="w-[80px]">引用租户</TableHead>
                  <TableHead class="w-[160px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading">
                  <TableCell v-for="n in 8" :key="n">
                    <Skeleton class="h-5 w-full" />
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="!dataList.length">
                  <TableCell colspan="8" class="h-24 text-center text-muted-foreground">
                    暂无队列配置
                  </TableCell>
                </TableRow>
                <TableRow
                  v-else
                  v-for="row in dataList as QueueConfig[]"
                  :key="row.id"
                >
                  <TableCell class="font-medium">{{ row.name }}</TableCell>
                  <TableCell>{{ row.config.host }}</TableCell>
                  <TableCell>{{ row.config.port }}</TableCell>
                  <TableCell>{{ row.config.username || '--' }}</TableCell>
                  <TableCell>{{ row.config.vhost || '/' }}</TableCell>
                  <TableCell>
                    <Badge :variant="getStatusBadge(row).variant">
                      {{ getStatusBadge(row).label }}
                    </Badge>
                  </TableCell>
                  <TableCell>{{ row.tenant_count || 0 }}</TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        :disabled="testingId === row.id && testLoading"
                        @click="handleTestConnection(row)"
                      >
                        <Plug class="mr-1 h-3.5 w-3.5" />
                        测试
                      </Button>
                      <Button variant="ghost" size="sm" @click="openEditDialog(row)">
                        <Pencil class="mr-1 h-3.5 w-3.5" />
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        class="text-destructive hover:text-destructive"
                        @click="openDeleteDialog(row)"
                      >
                        <Trash2 class="mr-1 h-3.5 w-3.5" />
                        删除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TabsContent>

          <!-- 发布订阅表格 -->
          <TabsContent value="pubsub" class="mt-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead class="w-[200px]">配置名称</TableHead>
                  <TableHead class="w-[100px]">类型</TableHead>
                  <TableHead class="w-[200px]">地址信息</TableHead>
                  <TableHead class="w-[100px]">用户名</TableHead>
                  <TableHead class="w-[80px]">状态</TableHead>
                  <TableHead class="w-[80px]">引用租户</TableHead>
                  <TableHead class="w-[160px]">创建时间</TableHead>
                  <TableHead class="w-[160px]">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-if="loading">
                  <TableCell v-for="n in 8" :key="n">
                    <Skeleton class="h-5 w-full" />
                  </TableCell>
                </TableRow>
                <TableRow v-else-if="!dataList.length">
                  <TableCell colspan="8" class="h-24 text-center text-muted-foreground">
                    暂无发布订阅配置
                  </TableCell>
                </TableRow>
                <TableRow
                  v-else
                  v-for="row in dataList as PubsubConfig[]"
                  :key="row.id"
                >
                  <TableCell class="font-medium">{{ row.name }}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{{ row.config.type }}</Badge>
                  </TableCell>
                  <TableCell>
                    <span v-if="row.config.brokers?.length">
                      {{ row.config.brokers.join(', ') }}
                    </span>
                    <span v-else-if="row.config.host">
                      {{ row.config.host }}:{{ row.config.port }}
                    </span>
                    <span v-else>--</span>
                  </TableCell>
                  <TableCell>{{ row.config.username || '--' }}</TableCell>
                  <TableCell>
                    <Badge :variant="getStatusBadge(row).variant">
                      {{ getStatusBadge(row).label }}
                    </Badge>
                  </TableCell>
                  <TableCell>{{ row.tenant_count || 0 }}</TableCell>
                  <TableCell>{{ formatDate(row.created_at) }}</TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        :disabled="testingId === row.id && testLoading"
                        @click="handleTestConnection(row)"
                      >
                        <Plug class="mr-1 h-3.5 w-3.5" />
                        测试
                      </Button>
                      <Button variant="ghost" size="sm" @click="openEditDialog(row)">
                        <Pencil class="mr-1 h-3.5 w-3.5" />
                        编辑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        class="text-destructive hover:text-destructive"
                        @click="openDeleteDialog(row)"
                      >
                        <Trash2 class="mr-1 h-3.5 w-3.5" />
                        删除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TabsContent>
        </div>
      </Tabs>
    </Card>

    <!-- 分页 -->
    <Pagination
      :total="total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />

    <!-- 新增/编辑弹窗 -->
    <Dialog :open="dialogOpen" @update:open="dialogOpen = $event">
      <DialogContent class="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>{{ editingId ? '编辑配置' : '新增配置' }}</DialogTitle>
        </DialogHeader>

        <div class="grid gap-4 py-4">
          <!-- 基础信息 -->
          <div class="space-y-2">
            <Label>配置名称</Label>
            <Input v-model="form.name" placeholder="请输入配置名称" />
          </div>

          <!-- 数据库配置 -->
          <template v-if="currentType === 'database'">
            <div class="grid gap-4 md:grid-cols-2">
              <div class="space-y-2">
                <Label>主机地址</Label>
                <Input v-model="form.config.host" placeholder="localhost" />
              </div>
              <div class="space-y-2">
                <Label>端口</Label>
                <Input v-model.number="form.config.port" type="number" placeholder="5432" />
              </div>
            </div>
            <div class="space-y-2">
              <Label>数据库名</Label>
              <Input v-model="form.config.database" placeholder="请输入数据库名" />
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
          <Button variant="outline" @click="dialogOpen = false">取消</Button>
          <Button :disabled="formLoading" @click="handleSave">
            {{ formLoading ? '保存中...' : '保存' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <!-- 删除确认弹窗 -->
    <Dialog :open="deleteDialogOpen" @update:open="deleteDialogOpen = $event">
      <DialogContent class="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
        </DialogHeader>
        <p class="py-4 text-muted-foreground">
          确定要删除此配置吗？如果配置已被租户引用，删除后相关租户将无法正常使用该资源。
        </p>
        <DialogFooter>
          <Button variant="outline" @click="deleteDialogOpen = false">取消</Button>
          <Button
            variant="destructive"
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
