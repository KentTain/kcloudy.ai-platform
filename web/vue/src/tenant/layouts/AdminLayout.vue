<script setup lang="ts">
/**
 * AdminLayout 管理后台布局组件
 * 左右结构：左侧侧边栏（支持折叠图标模式），右侧上下结构（顶部导航 + 内容区）
 */
import { computed } from "vue";
import { useRoute, RouterLink } from "vue-router";
import {
  SidebarProvider,
  Sidebar,
  SidebarInset,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar";
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
import AppBrandHeader from "./components/AppBrandHeader.vue";
import AppNavMain from "./components/AppNavMain.vue";
import AppNavUser from "./components/AppNavUser.vue";
import { useAdminMenuStore, type AdminMenuItem } from "@/tenant/stores/adminMenu";

const route = useRoute();
const adminMenuStore = useAdminMenuStore();

/**
 * 检查路径是否匹配二级菜单
 */
function isSecondaryMenuPath(path: string, menus: AdminMenuItem[]): boolean {
  for (const module of menus) {
    const matched = module.children?.some((child) => child.path === path);
    if (matched) return true;
  }
  return false;
}

/**
 * 检查路由路径是否匹配动态路由模式
 * 例如：/admin/tenants/abc 匹配 /admin/tenants/:id
 */
function isDynamicRoutePath(path: string, menuPath: string): boolean {
  // 将菜单路径转换为正则表达式
  // 例如：/admin/tenants -> ^/admin/tenants(/.*)?$
  const pattern = `^${menuPath}(/[^/]+)?$`;
  return new RegExp(pattern).test(path);
}

/**
 * 从路由路径中提取二级菜单路径
 * 例如：/admin/tenants/abc -> /admin/tenants
 *       /admin/tenants/create -> /admin/tenants
 */
function extractMenuPath(path: string, menus: AdminMenuItem[]): string | null {
  for (const module of menus) {
    for (const child of module.children || []) {
      if (child.path && isDynamicRoutePath(path, child.path)) {
        return child.path;
      }
    }
  }
  return null;
}

/**
 * 从管理员菜单中查找当前路由对应的菜单项
 * 返回面包屑路径：[模块名, 菜单项]
 */
function findMenuBreadcrumb(
  menus: AdminMenuItem[],
  currentPath: string
): { moduleName: string; modulePath: string | null; menuName: string; menuPath: string } | null {
  for (const module of menus) {
    // 在模块的子菜单中查找匹配的路由
    const menuItem = module.children?.find((item) => item.path === currentPath);
    if (menuItem) {
      // 模块路径：优先使用模块自身的 path，否则使用第一个可见子菜单的 path
      const modulePath = module.path || (module.children?.find((child) => child.path)?.path) || null;
      return {
        moduleName: module.name,
        modulePath,
        menuName: menuItem.name,
        menuPath: menuItem.path,
      };
    }
  }
  return null;
}

const breadcrumbItems = computed(() => {
  const meta = route.meta;

  if (!meta?.title) {
    return [];
  }

  // 从当前路由提取二级菜单路径
  const menuPath = extractMenuPath(route.path, adminMenuStore.adminMenus);

  if (!menuPath) {
    // 如果没有找到匹配的菜单路径，降级使用路由标题
    return [{ title: meta.title as string }];
  }

  // 使用提取的菜单路径查找模块信息
  const menuBreadcrumb = findMenuBreadcrumb(adminMenuStore.adminMenus, menuPath);

  if (!menuBreadcrumb) {
    // 如果没有找到菜单数据，降级使用路由标题
    return [{ title: meta.title as string }];
  }

  const items: { title: string; path?: string }[] = [];

  // 第一级：模块名（无路径，不可点击）
  items.push({
    title: menuBreadcrumb.moduleName,
    // 模块无 path，不添加 path 属性
  });

  // 第二级：二级菜单（可点击）
  items.push({
    title: menuBreadcrumb.menuName,
    path: menuBreadcrumb.menuPath,
  });

  // 第三级：页面路由（如"租户详情" /admin/tenants/:id）
  // 只有当前路由不是二级菜单路由时才添加
  if (!isSecondaryMenuPath(route.path, adminMenuStore.adminMenus)) {
    const pageTitle = meta.title as string;
    // 检查是否和二级菜单名称重复，避免重复显示
    if (pageTitle !== menuBreadcrumb.menuName) {
      items.push({
        title: pageTitle,
        path: route.path,
      });
    }
  }

  return items;
});
</script>

<template>
  <SidebarProvider class="h-svh overflow-hidden">
    <!-- 左侧：侧边栏 -->
    <Sidebar collapsible="icon" variant="sidebar" class="border-r">
      <!-- 品牌标识 -->
      <SidebarHeader>
        <AppBrandHeader />
      </SidebarHeader>

      <!-- 菜单导航 -->
      <SidebarContent>
        <AppNavMain />
      </SidebarContent>

      <!-- 用户面板 -->
      <SidebarFooter>
        <AppNavUser />
      </SidebarFooter>
    </Sidebar>

    <!-- 右侧：上下结构 -->
    <SidebarInset class="flex flex-col">
      <!-- 顶部导航栏 -->
      <header class="flex items-center gap-2 px-4 h-14 shrink-0 border-b">
        <SidebarTrigger class="-ml-1" />
        <Separator orientation="vertical" class="mt-2 mr-2 h-10" />
        <Breadcrumb>
          <BreadcrumbList>
            <template v-for="(item, index) in breadcrumbItems" :key="index">
              <BreadcrumbItem v-if="index < breadcrumbItems.length - 1">
                <!-- 有路径时渲染为链接，无路径时渲染为纯文本 -->
                <BreadcrumbLink v-if="item.path" as-child>
                  <RouterLink :to="item.path">{{ item.title }}</RouterLink>
                </BreadcrumbLink>
                <span v-else class="text-muted-foreground">{{ item.title }}</span>
              </BreadcrumbItem>
              <BreadcrumbSeparator v-if="index < breadcrumbItems.length - 1" />
              <BreadcrumbItem v-if="index === breadcrumbItems.length - 1">
                <BreadcrumbPage>{{ item.title }}</BreadcrumbPage>
              </BreadcrumbItem>
            </template>
          </BreadcrumbList>
        </Breadcrumb>
      </header>

      <!-- 内容区 -->
      <div class="flex-1 flex flex-col overflow-hidden">
        <router-view />
      </div>
    </SidebarInset>
  </SidebarProvider>
</template>
