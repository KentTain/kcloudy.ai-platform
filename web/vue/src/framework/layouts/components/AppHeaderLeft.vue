<script setup lang="ts">
/**
 * AppHeaderLeft 头部左侧组件
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

</script>

<template>
  <!-- 收缩按钮 -->
  <SidebarTrigger class="-ml-1" />
  
  <!-- 分隔线 -->
  <Separator orientation="vertical" class="mt-2 mr-2 data-[orientation=vertical]:h-8" />

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
</template>
