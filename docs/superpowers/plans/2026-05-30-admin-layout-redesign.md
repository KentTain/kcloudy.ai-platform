# AdminLayout 布局重设计 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 重构 AdminLayout 布局，实现左右结构：左侧侧边栏（租户切换器 + 菜单），右侧上下结构（顶部导航 + 内容区）

**架构：** 将原来顶部导航栏拆分为两部分：搜索框 + 功能图标 + 用户面板放到全局顶部导航；收缩按钮 + 面包屑移到内容页导航栏

**技术栈：** Vue 3 + TypeScript + shadcn-vue + Tailwind CSS

---

## 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `layouts/components/AppTenantSwitcher.vue` | 租户切换器组件 |
| `layouts/components/AppSearchBox.vue` | 搜索框组件（动态展开 + 结果面板） |
| `layouts/components/AppHeaderRight.vue` | 顶部导航右侧（功能图标 + 用户面板） |
| `layouts/components/AppContentHeader.vue` | 内容页导航栏（收缩按钮 + 面包屑） |
| `layouts/components/AppNotificationPanel.vue` | 通知面板组件 |
| `stores/notification.ts` | 通知状态管理 |
| `pages/PreviewLayoutPage.vue` | 预览页面 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `layouts/AdminLayout.vue` | 重构布局结构 |
| `layouts/components/AppSidebarFooter.vue` | 删除用户面板 |
| `router/index.ts` | 添加预览页面路由 |

---

## 任务 1：创建通知 Store

**文件：**
- 创建：`web/vue/src/framework/stores/notification.ts`

- [ ] **步骤 1：创建通知 Store**

```typescript
import { defineStore } from "pinia";
import { ref, computed } from "vue";

/**
 * 通知类型
 */
export type NotificationType = "system" | "warning" | "success";

/**
 * 通知项
 */
export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  content: string;
  time: Date;
  read: boolean;
}

/**
 * 通知状态管理
 */
export const useNotificationStore = defineStore("notification", () => {
  const notifications = ref<NotificationItem[]>([]);

  const unreadCount = computed(
    () => notifications.value.filter((n) => !n.read).length
  );

  const hasUnread = computed(() => unreadCount.value > 0);

  function addNotification(notification: Omit<NotificationItem, "id" | "time" | "read">) {
    notifications.value.push({
      ...notification,
      id: `notification-${Date.now()}`,
      time: new Date(),
      read: false,
    });
  }

  function markAsRead(id: string) {
    const notification = notifications.value.find((n) => n.id === id);
    if (notification) {
      notification.read = true;
    }
  }

  function markAllAsRead() {
    notifications.value.forEach((n) => (n.read = true));
  }

  function clearAll() {
    notifications.value = [];
  }

  // 模拟数据（开发用）
  function initMockData() {
    notifications.value = [
      {
        id: "1",
        type: "system",
        title: "系统升级通知",
        content: "系统将于今晚 22:00 进行维护升级，届时服务将暂停约 30 分钟。",
        time: new Date(Date.now() - 10 * 60 * 1000),
        read: false,
      },
      {
        id: "2",
        type: "warning",
        title: "存储空间预警",
        content: "知识库存储空间已使用 85%，建议及时清理或扩容。",
        time: new Date(Date.now() - 60 * 60 * 1000),
        read: false,
      },
      {
        id: "3",
        type: "success",
        title: "文档处理完成",
        content: "《API 设计规范》已成功向量化，共处理 128 个文档片段。",
        time: new Date(Date.now() - 2 * 60 * 60 * 1000),
        read: true,
      },
    ];
  }

  return {
    notifications,
    unreadCount,
    hasUnread,
    addNotification,
    markAsRead,
    markAllAsRead,
    clearAll,
    initMockData,
  };
});

export default useNotificationStore;
```

- [ ] **步骤 2：导出 Store**

修改 `web/vue/src/framework/stores/index.ts`，添加导出：

```typescript
export * from "./notification";
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/framework/stores/notification.ts web/vue/src/framework/stores/index.ts
git commit -m "feat(framework): 添加通知状态管理 Store"
```

---

## 任务 2：创建租户切换器组件

**文件：**
- 创建：`web/vue/src/framework/layouts/components/AppTenantSwitcher.vue`

- [ ] **步骤 1：创建租户切换器组件**

```vue
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
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/framework/layouts/components/AppTenantSwitcher.vue
git commit -m "feat(framework): 添加租户切换器组件"
```

---

## 任务 3：创建搜索框组件

**文件：**
- 创建：`web/vue/src/framework/layouts/components/AppSearchBox.vue`

- [ ] **步骤 1：创建搜索框组件**

```vue
<script setup lang="ts">
/**
 * AppSearchBox 搜索框组件
 * 支持动态展开和搜索结果面板
 */
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { Search } from "@lucide/vue";
import { onClickOutside } from "@vueuse/core";

const router = useRouter();

const isExpanded = ref(false);
const isActive = ref(false);
const searchQuery = ref("");
const searchBoxRef = ref<HTMLElement | null>(null);
const panelRef = ref<HTMLElement | null>(null);

// 快速操作
const quickActions = [
  { icon: "📄", title: "新建文档", action: () => console.log("新建文档") },
  { icon: "📚", title: "新建知识库", action: () => router.push("/datasets") },
  { icon: "⚙️", title: "系统设置", action: () => router.push("/settings/account") },
];

// 最近访问
const recentPages = [
  { icon: "📚", title: "产品文档库", url: "/datasets/1" },
  { icon: "👤", title: "用户管理", url: "/iam/users" },
];

function handleMouseEnter() {
  isExpanded.value = true;
}

function handleMouseLeave() {
  if (!isActive.value) {
    isExpanded.value = false;
  }
}

function handleClick() {
  isActive.value = true;
  isExpanded.value = true;
}

function closePanel() {
  isActive.value = false;
  if (!searchBoxRef.value?.matches(":hover")) {
    isExpanded.value = false;
  }
}

function handleSelectAction(action: () => void) {
  action();
  closePanel();
  searchQuery.value = "";
}

function handleSelectPage(url: string) {
  router.push(url);
  closePanel();
  searchQuery.value = "";
}

// 点击外部关闭
onClickOutside(panelRef, (event) => {
  if (searchBoxRef.value && !searchBoxRef.value.contains(event.target as Node)) {
    closePanel();
  }
});

// 快捷键
function handleKeyDown(event: KeyboardEvent) {
  if ((event.metaKey || event.ctrlKey) && event.key === "k") {
    event.preventDefault();
    isActive.value = !isActive.value;
    isExpanded.value = isActive.value;
  }
  if (event.key === "Escape" && isActive.value) {
    closePanel();
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
  <div class="flex-1 flex justify-center relative">
    <!-- 搜索框 -->
    <button
      ref="searchBoxRef"
      type="button"
      class="flex items-center gap-2 px-4 py-2 bg-muted/50 border border-border rounded-[10px] transition-all duration-300 cursor-text hover:border-border/80"
      :class="isExpanded ? 'w-[500px]' : 'w-[280px]'"
      :style="{ boxShadow: isActive ? '0 2px 8px rgba(0,0,0,0.08)' : 'none' }"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
      @click="handleClick"
    >
      <Search class="size-4 text-muted-foreground" />
      <span class="flex-1 text-left text-sm text-muted-foreground">
        搜索功能、文档、设置...
      </span>
      <kbd class="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 bg-muted rounded text-[10px] text-muted-foreground font-medium">
        ⌘K
      </kbd>
    </button>

    <!-- 搜索结果面板 -->
    <div
      v-show="isActive"
      ref="panelRef"
      class="absolute top-full left-1/2 -translate-x-1/2 w-[500px] mt-2 bg-background rounded-xl border border-border shadow-[0_10px_40px_rgba(0,0,0,0.15)] z-50"
    >
      <!-- 快速操作 -->
      <div class="px-4 py-3 border-b border-border">
        <div class="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
          快速操作
        </div>
      </div>
      <div class="p-2">
        <button
          v-for="(action, index) in quickActions"
          :key="index"
          type="button"
          class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-foreground rounded-lg hover:bg-muted transition-colors text-left"
          :class="index === 0 ? 'bg-muted' : ''"
          @click="handleSelectAction(action.action)"
        >
          <span>{{ action.icon }}</span>
          <span>{{ action.title }}</span>
        </button>
      </div>

      <!-- 最近访问 -->
      <div class="px-4 py-3 border-t border-border">
        <div class="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
          最近访问
        </div>
      </div>
      <div class="p-2">
        <button
          v-for="(page, index) in recentPages"
          :key="index"
          type="button"
          class="w-full flex items-center gap-2.5 px-3 py-2.5 text-sm text-foreground rounded-lg hover:bg-muted transition-colors text-left"
          @click="handleSelectPage(page.url)"
        >
          <span>{{ page.icon }}</span>
          <span>{{ page.title }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/framework/layouts/components/AppSearchBox.vue
git commit -m "feat(framework): 添加搜索框组件（动态展开 + 结果面板）"
```

---

## 任务 4：创建通知面板组件

**文件：**
- 创建：`web/vue/src/framework/layouts/components/AppNotificationPanel.vue`

- [ ] **步骤 1：创建通知面板组件**

```vue
<script setup lang="ts">
/**
 * AppNotificationPanel 通知面板组件
 * 显示通知列表，支持全部已读
 */
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { useNotificationStore, type NotificationItem } from "@/framework/stores/notification";

const router = useRouter();
const notificationStore = useNotificationStore();

const notifications = computed(() => notificationStore.notifications);
const unreadCount = computed(() => notificationStore.unreadCount);

function getTypeBgClass(type: NotificationItem["type"]) {
  const classes = {
    system: "bg-blue-50 dark:bg-blue-950",
    warning: "bg-amber-50 dark:bg-amber-950",
    success: "bg-green-50 dark:bg-green-950",
  };
  return classes[type];
}

function getTypeIcon(type: NotificationItem["type"]) {
  const icons = {
    system: "📢",
    warning: "⚠️",
    success: "✅",
  };
  return icons[type];
}

function formatTime(date: Date) {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / (1000 * 60));
  const hours = Math.floor(diff / (1000 * 60 * 60));

  if (minutes < 60) return `${minutes} 分钟前`;
  if (hours < 24) return `${hours} 小时前`;
  return date.toLocaleDateString();
}

function handleMarkAllRead() {
  notificationStore.markAllAsRead();
}

function handleViewAll() {
  router.push("/notifications");
}
</script>

<template>
  <Popover>
    <PopoverTrigger as-child>
      <Button variant="ghost" size="icon" class="relative h-9 w-9">
        <span class="text-base">🔔</span>
        <span
          v-if="unreadCount > 0"
          class="absolute top-1 right-1 w-2 h-2 bg-destructive rounded-full border-2 border-background"
        />
      </Button>
    </PopoverTrigger>
    <PopoverContent align="end" class="w-[360px] p-0">
      <!-- 标题栏 -->
      <div class="flex items-center justify-between px-4 py-3 border-b">
        <span class="text-sm font-semibold">通知</span>
        <button
          type="button"
          class="text-xs text-primary hover:underline"
          @click="handleMarkAllRead"
        >
          全部已读
        </button>
      </div>

      <!-- 通知列表 -->
      <div class="max-h-[320px] overflow-auto">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          class="px-4 py-3 border-b last:border-b-0 hover:bg-muted/50 transition-colors"
          :class="{ 'bg-muted/30': !notification.read }"
        >
          <div class="flex gap-3">
            <div
              class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
              :class="getTypeBgClass(notification.type)"
            >
              {{ getTypeIcon(notification.type) }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="text-[13px] font-medium text-foreground">
                {{ notification.title }}
              </div>
              <div class="text-[12px] text-muted-foreground mt-1 line-clamp-2">
                {{ notification.content }}
              </div>
              <div class="text-[11px] text-muted-foreground/70 mt-1">
                {{ formatTime(notification.time) }}
              </div>
            </div>
          </div>
        </div>

        <div
          v-if="notifications.length === 0"
          class="py-8 text-center text-sm text-muted-foreground"
        >
          暂无通知
        </div>
      </div>

      <!-- 底部 -->
      <div class="px-4 py-3 border-t text-center">
        <button
          type="button"
          class="text-xs text-primary hover:underline"
          @click="handleViewAll"
        >
          查看全部通知
        </button>
      </div>
    </PopoverContent>
  </Popover>
</template>
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/framework/layouts/components/AppNotificationPanel.vue
git commit -m "feat(framework): 添加通知面板组件"
```

---

## 任务 5：创建顶部导航右侧组件

**文件：**
- 创建：`web/vue/src/framework/layouts/components/AppHeaderRight.vue`

- [ ] **步骤 1：创建顶部导航右侧组件**

```vue
<script setup lang="ts">
/**
 * AppHeaderRight 顶部导航右侧区域
 * 包含功能图标（通知/待办/帮助）和用户面板
 */
import { computed } from "vue";
import { useRouter } from "vue-router";
import { Moon, Sun, User, Settings, LogOut, HelpCircle, ClipboardList } from "@lucide/vue";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useUserStore } from "@/framework/stores/user";
import { useColorMode } from "@/framework/composables/useColorMode";
import { useNotificationStore } from "@/framework/stores/notification";
import AppNotificationPanel from "./AppNotificationPanel.vue";

const router = useRouter();
const userStore = useUserStore();
const { toggleTheme } = useColorMode();
const notificationStore = useNotificationStore();

const avatarUrl = computed(() => userStore.userInfo?.avatar || "");
const nickname = computed(() => userStore.userInfo?.nickname || "用户");
const email = computed(() => userStore.userInfo?.email || "");
const initials = computed(() => nickname.value.charAt(0).toUpperCase());

const hasUnreadNotification = computed(() => notificationStore.hasUnread);

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
    <div class="w-px h-6 bg-border mx-1" />

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
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/framework/layouts/components/AppHeaderRight.vue
git commit -m "feat(framework): 添加顶部导航右侧组件（功能图标 + 用户面板）"
```

---

## 任务 6：创建内容页导航栏组件

**文件：**
- 创建：`web/vue/src/framework/layouts/components/AppContentHeader.vue`

- [ ] **步骤 1：创建内容页导航栏组件**

```vue
<script setup lang="ts">
/**
 * AppContentHeader 内容页导航栏组件
 * 包含收缩按钮、面包屑、水平导航
 */
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";

const route = useRoute();
const router = useRouter();

const breadcrumbs = computed(() => {
  const matched = route.matched.filter((item) => item.meta?.title);
  return matched.map((item) => ({
    title: item.meta?.title as string,
    path: item.path,
  }));
});

// 水平导航项（可根据页面动态配置）
const navTabs = computed(() => {
  // 示例：知识库页面的标签
  if (route.path.startsWith("/datasets")) {
    return [
      { title: "全部", key: "all", active: true },
      { title: "我创建的", key: "mine", active: false },
      { title: "共享给我的", key: "shared", active: false },
    ];
  }
  return [];
});
</script>

<template>
  <header class="flex items-center gap-3 px-5 py-3 bg-background border-b">
    <!-- 收缩按钮 -->
    <SidebarTrigger class="h-7 w-7" />
    <Separator orientation="vertical" class="h-5" />

    <!-- 面包屑 -->
    <Breadcrumb v-if="breadcrumbs.length > 0">
      <BreadcrumbList>
        <template v-for="(item, index) in breadcrumbs" :key="item.path">
          <BreadcrumbItem v-if="index < breadcrumbs.length - 1">
            <BreadcrumbLink as-child>
              <RouterLink :to="item.path">{{ item.title }}</RouterLink>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator v-if="index < breadcrumbs.length - 1" />
          <BreadcrumbItem v-if="index === breadcrumbs.length - 1">
            <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
          </BreadcrumbItem>
        </template>
      </BreadcrumbList>
    </Breadcrumb>

    <div class="flex-1" />

    <!-- 水平导航标签 -->
    <div v-if="navTabs.length > 0" class="flex gap-1">
      <button
        v-for="tab in navTabs"
        :key="tab.key"
        type="button"
        class="px-3 py-1.5 text-xs rounded-md transition-colors"
        :class="tab.active ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:bg-muted'"
      >
        {{ tab.title }}
      </button>
    </div>
  </header>
</template>
```

- [ ] **步骤 2：Commit**

```bash
git add web/vue/src/framework/layouts/components/AppContentHeader.vue
git commit -m "feat(framework): 添加内容页导航栏组件"
```

---

## 任务 7：重构 AdminLayout 布局

**文件：**
- 修改：`web/vue/src/framework/layouts/AdminLayout.vue`

- [ ] **步骤 1：重构 AdminLayout 布局**

```vue
<script setup lang="ts">
/**
 * AdminLayout 后台管理布局组件
 * 左右结构：左侧侧边栏，右侧上下结构（顶部导航 + 内容区）
 */
import { onMounted } from "vue";
import { SidebarProvider, Sidebar, SidebarInset, SidebarContent } from "@/components/ui/sidebar";
import AppTenantSwitcher from "./components/AppTenantSwitcher.vue";
import AppNavMain from "./components/AppNavMain.vue";
import AppSearchBox from "./components/AppSearchBox.vue";
import AppHeaderRight from "./components/AppHeaderRight.vue";
import AppContentHeader from "./components/AppContentHeader.vue";
import AppMain from "./components/AppMain.vue";
import { useNotificationStore } from "@/framework/stores/notification";

const notificationStore = useNotificationStore();

onMounted(() => {
  // 初始化模拟通知数据
  notificationStore.initMockData();
});
</script>

<template>
  <SidebarProvider class="h-svh overflow-hidden">
    <!-- 左侧：侧边栏 -->
    <Sidebar collapsible="icon" variant="sidebar" class="border-r">
      <!-- 租户切换器 -->
      <AppTenantSwitcher />

      <!-- 菜单导航 -->
      <SidebarContent>
        <AppNavMain />
      </SidebarContent>
    </Sidebar>

    <!-- 右侧：上下结构 -->
    <SidebarInset class="flex flex-col">
      <!-- 上半部分：顶部导航栏 -->
      <header class="flex items-center gap-4 px-5 h-14 bg-background border-b shrink-0">
        <AppSearchBox />
        <AppHeaderRight />
      </header>

      <!-- 下半部分：内容区 -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <!-- 内容页导航栏 -->
        <AppContentHeader />

        <!-- 内容页 -->
        <AppMain />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
```

- [ ] **步骤 2：删除 AppSidebarFooter 中不再需要的用户面板代码**

修改 `web/vue/src/framework/layouts/components/AppSidebarFooter.vue`，删除用户面板相关代码：

```vue
<script setup lang="ts">
/**
 * AppSidebarFooter 侧边栏底部组件
 * 保留用于未来扩展
 */
</script>

<template>
  <div class="p-2">
    <!-- 预留用于其他功能 -->
  </div>
</template>
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/framework/layouts/AdminLayout.vue web/vue/src/framework/layouts/components/AppSidebarFooter.vue
git commit -m "refactor(framework): 重构 AdminLayout 为左右布局结构"
```

---

## 任务 8：创建预览页面和路由

**文件：**
- 创建：`web/vue/src/framework/pages/PreviewLayoutPage.vue`
- 修改：`web/vue/src/framework/router/index.ts`

- [ ] **步骤 1：创建预览页面**

```vue
<script setup lang="ts">
/**
 * PreviewLayoutPage 布局预览页面
 * 无需登录，用于验证布局效果
 */
import { ref } from "vue";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import AppPage from "@/framework/layouts/components/AppPage.vue";

const datasets = ref([
  { id: 1, name: "产品文档库", count: 128, updated: "2小时前", color: "from-emerald-500 to-emerald-600" },
  { id: 2, name: "FAQ 知识库", count: 256, updated: "1天前", color: "from-amber-500 to-amber-600" },
  { id: 3, name: "技术规范库", count: 64, updated: "3天前", color: "from-blue-500 to-blue-600" },
]);
</script>

<template>
  <AppPage
    title="知识库管理"
    eyebrow="知识管理"
    description="管理系统的知识库资源，支持文档上传、向量化处理和智能检索"
  >
    <template #actions>
      <Button class="bg-gradient-to-r from-primary to-primary/80 shadow-sm">
        + 新建知识库
      </Button>
      <Button variant="outline">
        筛选
      </Button>
    </template>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <Card
        v-for="dataset in datasets"
        :key="dataset.id"
        class="hover:shadow-md transition-shadow cursor-pointer"
      >
        <CardHeader class="pb-3">
          <div class="flex items-center gap-3">
            <div
              :class="`w-11 h-11 rounded-xl bg-gradient-to-br ${dataset.color} flex items-center justify-center text-white`"
            >
              📚
            </div>
            <div>
              <CardTitle class="text-base">{{ dataset.name }}</CardTitle>
              <p class="text-xs text-muted-foreground mt-0.5">
                {{ dataset.count }} 个文档 · 更新于 {{ dataset.updated }}
              </p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <p class="text-sm text-muted-foreground line-clamp-2">
            存储产品相关的技术文档、API 规格和使用指南，支持智能检索和问答。
          </p>
        </CardContent>
      </Card>
    </div>
  </AppPage>
</template>
```

- [ ] **步骤 2：添加预览路由**

修改 `web/vue/src/framework/router/index.ts`，在 `constantRoutes` 中添加：

```typescript
{
  path: "/preview/layout",
  name: "PreviewLayout",
  component: () => import("@/framework/pages/PreviewLayoutPage.vue"),
  meta: { title: "布局预览", hidden: true, requiresAuth: false },
},
```

- [ ] **步骤 3：Commit**

```bash
git add web/vue/src/framework/pages/PreviewLayoutPage.vue web/vue/src/framework/router/index.ts
git commit -m "feat(framework): 添加布局预览页面和路由"
```

---

## 任务 9：验证和清理

- [ ] **步骤 1：启动开发服务器**

```bash
cd web/vue && pnpm dev
```

- [ ] **步骤 2：访问预览页面验证布局**

浏览器访问 `http://localhost:5173/preview/layout`，验证：
- 左右布局结构正确
- 租户切换器显示正常
- 搜索框动态展开效果
- 功能图标和通知面板
- 用户面板下拉菜单
- 内容页导航栏（收缩按钮 + 面包屑）

- [ ] **步骤 3：最终 Commit**

```bash
git add -A
git commit -m "feat(framework): 完成 AdminLayout 布局重设计"
```
