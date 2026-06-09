<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getModules, deleteModule } from '@/tenant/api/module'
import type { Module } from '@/tenant/types/admin'
import { notifySuccess, notifyError, confirmAction } from '@/framework/utils/feedback'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
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
import { Pagination } from '@/components/common'
import { Plus, Search, RotateCcw, Pencil, Trash2, Eye, RefreshCw, Package, CheckCircle, Star, Users } from '@lucide/vue'

const router = useRouter()

// 数据列表
const dataList = ref<Module[]>([])
const loading = ref(false)
const total = ref(0)

// 分页
const pagination = ref({
  page: 1,
  pageSize: 20,
})

// 搜索筛选
const searchForm = ref({
  keyword: '',
  is_active: '',
})

// 统计数据
const stats = computed(() => {
  const totalCount = dataList.value.length
  const activeCount = dataList.value.filter(item => item.is_active).length
  const needCount = dataList.value.filter(item => item.is_need).length
  const assignedCount = dataList.value.reduce((sum, item) => sum + (item.tenant_count || 0), 0)
  return { totalCount, activeCount, needCount, assignedCount }
})

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const response = await getModules({
      page: pagination.value.page,
      page_size: pagination.value.pageSize,
      keyword: searchForm.value.keyword || undefined,
      is_active: searchForm.value.is_active ? searchForm.value.is_active === 'true' : undefined,
    })

    if (response.data) {
      dataList.value = response.data.items || []
      total.value = response.data.total || 0
    }
  } catch (error) {
    console.error('加载模块列表失败:', error)
    notifyError('加载模块列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.value.page = 1
  loadData()
}

// 重置
const handleReset = () => {
  searchForm.value = { keyword: '', is_active: '' }
  pagination.value.page = 1
  loadData()
}

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

// 新增模块
const handleCreate = () => {
  router.push('/admin/modules/create')
}

// 查看详情
const handleDetail = (row: Module) => {
  router.push(`/admin/modules/${row.id}`)
}

// 编辑模块
const handleEdit = (row: Module) => {
  router.push(`/admin/modules/${row.id}/edit`)
}

// 删除模块
const handleDelete = async (row: Module) => {
  if (!await confirmAction(`确定要删除模块 "${row.name}" 吗？删除后不可恢复。`)) return

  try {
    await deleteModule(row.id)
    notifySuccess('模块已删除')
    loadData()
  } catch (error: any) {
    console.error('删除模块失败:', error)
    const errorMessage = error?.response?.data?.message || error?.message || '删除失败'
    notifyError(errorMessage)
  }
}

// 格式化日期
const formatDate = (dateStr?: string): string => {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleString()
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
        <h2 class="text-xl font-semibold">模块管理</h2>
        <p class="text-muted-foreground mt-1 text-sm">
          管理系统模块，包括模块信息、菜单、权限和角色配置。
        </p>
      </div>
      <div class="flex items-center gap-2">
        <Button variant="outline" @click="loadData">
          <RefreshCw class="mr-1 h-4 w-4" />
          刷新
        </Button>
        <Button @click="handleCreate">
          <Plus class="mr-1 h-4 w-4" />
          新增模块
        </Button>
      </div>
    </div>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Package class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">模块总数</span>
        </div>
        <div class="text-2xl font-semibold">{{ stats.totalCount }}</div>
        <div class="text-muted-foreground text-xs">已配置的系统模块数量</div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <CheckCircle class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">启用模块</span>
        </div>
        <div class="text-2xl font-semibold">{{ stats.activeCount }}</div>
        <div class="text-muted-foreground text-xs">当前启用状态的模块数量</div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Star class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">必须模块</span>
        </div>
        <div class="text-2xl font-semibold">{{ stats.needCount }}</div>
        <div class="text-muted-foreground text-xs">租户必须分配的模块数量</div>
      </Card>
      <Card class="gap-2 px-5 py-4">
        <div class="flex items-center gap-2">
          <Users class="text-muted-foreground h-4 w-4" />
          <span class="text-muted-foreground text-sm">已分配次数</span>
        </div>
        <div class="text-2xl font-semibold">{{ stats.assignedCount }}</div>
        <div class="text-muted-foreground text-xs">所有模块分配给租户的总次数</div>
      </Card>
    </div>

    <!-- 搜索筛选区 + 数据表格区 -->
    <Card class="flex min-h-0 flex-1 flex-col gap-0 overflow-hidden py-0">
      <div class="border-b px-5 py-4">
        <div class="flex flex-wrap items-center justify-between gap-3">
          <div>
            <div class="font-medium">模块列表</div>
            <div class="text-muted-foreground mt-1 text-xs">管理系统模块及其菜单、权限、角色配置</div>
          </div>
          <div class="flex flex-wrap items-center gap-2">
            <Input
              v-model="searchForm.keyword"
              class="w-56"
              placeholder="搜索模块名称或编码"
              @keydown.enter="handleSearch"
            />
            <Select v-model="searchForm.is_active">
              <SelectTrigger class="w-[130px]">
                <SelectValue placeholder="模块状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部状态</SelectItem>
                <SelectItem value="true">启用</SelectItem>
                <SelectItem value="false">停用</SelectItem>
              </SelectContent>
            </Select>
            <Button variant="outline" @click="handleSearch">
              <Search class="mr-1 h-4 w-4" />
              搜索
            </Button>
            <Button variant="outline" @click="handleReset">
              <RotateCcw class="mr-1 h-4 w-4" />
              重置
            </Button>
          </div>
        </div>
      </div>

      <div class="min-h-0 flex-1 overflow-auto px-5 py-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-[200px]">模块信息</TableHead>
              <TableHead class="w-[80px]">状态</TableHead>
              <TableHead class="w-[100px]">必须模块</TableHead>
              <TableHead class="w-[100px]">分配次数</TableHead>
              <TableHead class="w-[180px]">创建时间</TableHead>
              <TableHead class="w-[160px]">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow v-if="loading">
              <TableCell v-for="n in 6" :key="n">
                <Skeleton class="h-5 w-full" />
              </TableCell>
            </TableRow>
            <TableRow v-else-if="!dataList.length">
              <TableCell colspan="6" class="h-24 text-center text-muted-foreground">
                暂无模块数据
              </TableCell>
            </TableRow>
            <TableRow v-else v-for="row in dataList" :key="row.id">
              <TableCell>
                <div class="space-y-1">
                  <div class="font-medium">{{ row.name }}</div>
                  <div class="text-muted-foreground text-xs">{{ row.code }}</div>
                </div>
              </TableCell>
              <TableCell>
                <Badge :variant="row.is_active ? 'default' : 'secondary'">
                  {{ row.is_active ? '启用' : '停用' }}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge :variant="row.is_need ? 'default' : 'outline'">
                  {{ row.is_need ? '是' : '否' }}
                </Badge>
              </TableCell>
              <TableCell>{{ row.tenant_count || 0 }}</TableCell>
              <TableCell>{{ formatDate(row.created_at) }}</TableCell>
              <TableCell>
                <div class="flex items-center gap-1">
                  <Button variant="ghost" size="sm" @click="handleDetail(row)">
                    <Eye class="mr-1 h-3.5 w-3.5" />
                    详情
                  </Button>
                  <Button variant="ghost" size="sm" @click="handleEdit(row)">
                    <Pencil class="mr-1 h-3.5 w-3.5" />
                    编辑
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    class="text-destructive hover:text-destructive"
                    @click="handleDelete(row)"
                  >
                    <Trash2 class="mr-1 h-3.5 w-3.5" />
                    删除
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>
    </Card>

    <!-- 分页 -->
    <Pagination
      :total="total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </div>
</template>
