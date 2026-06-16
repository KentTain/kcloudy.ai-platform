<script setup lang="ts">
/**
 * AppHeaderSearchBox 头部搜索框组件
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
