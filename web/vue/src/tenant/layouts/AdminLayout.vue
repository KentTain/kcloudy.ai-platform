<script setup lang="ts">
/**
 * AdminLayout 管理后台布局组件
 * 左右结构：左侧侧边栏（支持折叠图标模式），右侧上下结构（顶部导航 + 内容区）
 */
import { computed } from "vue";
import { useRoute } from "vue-router";
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
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import AppBrandHeader from "./components/AppBrandHeader.vue";
import AppNavMain from "./components/AppNavMain.vue";
import AppNavUser from "./components/AppNavUser.vue";
import { useAdminMenuStore, type AdminMenuItem } from "@/tenant/stores/adminMenu";
import { onMounted } from "vue";

const route = useRoute();
const adminMenuStore = useAdminMenuStore();

// 组件挂载时获取菜单数据
onMounted(() => {
  if (adminMenuStore.adminMenus.length === 0) {
    adminMenuStore.fetchAdminMenus();
  }
});

/**
 * 从管理员菜单中查找当前路由对应的菜单项
 * 返回面包屑路径：[模块名, 菜单项]
 */
function findMenuBreadcrumb(
  menus: AdminMenuItem[],
  currentPath: string
): { moduleName: string; menuName: string } | null {
  for (const module of menus) {
    // 在模块的子菜单中查找匹配的路由
    const menuItem = module.children?.find((item) => item.path === currentPath);
    if (menuItem) {
      return {
        moduleName: module.name,
        menuName: menuItem.name,
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

  // 从菜单数据中查找当前路由对应的模块和菜单
  const menuBreadcrumb = findMenuBreadcrumb(adminMenuStore.adminMenus, route.path);

  if (menuBreadcrumb) {
    return [
      { title: menuBreadcrumb.moduleName }, // 第一级：模块名，不可点击
      { title: menuBreadcrumb.menuName }, // 第二级：当前菜单，不可点击
    ];
  }

  // 降级处理：如果没有找到菜单数据，使用路由标题
  return [{ title: meta.title as string }];
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
            <template v-for="(item, index) in breadcrumbItems" :key="item.title">
              <BreadcrumbItem v-if="index < breadcrumbItems.length - 1">
                <span class="text-muted-foreground">{{ item.title }}</span>
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
