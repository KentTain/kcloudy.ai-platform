<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/iam/stores/user'
import { useUserStore as useFrameworkUserStore } from '@/framework/stores'
import type { User } from '@/iam/types'
import { confirmAction } from '@/framework/utils/feedback'
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
import { Plus, Search, RotateCcw, Pencil, Trash2, Lock, ShieldOff, ShieldCheck } from '@lucide/vue'

const router = useRouter()
const userStore = useUserStore()
const frameworkUserStore = useFrameworkUserStore()

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
  { label: '锁定', value: 'locked' },
]

const allStatusOptions = [
  { label: '全部', value: 'all' },
  ...statusOptions,
]

const handleSearch = () => {
  pagination.value.page = 1
  loadUsers()
}

const handleReset = () => {
  searchForm.value = { keyword: '', status: '' }
  pagination.value.page = 1
  loadUsers()
}

const loadUsers = async () => {
  await userStore.fetchUsers({
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
    keyword: searchForm.value.keyword || undefined,
    status: searchForm.value.status || undefined,
  })
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadUsers()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadUsers()
}

const handleCreate = () => {
  router.push('/users/create')
}

const handleEdit = (row: User) => {
  router.push(`/users/${row.id}/edit`)
}

const handleDelete = async (row: User) => {
  if (!confirmAction(`确定要删除用户 "${row.username}" 吗？`)) return
  await userStore.removeUser(row.id)
}

const handleStatusChange = async (row: User, status: 'enable' | 'disable' | 'lock') => {
  await userStore.changeUserStatus(row.id, status)
}

const canCreate = computed(() => frameworkUserStore.hasPermission('user:add'))
const canEdit = computed(() => frameworkUserStore.hasPermission('user:edit'))
const canDelete = computed(() => frameworkUserStore.hasPermission('user:delete'))

function getStatusBadgeVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (status === 'active') return 'default'
  if (status === 'locked') return 'destructive'
  return 'secondary'
}

function getStatusLabel(status: string): string {
  if (status === 'active') return '激活'
  if (status === 'locked') return '锁定'
  return '停用'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  loadUsers()
})
</script>

<template>
  <AppPage title="用户管理" variant="list">
    <template #actions>
      <Button v-if="canCreate" @click="handleCreate">
        <Plus class="mr-1 h-4 w-4" />
        新建用户
      </Button>
    </template>

    <!-- 搜索筛选区 -->
    <div class="flex flex-wrap items-end gap-3">
      <div class="flex flex-col gap-1.5">
        <span class="text-sm text-muted-foreground">关键字</span>
        <Input
          v-model="searchForm.keyword"
          placeholder="用户名/邮箱/手机号"
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
            
            <SelectItem v-for="opt in allStatusOptions" :key="opt.value" :value="opt.value">
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
            <TableHead class="w-[120px]">用户名</TableHead>
            <TableHead class="w-[100px]">昵称</TableHead>
            <TableHead class="w-[150px]">邮箱</TableHead>
            <TableHead class="w-[120px]">手机号</TableHead>
            <TableHead class="w-[80px]">状态</TableHead>
            <TableHead class="w-[180px]">创建时间</TableHead>
            <TableHead class="w-[200px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <!-- 加载态 Skeleton -->
          <TableRow v-if="userStore.loading">
            <TableCell v-for="n in 7" :key="n">
              <Skeleton class="h-5 w-full" />
            </TableCell>
          </TableRow>
          <!-- 空数据 -->
          <TableRow v-else-if="!userStore.users.length">
            <TableCell colspan="7" class="h-24 text-center text-muted-foreground">
              暂无数据
            </TableCell>
          </TableRow>
          <!-- 数据行 -->
          <TableRow v-else v-for="row in userStore.users" :key="row.id">
            <TableCell class="font-medium">{{ row.username }}</TableCell>
            <TableCell>{{ row.nickname || '--' }}</TableCell>
            <TableCell>{{ row.email || '--' }}</TableCell>
            <TableCell>{{ row.phone || '--' }}</TableCell>
            <TableCell>
              <Badge :variant="getStatusBadgeVariant(row.status)">
                {{ getStatusLabel(row.status) }}
              </Badge>
            </TableCell>
            <TableCell>{{ formatDate(row.created_at) }}</TableCell>
            <TableCell>
              <div class="flex items-center gap-1">
                <Button v-if="canEdit" variant="ghost" size="sm" @click="handleEdit(row)">
                  <Pencil class="mr-1 h-3.5 w-3.5" />
                  编辑
                </Button>
                <Button
                  v-if="canEdit && row.status === 'active'"
                  variant="ghost"
                  size="sm"
                  @click="handleStatusChange(row, 'disable')"
                >
                  <ShieldOff class="mr-1 h-3.5 w-3.5" />
                  停用
                </Button>
                <Button
                  v-if="canEdit && row.status === 'inactive'"
                  variant="ghost"
                  size="sm"
                  @click="handleStatusChange(row, 'enable')"
                >
                  <ShieldCheck class="mr-1 h-3.5 w-3.5" />
                  激活
                </Button>
                <Button
                  v-if="canEdit && row.status !== 'locked'"
                  variant="ghost"
                  size="sm"
                  class="text-destructive hover:text-destructive"
                  @click="handleStatusChange(row, 'lock')"
                >
                  <Lock class="mr-1 h-3.5 w-3.5" />
                  锁定
                </Button>
                <Button
                  v-if="canDelete"
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

    <!-- 分页 -->
    <Pagination
      :total="userStore.total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </AppPage>
</template>