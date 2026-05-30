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
