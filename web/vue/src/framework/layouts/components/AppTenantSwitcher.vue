<script setup lang="ts">
/**
 * AppTenantSwitcher 租户切换器组件
 * 显示当前租户 logo 和名称，支持切换租户
 * 参照 shadcn team-switcher 实现
 */
import { computed, onMounted } from "vue";
import { ChevronsUpDown, Building2, Check } from "@lucide/vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import { useUserStore } from "@/framework/stores/user";

const { isMobile } = useSidebar();
const userStore = useUserStore();

const currentTenant = computed(() => userStore.currentTenant);
const tenants = computed(() => userStore.tenants);

const tenantInitial = computed(() => {
  const name = currentTenant.value?.name || "T";
  return name.charAt(0).toUpperCase();
});

// 初始化时选择默认租户
onMounted(() => {
  // 如果当前没有选中租户，但有默认租户，则自动选择
  if (!currentTenant.value && tenants.value.length > 0) {
    const defaultTenant = tenants.value.find((t) => t.is_default);
    if (defaultTenant) {
      switchTenant(defaultTenant.id);
    }
  }
});

function switchTenant(tenantId: string) {
  // TODO: 实现租户切换逻辑
  console.log("Switch to tenant:", tenantId);
}
</script>

<template>
  <SidebarMenu>
    <SidebarMenuItem>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton
            size="lg"
            class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          >
            <div class="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
              <Building2 v-if="!currentTenant" class="size-4" />
              <span v-else class="text-sm font-bold">{{ tenantInitial }}</span>
            </div>
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-medium">{{ currentTenant?.name || "选择租户" }}</span>
              <span class="truncate text-xs">企业版</span>
            </div>
            <ChevronsUpDown class="ml-auto" />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          class="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
          align="start"
          :side="isMobile ? 'bottom' : 'right'"
          :side-offset="4"
        >
          <DropdownMenuLabel class="text-xs text-muted-foreground">
            租户列表
          </DropdownMenuLabel>
          <DropdownMenuItem
            v-for="(tenant, index) in tenants"
            :key="tenant.id"
            :class="tenant.id === currentTenant?.id ? 'bg-accent' : ''"
            class="gap-2 p-2"
            @click="switchTenant(tenant.id)"
          >
            <div class="flex size-6 items-center justify-center rounded-md border">
              <span class="text-xs font-medium">{{ tenant.name.charAt(0).toUpperCase() }}</span>
            </div>
            {{ tenant.name }}
            <Check v-if="tenant.id === currentTenant?.id" class="ml-auto size-4 text-primary" />
            <DropdownMenuShortcut v-else>{{ '' }}{{ index + 1 }}</DropdownMenuShortcut>
          </DropdownMenuItem>
          <DropdownMenuItem v-if="tenants.length === 0" disabled>
            暂无其他租户
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  </SidebarMenu>
</template>
