<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTenantStore } from '@/tenant/stores/tenant'
import { useUserStore } from '@/framework/stores'
import type { Tenant } from '@/tenant/types'
import { confirmAction, notifySuccess } from '@/framework/utils/feedback'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Input, Badge, Skeleton, Pagination } from '@/components'
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
import { Card } from '@/components/ui/card'
import { Plus, Search, RotateCcw, Pencil, Trash2, ShieldCheck, ShieldOff, Building2, UserX, Clock } from '@lucide/vue'

const router = useRouter()
const tenantStore = useTenantStore()
const frameworkUserStore = useUserStore()

const searchForm = ref({
  keyword: '',
  status: '',
})

const pagination = ref({
  page: 1,
  pageSize: 20,
})

const statusOptions = [
  { label: '激活', value: 'active' },
  { label: '停用', value: 'inactive' },
]

const loadTenants = async () => {
  await tenantStore.fetchTenants({
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    keyword: searchForm.value.keyword || undefined,
    status: searchForm.value.status === 'all' ? undefined : searchForm.value.status || undefined,
  })
}

const handleSearch = () => {
  pagination.value.page = 1
  loadTenants()
}

const handleReset = () => {
  searchForm.value = { keyword: '', status: '' }
  pagination.value.page = 1
  loadTenants()
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadTenants()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadTenants()
}

const handleCreate = () => {
  router.push('/tenants/create')
}

const handleEdit = (row: Tenant) => {
  router.push(`/tenants/${row.id}/edit`)
}

const handleDetail = (row: Tenant) => {
  router.push(`/tenants/${row.id}`)
}

const handleDelete = async (row: Tenant) => {
  if (!confirmAction(`确定要删除租户 "${row.name}" 吗？`)) return
  await tenantStore.removeTenant(row.id)
  notifySuccess('删除成功')
}

const handleActivate = async (row: Tenant) => {
  await tenantStore.activate(row.id)
  notifySuccess('激活成功')
}

const handleDeactivate = async (row: Tenant) => {
  await tenantStore.deactivate(row.id)
  notifySuccess('停用成功')
}

const canCreate = computed(() => frameworkUserStore.hasRole('admin'))
const canEdit = computed(() => frameworkUserStore.hasRole('admin'))

function formatDate(dateStr?: string): string {
  if (!dateStr) return '永久'
  return new Date(dateStr).toLocaleDateString()
}

onMounted(() => {
  loadTenants()
})
</script>

<template>
  <AppPage title="租户管理" variant="list">
    <template #actions>
      <Button v-if="canCreate" @click="handleCreate">
        <Plus class="mr-1 h-4 w-4" />
        新建租户
      </Button>
    </template>

    <!-- 统计卡片区 -->
    <div class="grid gap-4 md:grid-cols-3">
      <template v-if="tenantStore.loading">
        <Card class="gap-2 px-5 py-4">
          <Skeleton class="h-4 w-20" />
          <Skeleton class="h-8 w-16" />
          <Skeleton class="h-3 w-32" />
        </Card>
        <Card class="gap-2 px-5 py-4">
          <Skeleton class="h-4 w-20" />
          <Skeleton class="h-8 w-16" />
          <Skeleton class="h-3 w-32" />
        </Card>
        <Card class="gap-2 px-5 py-4">
          <Skeleton class="h-4 w-20" />
          <Skeleton class="h-8 w-16" />
          <Skeleton class="h-3 w-32" />
        </Card>
      </template>
      <template v-else>
        <Card class="gap-2 px-5 py-4">
          <div class="flex items-center gap-2">
            <Building2 class="text-muted-foreground h-4 w-4" />
            <span class="text-muted-foreground text-sm">租户总数</span>
          </div>
          <div class="text-2xl font-semibold">{{ tenantStore.stats.total_count }}</div>
          <div class="text-muted-foreground text-xs">系统中的租户总数</div>
        </Card>
        <Card class="gap-2 px-5 py-4">
          <div class="flex items-center gap-2">
            <UserX class="text-muted-foreground h-4 w-4" />
            <span class="text-muted-foreground text-sm">未激活数</span>
          </div>
          <div class="text-2xl font-semibold">{{ tenantStore.stats.inactive_count }}</div>
          <div class="text-muted-foreground text-xs">状态为停用的租户数量</div>
        </Card>
        <Card class="gap-2 px-5 py-4">
          <div class="flex items-center gap-2">
            <Clock class="text-muted-foreground h-4 w-4" />
            <span class="text-muted-foreground text-sm">过期数</span>
          </div>
          <div class="text-2xl font-semibold">{{ tenantStore.stats.expired_count }}</div>
          <div class="text-muted-foreground text-xs">已过期的租户数量</div>
        </Card>
      </template>
    </div>

    <!-- 搜索筛选区 -->
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex flex-col gap-1.5">
        <span class="text-sm text-muted-foreground">关键字</span>
        <Input
          v-model="searchForm.keyword"
          placeholder="租户名称/编码"
          class="w-[200px]"
          @keyup.enter="handleSearch"
        />
      </div>
      <div class="flex flex-col gap-1.5">
        <span class="text-sm text-muted-foreground">状态</span>
        <Select v-model="searchForm.status">
          <SelectTrigger class="w-[120px]">
            <SelectValue placeholder="全部" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部</SelectItem>
            <SelectItem v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </SelectItem>
          </SelectContent>
        </Select>
      </div>
      <div class="flex gap-2">
        <Button size="sm" @click="handleSearch">
          <Search class="mr-1 h-4 w-4" />
          搜索
        </Button>
        <Button variant="outline" size="sm" @click="handleReset">
          <RotateCcw class="mr-1 h-4 w-4" />
          重置
        </Button>
      </div>
    </div>

    <!-- 数据表格 -->
    <div class="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-[120px]">租户名称</TableHead>
            <TableHead class="w-[120px]">租户编码</TableHead>
            <TableHead class="w-[100px]">联系人</TableHead>
            <TableHead class="w-[150px]">联系人邮箱</TableHead>
            <TableHead class="w-[80px]">状态</TableHead>
            <TableHead class="w-[180px]">过期时间</TableHead>
            <TableHead class="w-[180px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-if="tenantStore.loading">
            <TableCell v-for="n in 7" :key="n">
              <Skeleton class="h-5 w-full" />
            </TableCell>
          </TableRow>
          <TableRow v-else-if="!tenantStore.tenants.length">
            <TableCell colspan="7" class="h-24 text-center text-muted-foreground">
              暂无数据
            </TableCell>
          </TableRow>
          <TableRow v-else v-for="row in tenantStore.tenants" :key="row.id">
            <TableCell class="font-medium">{{ row.name }}</TableCell>
            <TableCell>{{ row.code }}</TableCell>
            <TableCell>{{ row.contact_name || '--' }}</TableCell>
            <TableCell>{{ row.contact_email || '--' }}</TableCell>
            <TableCell>
              <Badge :variant="row.status === 'active' ? 'default' : 'secondary'">
                {{ row.status === 'active' ? '激活' : '停用' }}
              </Badge>
            </TableCell>
            <TableCell>{{ formatDate(row.expired_at) }}</TableCell>
            <TableCell>
              <div class="flex items-center gap-1">
                <Button v-if="canEdit" variant="ghost" size="sm" @click="handleDetail(row)">
                  详情
                </Button>
                <Button v-if="canEdit" variant="ghost" size="sm" @click="handleEdit(row)">
                  <Pencil class="mr-1 h-3.5 w-3.5" />
                  编辑
                </Button>
                <Button
                  v-if="canEdit && row.status === 'inactive'"
                  variant="ghost"
                  size="sm"
                  @click="handleActivate(row)"
                >
                  <ShieldCheck class="mr-1 h-3.5 w-3.5" />
                  激活
                </Button>
                <Button
                  v-if="canEdit && row.status === 'active'"
                  variant="ghost"
                  size="sm"
                  @click="handleDeactivate(row)"
                >
                  <ShieldOff class="mr-1 h-3.5 w-3.5" />
                  停用
                </Button>
                <Button
                  v-if="canEdit"
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

    <Pagination
      :total="tenantStore.total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </AppPage>
</template>
