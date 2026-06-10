<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { usePermissionStore } from '@/iam/stores/permission'
import { useRoleStore } from '@/iam/stores/role'
import type { Permission, Role } from '@/iam/types'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'

const props = withDefaults(defineProps<{
  role: Role | null
  open: boolean
}>(), {
  role: null,
  open: false,
})

const emit = defineEmits<{
  'update:open': [value: boolean]
  saved: []
}>()

const permissionStore = usePermissionStore()
const roleStore = useRoleStore()

const selectedIds = ref<string[]>([])

// All permissions (flat list)
const allPermissions = computed(() => permissionStore.permissions)

// Group permissions by resource for display
const permissionGroups = computed(() => {
  const map = new Map<string, Permission[]>()
  for (const perm of allPermissions.value) {
    const list = map.get(perm.resource) || []
    list.push(perm)
    map.set(perm.resource, list)
  }
  return Array.from(map.entries()).map(([resource, permissions]) => ({
    resource,
    permissions,
  }))
})

const selectedCount = computed(() => selectedIds.value.length)
const totalCount = computed(() => allPermissions.value.length)

// When all permissions are selected, show "取消全选"; otherwise show "全选"
const selectAllButtonText = computed(() => {
  if (totalCount.value === 0) return '全选'
  return selectedCount.value === totalCount.value ? '取消全选' : '全选'
})

const toggleSelectAll = () => {
  if (selectedCount.value === totalCount.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = allPermissions.value.map(p => p.id)
  }
}

const togglePermission = (id: string) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx === -1) {
    selectedIds.value = [...selectedIds.value, id]
  } else {
    selectedIds.value = selectedIds.value.filter(i => i !== id)
  }
}

const isSelected = (id: string) => selectedIds.value.includes(id)

const getActionVariant = (action: string) => {
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

// Initialize when dialog opens
watch(() => props.open, async (val) => {
  if (val && props.role) {
    try {
      await Promise.all([
        permissionStore.fetchAllPermissions(),
        roleStore.fetchRolePermissions(props.role.id),
      ])
      selectedIds.value = roleStore.currentRolePermissions.map(p => p.id)
    } catch {
      selectedIds.value = []
    }
  }
})

const dialogOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
})

const handleSave = async () => {
  if (!props.role) return
  try {
    await roleStore.updateRolePermissions(props.role.id, selectedIds.value)
    emit('saved')
    dialogOpen.value = false
  } catch {
    // 错误已由 store 显示通知，保持弹窗打开
  }
}

const handleCancel = () => {
  dialogOpen.value = false
}
</script>

<template>
  <Dialog v-model:open="dialogOpen">
    <DialogContent class="sm:max-w-lg">
      <DialogHeader>
        <DialogTitle>分配权限</DialogTitle>
        <DialogDescription>
          为角色「{{ role?.name }}」分配权限
        </DialogDescription>
      </DialogHeader>

      <!-- 已选统计 + 全选操作 -->
      <div class="flex items-center justify-between">
        <span class="text-muted-foreground text-sm">
          已选择 {{ selectedCount }}/{{ totalCount }} 项权限
        </span>
        <Button
          variant="outline"
          size="sm"
          :disabled="totalCount === 0"
          @click="toggleSelectAll"
        >
          {{ selectAllButtonText }}
        </Button>
      </div>

      <!-- 权限列表 -->
      <ScrollArea class="h-80 rounded-md border">
        <div v-if="totalCount === 0" class="text-muted-foreground flex h-full items-center justify-center text-sm">
          暂无权限数据
        </div>
        <div v-else class="p-1">
          <div v-for="group in permissionGroups" :key="group.resource">
            <div class="text-muted-foreground px-2 py-1.5 text-xs font-medium">
              {{ group.resource }}
            </div>
            <div
              v-for="perm in group.permissions"
              :key="perm.id"
              class="flex cursor-pointer items-center gap-2 rounded px-2 py-1.5 hover:bg-muted/50"
              @click="togglePermission(perm.id)"
            >
              <Checkbox
                :checked="isSelected(perm.id)"
                @update:checked="() => togglePermission(perm.id)"
                @click.stop
              />
              <span class="flex-1 text-sm">{{ perm.name }}</span>
              <Badge :variant="getActionVariant(perm.action)">
                {{ perm.action }}
              </Badge>
            </div>
          </div>
        </div>
      </ScrollArea>

      <DialogFooter>
        <Button variant="outline" @click="handleCancel">取消</Button>
        <Button @click="handleSave">保存</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
