<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useRoleStore } from '@/iam/stores/role'
import { useUserStore } from '@/framework/stores'
import type { Role } from '@/iam/types'
import { confirmAction, notifyError } from '@/framework/utils/feedback'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Button, Badge, Skeleton, Pagination } from '@/components'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Plus, Pencil, Trash2, Shield } from '@lucide/vue'
import PermissionAssignDialog from '@/iam/components/PermissionAssignDialog.vue'

const router = useRouter()
const roleStore = useRoleStore()
const frameworkUserStore = useUserStore()

const pagination = ref({
  page: 1,
  pageSize: 20,
})

const loadRoles = async () => {
  await roleStore.fetchRoles({
    page: pagination.value.page,
    page_size: pagination.value.pageSize,
  })
}

const handlePageChange = (page: number) => {
  pagination.value.page = page
  loadRoles()
}

const handlePageSizeChange = (pageSize: number) => {
  pagination.value.pageSize = pageSize
  pagination.value.page = 1
  loadRoles()
}

const handleCreate = () => {
  router.push('/roles/create')
}

const handleEdit = (row: Role) => {
  router.push(`/roles/${row.id}`)
}

const handleDelete = async (row: Role) => {
  if (row.is_system) {
    notifyError('系统内置角色无法删除')
    return
  }
  if (!confirmAction(`确定要删除角色 "${row.name}" 吗？`)) return
  await roleStore.removeRole(row.id)
}

const assignRole = ref<Role | null>(null)
const assignDialogOpen = ref(false)

const handleAssignPermission = (row: Role) => {
  assignRole.value = row
  assignDialogOpen.value = true
}

const handleAssignSaved = () => {
  loadRoles()
}

const canCreate = computed(() => frameworkUserStore.hasPermission('role:add'))
const canEdit = computed(() => frameworkUserStore.hasPermission('role:edit'))
const canDelete = computed(() => frameworkUserStore.hasPermission('role:delete'))
const canAssign = computed(() => frameworkUserStore.hasPermission('role:edit'))

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

onMounted(() => {
  loadRoles()
})
</script>

<template>
  <AppPage title="角色列表" variant="list">
    <template #actions>
      <Button v-if="canCreate" @click="handleCreate">
        <Plus class="mr-1 h-4 w-4" />
        新建角色
      </Button>
    </template>

    <div class="rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-[120px]">角色编码</TableHead>
            <TableHead class="w-[120px]">角色名称</TableHead>
            <TableHead class="w-[200px]">描述</TableHead>
            <TableHead class="w-[100px]">系统角色</TableHead>
            <TableHead class="w-[180px]">创建时间</TableHead>
            <TableHead class="w-[150px]">操作</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-if="roleStore.loading">
            <TableCell v-for="n in 6" :key="n">
              <Skeleton class="h-5 w-full" />
            </TableCell>
          </TableRow>
          <TableRow v-else-if="!roleStore.roles?.length">
            <TableCell colspan="6" class="h-24 text-center text-muted-foreground">
              暂无数据
            </TableCell>
          </TableRow>
          <TableRow v-else v-for="row in roleStore.roles" :key="row.id">
            <TableCell class="font-medium">{{ row.code }}</TableCell>
            <TableCell>{{ row.name }}</TableCell>
            <TableCell>{{ row.description || '--' }}</TableCell>
            <TableCell>
              <Badge :variant="row.is_system ? 'default' : 'secondary'">
                {{ row.is_system ? '是' : '否' }}
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
                  v-if="canAssign"
                  variant="ghost"
                  size="sm"
                  @click="handleAssignPermission(row)"
                >
                  <Shield class="mr-1 h-3.5 w-3.5" />
                  分配权限
                </Button>
                <Button
                  v-if="canDelete && !row.is_system"
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
      :total="roleStore.total"
      :page="pagination.page"
      :page-size="pagination.pageSize"
      @update:page="handlePageChange"
      @update:page-size="handlePageSizeChange"
    />
  </AppPage>

  <PermissionAssignDialog
    :role="assignRole"
    v-model:open="assignDialogOpen"
    @saved="handleAssignSaved"
  />
</template>