<script setup lang="ts">
import { Ellipsis, Pencil, ShieldCheck, ShieldOff, Text, Trash2 } from "lucide-vue-next";
import { computed } from "vue";
import { Button } from "@/components";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Tenant } from "@/tenant/types";

const props = defineProps<{
  row: Tenant;
  canEdit: boolean;
}>();

const emit = defineEmits<{
  detail: [row: Tenant];
  edit: [row: Tenant];
  activate: [row: Tenant];
  deactivate: [row: Tenant];
  delete: [row: Tenant];
}>();

// 条件判断
const canActivate = computed(() => props.canEdit && props.row.status === "inactive");
const canDeactivate = computed(() => props.canEdit && props.row.status === "active");
const canDelete = computed(() => props.canEdit);
const hasActions = computed(() => true); // 始终有详情操作
</script>

<template>
  <DropdownMenu v-if="hasActions">
    <DropdownMenuTrigger as-child>
      <Button variant="ghost" class="flex h-8 w-8 p-0 data-[state=open]:bg-muted">
        <Ellipsis class="h-4 w-4" />
        <span class="sr-only">打开操作菜单</span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="end" class="w-[120px]">
      <!-- 详情 -->
      <DropdownMenuItem @click="emit('detail', row)">
        <Text class="h-4 w-4" />
        详情
      </DropdownMenuItem>

      <!-- 编辑 -->
      <DropdownMenuItem v-if="canEdit" @click="emit('edit', row)">
        <Pencil class="h-4 w-4" />
        编辑
      </DropdownMenuItem>

      <!-- 激活 -->
      <DropdownMenuItem v-if="canActivate" @click="emit('activate', row)">
        <ShieldCheck class="h-4 w-4" />
        激活
      </DropdownMenuItem>

      <!-- 停用 -->
      <DropdownMenuItem v-if="canDeactivate" @click="emit('deactivate', row)">
        <ShieldOff class="h-4 w-4" />
        停用
      </DropdownMenuItem>

      <!-- 分隔线：删除操作前分隔 -->
      <DropdownMenuSeparator v-if="canDelete" />

      <!-- 删除 -->
      <DropdownMenuItem v-if="canDelete" class="text-destructive" @click="emit('delete', row)">
        <Trash2 class="h-4 w-4" />
        删除
      </DropdownMenuItem>
    </DropdownMenuContent>
  </DropdownMenu>
</template>
