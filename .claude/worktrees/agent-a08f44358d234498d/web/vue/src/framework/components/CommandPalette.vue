<script setup lang="ts">
/**
 * CommandPalette 全局命令面板组件
 * 支持快捷键 Cmd/Ctrl + K 触发
 * 支持搜索和快速跳转
 */
import { onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { SearchIcon } from "@lucide/vue";
import { Dialog, DialogContent } from "@/components";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useCommandPalette } from "@/framework/composables/useCommandPalette";

const router = useRouter();
const { isOpen, closeCommandPalette } = useCommandPalette();

// 菜单项定义
const menuItems = [
  { title: "首页", url: "/", keywords: ["home", "首页"] },
  { title: "健康检查", url: "/health", keywords: ["health", "健康"] },
  { title: "知识库", url: "/datasets", keywords: ["datasets", "知识库", "数据"] },
  { title: "用户管理", url: "/iam/users", keywords: ["users", "用户", "IAM"] },
  { title: "角色管理", url: "/iam/roles", keywords: ["roles", "角色", "IAM"] },
  { title: "部门管理", url: "/iam/departments", keywords: ["departments", "部门", "IAM"] },
  { title: "租户管理", url: "/iam/tenants", keywords: ["tenants", "租户", "IAM"] },
  { title: "权限管理", url: "/iam/permissions", keywords: ["permissions", "权限", "IAM"] },
  { title: "账号设置", url: "/settings/account", keywords: ["account", "账号", "设置"] },
  { title: "开发者设置", url: "/settings/developer", keywords: ["developer", "开发者", "设置"] },
];

function handleSelect(item: (typeof menuItems)[number]) {
  router.push(item.url);
  closeCommandPalette();
}

// 快捷键监听
function handleKeyDown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === "k") {
    event.preventDefault();
    if (isOpen.value) {
      closeCommandPalette();
    } else {
      // 通过 useCommandPalette 的 toggleCommandPalette 来打开
      const { toggleCommandPalette } = useCommandPalette();
      toggleCommandPalette();
    }
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeyDown);
});
</script>

<template>
  <Dialog :open="isOpen" @update:open="(v) => !v && closeCommandPalette()">
    <DialogContent class="overflow-hidden p-0 shadow-lg max-w-lg">
      <Command class="[&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:font-medium [&_[cmdk-group-heading]]:text-muted-foreground [&_[cmdk-input-wrapper]_svg]:h-5 [&_[cmdk-input-wrapper]_svg]:w-5 [&_[cmdk-input]]:h-12 [&_[cmdk-item]]:px-2 [&_[cmdk-item]]:py-3 [&_[cmdk-item]_svg]:h-5 [&_[cmdk-item]_svg]:w-5">
        <CommandInput placeholder="搜索页面或功能..." />
        <CommandList>
          <CommandEmpty>无匹配入口</CommandEmpty>
          <CommandGroup heading="页面导航">
            <CommandItem
              v-for="item in menuItems"
              :key="item.url"
              :value="item.title"
              @select="handleSelect(item)"
            >
              <SearchIcon class="mr-2 size-4" />
              <span>{{ item.title }}</span>
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </DialogContent>
  </Dialog>
</template>
