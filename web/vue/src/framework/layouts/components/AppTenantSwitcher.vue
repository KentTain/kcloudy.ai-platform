<script setup lang="ts">
/**
 * AppTenantSwitcher 租户切换器组件
 * 显示当前租户 logo 和名称，支持切换租户
 */
import { computed } from "vue";
import { ChevronsUpDown } from "@lucide/vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useUserStore } from "@/framework/stores/user";

const userStore = useUserStore();

const currentTenant = computed(() => userStore.currentTenant);
const tenants = computed(() => userStore.tenants);

const tenantInitial = computed(() => {
  const name = currentTenant.value?.name || "T";
  return name.charAt(0).toUpperCase();
});

function switchTenant(tenantId: string) {
  // TODO: 实现租户切换逻辑
  console.log("Switch to tenant:", tenantId);
}
</script>

<template>
  <div class="px-3 py-3">
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <button
          type="button"
          class="flex w-full items-center gap-2.5 rounded-[10px] bg-muted/50 px-2.5 py-2.5 text-left transition-colors hover:bg-muted"
        >
          <div
            class="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-primary/80 text-primary-foreground text-sm font-bold shadow-sm"
          >
            {{ tenantInitial }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="text-[13px] font-semibold text-foreground truncate">
              {{ currentTenant?.name || "选择租户" }}
            </div>
            <div class="text-[11px] text-muted-foreground">企业版</div>
          </div>
          <ChevronsUpDown class="size-4 text-muted-foreground shrink-0" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" class="w-[200px]">
        <DropdownMenuItem
          v-for="tenant in tenants"
          :key="tenant.id"
          :class="tenant.id === currentTenant?.id ? 'bg-accent' : ''"
          @click="switchTenant(tenant.id)"
        >
          {{ tenant.name }}
        </DropdownMenuItem>
        <DropdownMenuItem v-if="tenants.length === 0" disabled>
          暂无其他租户
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>
