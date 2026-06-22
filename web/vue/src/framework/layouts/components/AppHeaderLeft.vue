<script setup lang="ts">
/**
 * AppHeaderLeft 头部左侧组件
 * 包含收缩按钮、面包屑、水平导航
 * 支持 tenant 管理区域（/admin/*）和普通用户区域
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
import { useAdminMenuStore, type AdminMenuItem } from "@/tenant/stores/adminMenu";

const route = useRoute();
const menuStore = useMenuStore();
const adminMenuStore = useAdminMenuStore();

/**
 * 判断是否在 tenant 管理区域
 */
const isAdminArea = computed(() => route.path.startsWith("/admin"));

/**
 * 从管理员菜单中查找当前路由对应的模块信息和菜单项
 * 返回模块名、模块路径和匹配的菜单项
 */
function findAdminModuleByPath(
  menus: AdminMenuItem[],
  currentPath: string
): { moduleName: string; modulePath: string | null; menuItem?: AdminMenuItem } | null {
  for (const module of menus) {
    // 检查子菜单中是否有匹配的路径
    const matchedChild = module.children?.find((child) => child.path === currentPath);
    if (matchedChild) {
      return {
        moduleName: module.name,
        modulePath: module.path || null, // 模块路径可能为空
        menuItem: matchedChild
      };
    }
  }
  return null;
}

/**
 * 从用户菜单中查找当前路由对应的模块信息和菜单项
 * 返回模块名、模块路径和匹配的菜单项
 */
function findModuleByPath(
  menus: UserMenuItem[],
  currentPath: string
): { moduleName: string; modulePath: string | null } | null {
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

/**
 * 检查路径是否匹配二级菜单
 * 用于区分面包屑中的二级菜单和三级页面
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

  // 根据区域选择不同的菜单数据源
  if (isAdminArea.value) {
    // Tenant 管理区域：使用管理员菜单
    const adminMenus = adminMenuStore.adminMenus;

    // 从当前路由提取二级菜单路径
    const menuPath = extractMenuPath(route.path, adminMenus);

    if (!menuPath) {
      // 如果没有找到匹配的菜单路径，直接显示路由匹配的面包屑
      return matched.map((item) => ({
        title: item.meta?.title as string,
        path: item.path,
      }));
    }

    // 使用提取的菜单路径查找模块信息
    const moduleInfo = findAdminModuleByPath(adminMenus, menuPath);

    if (!moduleInfo) {
      // 如果没有找到模块信息，直接显示路由匹配的面包屑
      return matched.map((item) => ({
        title: item.meta?.title as string,
        path: item.path,
      }));
    }

    const items: { title: string; path?: string }[] = [];

    // 第一级：模块名称（如"租户管理"），无路径不可点击
    items.push({
      title: moduleInfo.moduleName,
      // 模块无 path，不添加 path 属性
    });

    // 第二级：功能菜单（如"租户管理" /admin/tenants）
    if (moduleInfo.menuItem) {
      items.push({
        title: moduleInfo.menuItem.name,
        path: moduleInfo.menuItem.path,
      });
    }

    // 第三级：页面路由（如"租户详情" /admin/tenants/:id）
    // 只有当前路由不是二级菜单路由时才添加
    if (!isSecondaryMenuPath(route.path, adminMenus)) {
      // 使用当前路由的 title，而不是 matched 中的最后一个
      const currentRoute = matched[matched.length - 1];
      if (currentRoute && currentRoute.meta?.title) {
        // 检查是否和二级菜单名称重复，避免重复显示
        if (currentRoute.meta.title !== moduleInfo.menuItem?.name) {
          items.push({
            title: currentRoute.meta.title as string,
            path: currentRoute.path,
          });
        }
      }
    }

    return items;
  } else {
    // 普通用户区域：使用用户菜单
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
  }
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
