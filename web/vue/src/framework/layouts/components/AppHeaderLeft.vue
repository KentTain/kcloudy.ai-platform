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
 * 从用户菜单中查找当前路由对应的模块信息和菜单项
 * 返回模块名、模块路径和匹配的菜单项
 */
function findModuleByPath(menus: UserMenuItem[], currentPath: string): { moduleName: string; modulePath: string | null } | null {
  for (const module of menus) {
    // 检查模块本身的路径是否匹配
    if (module.path === currentPath) {
      return { moduleName: module.name, modulePath: module.path };
    }
    // 检查子菜单中是否有匹配的路径
    const matchedChild = module.children?.find((child) => child.path === currentPath);
    if (matchedChild) {
      // 模块路径：优先使用模块自身的 path，否则使用第一个可见子菜单的 path
      const modulePath = module.path || (module.children?.find((child) => child.path)?.path) || null;
      return { moduleName: module.name, modulePath };
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

  // 从菜单数据中查找当前路由对应的模块信息
  const moduleInfo = findModuleByPath(menuStore.userMenus, route.path);

  // 构建面包屑
  const items: { title: string; path?: string }[] = [];

  // 如果找到模块信息且不是首页，添加模块作为第一级
  if (moduleInfo && route.path !== "/") {
    items.push({
      title: moduleInfo.moduleName,
      // 只有模块有有效路径时才添加
      ...(moduleInfo.modulePath ? { path: moduleInfo.modulePath } : {})
    });
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
  <Breadcrumb v-if="breadcrumbs.length > 0" class="hidden md:block">
    <BreadcrumbList>
      <template v-for="(item, index) in breadcrumbs" :key="index">
        <BreadcrumbItem v-if="index < breadcrumbs.length - 1">
          <!-- 有路径时渲染为链接，无路径时渲染为纯文本 -->
          <BreadcrumbLink v-if="item.path" as-child>
            <RouterLink :to="item.path">{{ item.title }}</RouterLink>
          </BreadcrumbLink>
          <span v-else class="text-muted-foreground">{{ item.title }}</span>
        </BreadcrumbItem>
        <BreadcrumbSeparator v-if="index < breadcrumbs.length - 1" />
        <BreadcrumbItem v-if="index === breadcrumbs.length - 1">
          <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
        </BreadcrumbItem>
      </template>
    </BreadcrumbList>
  </Breadcrumb>
</template>
