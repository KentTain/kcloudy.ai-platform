<script setup lang="ts">
/**
 * AppHeaderRight 顶部导航右侧区域
 * 包含功能图标（通知/待办/帮助）和用户面板
 */
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Moon, Sun, User, LogOut, HelpCircle, ClipboardList } from "@lucide/vue";
import { Button } from "@/components";
import { Separator } from "@/components/ui/separator";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useUserStore } from "@/framework/stores/user";
import { useColorMode } from "@/framework/composables/useColorMode";
import AppNotificationPanel from "./AppNotificationPanel.vue";

const router = useRouter();
const userStore = useUserStore();
const { toggleTheme } = useColorMode();

const avatarUrl = computed(() => userStore.userInfo?.avatar || "");
const nickname = computed(() => userStore.userInfo?.nickname || "用户");
const email = computed(() => userStore.userInfo?.email || "");
const initials = computed(() => nickname.value.charAt(0).toUpperCase());

// 待办数量（模拟）
const todoCount = computed(() => 3);

function navigateTo(path: string) {
  router.push(path);
}

function handleLogout() {
  userStore.logout();
  router.push("/login");
}
</script>

<template>
  <div class="flex items-center gap-2">
    <!-- 通知 -->
    <AppNotificationPanel />

    <!-- 待办 -->
    <Button variant="ghost" size="icon" class="relative h-9 w-9" @click="navigateTo('/todos')">
      <ClipboardList class="size-4" />
      <span
        v-if="todoCount > 0"
        class="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full border-2 border-background"
      />
    </Button>

    <!-- 帮助 -->
    <Button variant="ghost" size="icon" class="h-9 w-9">
      <HelpCircle class="size-4" />
    </Button>

    <!-- 分隔线 -->
    <Separator orientation="vertical" class="mt-2 mr-2 h-10" />

    <!-- 用户面板 -->
    <DropdownMenu>
      <DropdownMenuTrigger as-child>
        <button
          type="button"
          class="flex items-center gap-2.5 px-2.5 py-1.5 rounded-[10px] bg-muted/50 hover:bg-muted transition-colors"
        >
          <Avatar class="h-8 w-8">
            <AvatarImage :src="avatarUrl" />
            <AvatarFallback class="bg-gradient-to-br from-orange-500 to-orange-600 text-white text-xs font-medium">
              {{ initials }}
            </AvatarFallback>
          </Avatar>
          <div class="text-left hidden sm:block">
            <div class="text-[13px] font-medium text-foreground">{{ nickname }}</div>
            <div class="text-[11px] text-muted-foreground truncate max-w-[120px]">{{ email }}</div>
          </div>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" class="w-48">
        <DropdownMenuItem @click="toggleTheme">
          <Moon class="size-4 mr-2 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Sun class="absolute size-4 mr-2 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span>切换主题</span>
        </DropdownMenuItem>
        <DropdownMenuItem @click="navigateTo('/settings/account')">
          <User class="size-4 mr-2" />
          <span>账号设置</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem class="text-destructive focus:text-destructive" @click="handleLogout">
          <LogOut class="size-4 mr-2" />
          <span>退出登录</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  </div>
</template>
