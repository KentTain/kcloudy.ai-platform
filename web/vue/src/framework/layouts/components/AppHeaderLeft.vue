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
import { useMenuStore, type UserMenuItem } from "@/framework/stores/menu";

const route = useRoute();
const menuStore = useMenuStore();

/**
 * 从用户菜单中查找当前路由对应的模块名
 */
function findModuleByPath(menus: UserMenuItem[], currentPath: string): string | null {
  for (const module of menus) {
    // 检查模块本身的路径是否匹配
    if (module.path === currentPath) {
      return module.name;
    }
    // 检查子菜单中是否有匹配的路径
    if (module.children?.some((child) => child.path === currentPath)) {
      return module.name;
    }
  }
  return null;
}

// 面包屑数据
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

  // 从菜单数据中查找当前路由对应的模块名
  const moduleName = findModuleByPath(menuStore.userMenus, route.path);

  // 构建面包屑
  const items: { title: string; path?: string }[] = [];

  // 如果找到模块名且不是首页，添加模块作为第一级
  if (moduleName && route.path !== "/") {
    items.push({ title: moduleName });
  }

  // 添加当前页面的面包屑
  for (const item of matched) {
    items.push({
      title: item.meta?.title as string,
      path: item.path,
    });
  }

  return items;
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
