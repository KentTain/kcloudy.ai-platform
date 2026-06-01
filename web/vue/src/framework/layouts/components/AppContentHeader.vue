<script setup lang="ts">
/**
 * AppContentHeader 内容页导航栏组件
 * 包含收缩按钮、面包屑、水平导航
 */
import { computed } from "vue";
import { useRoute } from "vue-router";
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

// 面包屑数据从 route.matched 提取
const breadcrumbs = computed(() => {
  // 特殊处理首页
  if (route.path === "/") {
    return [{ title: "首页", path: "/" }];
  }

  // 从路由匹配中提取有标题的路由
  const matched = route.matched.filter((item) => item.meta?.title);

  if (matched.length === 0) {
    return [];
  }

  return matched.map((item) => ({
    title: item.meta?.title as string,
    path: item.path,
  }));
});

// Mock 水平导航数据（实际应根据页面动态配置）
const navTabs = computed(() => {
  // 示例：知识库页面的标签
  if (route.path.startsWith("/datasets")) {
    return [
      { title: "全部", key: "all", active: true },
      { title: "我创建的", key: "mine", active: false },
      { title: "共享给我的", key: "shared", active: false },
    ];
  }
  
  // 示例：用户管理页面的标签
  if (route.path === "/iam/users") {
    return [
      { title: "全部用户", key: "all", active: true },
      { title: "已激活", key: "active", active: false },
      { title: "已禁用", key: "disabled", active: false },
    ];
  }
  
  // Mock 数据演示
  return [
    { title: "全部", key: "all", active: true },
    { title: "进行中", key: "progress", active: false },
    { title: "已完成", key: "done", active: false },
  ];
});

function handleTabClick(key: string) {
  console.log("Tab clicked:", key);
  // TODO: 切换 tab 逻辑
}
</script>

<template>
  <header class="flex items-center gap-2 px-4 h-12 shrink-0 border-b transition-[height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
    <!-- 收缩按钮 -->
    <SidebarTrigger class="-ml-1" />
    <Separator orientation="vertical" class="mr-2 data-[orientation=vertical]:h-4" />

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
        @click="handleTabClick(tab.key)"
      >
        {{ tab.title }}
      </button>
    </div>
  </header>
</template>
