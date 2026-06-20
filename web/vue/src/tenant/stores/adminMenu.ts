/**
 * 管理员菜单状态管理
 *
 * 菜单数据来自 Tenant 模块（module.code='tenant'）的 module_menus。
 * 使用 admin_token 认证（由 API 客户端拦截器自动处理）。
 */
import { defineStore } from "pinia";
import { ref } from "vue";
import { rawGet } from "@/framework/api/client";
import type { Success } from "@/framework/types";

/**
 * 管理员菜单项
 */
export interface AdminMenuItem {
  id: string;
  module_id: string;
  parent_id: string | null;
  code: string;
  name: string;
  path: string;
  icon: string | null;
  sort_order: number;
  is_visible: boolean;
  children: AdminMenuItem[];
}

export const useAdminMenuStore = defineStore("admin-menu", () => {
  /** 菜单列表 */
  const adminMenus = ref<AdminMenuItem[]>([]);
  /** 加载状态 */
  const loading = ref(false);
  /** 错误信息 */
  const error = ref<string | null>(null);

  /**
   * 获取管理员菜单
   */
  async function fetchAdminMenus(): Promise<void> {
    loading.value = true;
    error.value = null;

    try {
      const response = await rawGet<Success<AdminMenuItem[]>>(
        "/tenant/admin/v1/admin/menus"
      );
      adminMenus.value = response.data || [];
    } catch (err) {
      error.value = err instanceof Error ? err.message : "获取菜单失败";
      adminMenus.value = [];
    } finally {
      loading.value = false;
    }
  }

  /**
   * 清空菜单状态
   */
  function clearMenus(): void {
    adminMenus.value = [];
    loading.value = false;
    error.value = null;
  }

  return {
    adminMenus,
    loading,
    error,
    fetchAdminMenus,
    clearMenus,
  };
});

export default useAdminMenuStore;
