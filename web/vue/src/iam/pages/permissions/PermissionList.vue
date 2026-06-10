<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { usePermissionStore } from '@/iam/stores/permission'
import AppPage from '@/framework/layouts/components/AppPage.vue'
import { Badge, Input } from '@/components'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Search } from '@lucide/vue'

const permissionStore = usePermissionStore()

// 搜索关键字
const searchKeyword = ref('')

// 加载所有权限
const loadPermissions = async () => {
  await permissionStore.fetchAllPermissions()
}

// 筛选后的权限列表
const filteredPermissions = computed(() => {
  if (!searchKeyword.value.trim()) {
    return permissionStore.permissions
  }
  const keyword = searchKeyword.value.toLowerCase()
  return permissionStore.permissions.filter(p =>
    p.name.toLowerCase().includes(keyword) ||
    p.code.toLowerCase().includes(keyword) ||
    p.resource.toLowerCase().includes(keyword)
  )
})

// 操作类型标签颜色
const getActionBadgeVariant = (action: string) => {
  switch (action) {
    case 'read':
      return 'default'
    case 'write':
      return 'secondary'
    case 'delete':
      return 'destructive'
    default:
      return 'outline'
  }
}

// 统计信息文本
const statsText = computed(() => {
  const total = permissionStore.permissions.length
  const filtered = filteredPermissions.value.length

  if (searchKeyword.value.trim()) {
    return `共 ${total} 项权限，筛选结果 ${filtered} 项`
  }
  return `共 ${total} 项权限`
})

onMounted(() => {
  loadPermissions()
})
</script>

<template>
  <AppPage title="权限管理" variant="list">
    <div class="flex h-full flex-col gap-4">
      <!-- 工具栏 -->
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div class="relative w-full sm:w-64">
          <Search class="text-muted-foreground absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" />
          <Input
            v-model="searchKeyword"
            placeholder="搜索名称/编码/资源"
            class="pl-9"
          />
        </div>
      </div>

      <!-- 权限列表 -->
      <div class="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead class="w-[150px]">权限名称</TableHead>
              <TableHead class="w-[200px]">权限编码</TableHead>
              <TableHead class="w-[120px]">资源</TableHead>
              <TableHead class="w-[100px]">操作类型</TableHead>
              <TableHead>说明</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <!-- 空状态 -->
            <TableRow v-if="filteredPermissions.length === 0">
              <TableCell colspan="5" class="text-muted-foreground text-center">
                {{ searchKeyword.trim() ? '未找到匹配的权限' : '暂无权限数据' }}
              </TableCell>
            </TableRow>
            <!-- 权限列表 -->
            <TableRow v-for="permission in filteredPermissions" :key="permission.id">
              <TableCell class="font-medium">{{ permission.name }}</TableCell>
              <TableCell class="font-mono text-sm">{{ permission.code }}</TableCell>
              <TableCell>{{ permission.resource }}</TableCell>
              <TableCell>
                <Badge :variant="getActionBadgeVariant(permission.action)">
                  {{ permission.action }}
                </Badge>
              </TableCell>
              <TableCell>{{ permission.description || '--' }}</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </div>

      <!-- 统计信息 -->
      <div class="text-muted-foreground text-sm">
        {{ statsText }}
      </div>
    </div>
  </AppPage>
</template>
