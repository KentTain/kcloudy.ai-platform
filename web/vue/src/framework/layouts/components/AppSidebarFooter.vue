<script setup lang="ts">
/**
 * AppSidebarFooter 增强的用户菜单组件
 * 包含主题切换、账号设置、开发者设置和退出登录入口
 */
import { computed } from "vue";
import { useRouter } from "vue-router";
import { ChevronsUpDown, MoonIcon, SunIcon, ContactRound, KeyRound, LogOut } from "@lucide/vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem, useSidebar } from "@/components/ui/sidebar";
import { useUserStore } from "@/framework/stores/user";
import { useColorMode } from "@/framework/composables/useColorMode";

const router = useRouter();
const { isMobile } = useSidebar();
const userStore = useUserStore();
const { toggleTheme } = useColorMode();

const avatarUrl = computed(() => userStore.userInfo?.avatar || "");
const nickname = computed(() => userStore.userInfo?.nickname || "用户");
const username = computed(() => userStore.userInfo?.username || "");
const initials = computed(() => nickname.value.charAt(0).toUpperCase());

function handleThemeToggle() {
  toggleTheme();
}

function navigateTo(path: string) {
  router.push(path);
}

function handleLogout() {
  userStore.logout();
  router.push("/login");
}
</script>

<template>
  <SidebarMenu>
    <SidebarMenuItem>
      <DropdownMenu>
        <DropdownMenuTrigger as-child>
          <SidebarMenuButton
            class="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
            size="lg"
          >
            <Avatar class="h-8 w-8 rounded-lg">
              <AvatarImage :src="avatarUrl" />
              <AvatarFallback class="rounded-lg">{{ initials }}</AvatarFallback>
            </Avatar>
            <div class="grid flex-1 text-left text-sm leading-tight">
              <span class="truncate font-semibold">{{ nickname }}</span>
              <span class="truncate text-xs">{{ username }}</span>
            </div>
            <ChevronsUpDown class="ml-auto size-4" />
          </SidebarMenuButton>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          :side="isMobile ? 'bottom' : 'right'"
          align="end"
          :side-offset="4"
          class="w-[--reka-dropdown-menu-trigger-width] min-w-56 rounded-lg"
        >
          <DropdownMenuLabel class="p-0 font-normal">
            <div class="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
              <Avatar class="h-8 w-8 rounded-lg">
                <AvatarImage :src="avatarUrl" />
                <AvatarFallback class="rounded-lg">{{ initials }}</AvatarFallback>
              </Avatar>
              <div class="grid flex-1 text-left text-sm leading-tight">
                <span class="truncate font-semibold">{{ nickname }}</span>
                <span class="truncate text-xs">{{ username }}</span>
              </div>
            </div>
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem @click="handleThemeToggle">
              <MoonIcon class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <SunIcon class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span>切换主题</span>
            </DropdownMenuItem>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuGroup>
            <DropdownMenuItem @click="navigateTo('/settings/account')">
              <ContactRound class="mr-2 size-4" />
              账号设置
            </DropdownMenuItem>
            <DropdownMenuItem @click="navigateTo('/settings/developer')">
              <KeyRound class="mr-2 size-4" />
              开发者设置
            </DropdownMenuItem>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem @click="handleLogout">
            <LogOut class="mr-2 size-4" />
            退出登录
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </SidebarMenuItem>
  </SidebarMenu>
</template>
