import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { adminLogin as adminLoginApi, adminLogout as adminLogoutApi, getCurrentAdmin } from "../api/admin";
import type { AdminLoginRequest, AdminInfo } from "../types/admin";
import type { AdminMenuItem } from "./adminMenu";
import { useAdminMenuStore } from "./adminMenu";
import { notifyError } from "@/framework/utils/feedback";

const ADMIN_TOKEN_KEY = "admin_token";
const ADMIN_INFO_KEY = "admin_info";
const ADMIN_ROLE_KEY = "admin_role";
const ADMIN_PERMISSIONS_KEY = "admin_permissions";
const ADMIN_MENUS_KEY = "admin_menus";

export const useAdminAuthStore = defineStore("admin-auth", () => {
  const token = ref<string | null>(localStorage.getItem(ADMIN_TOKEN_KEY));
  const adminInfo = ref<AdminInfo | null>(
    JSON.parse(localStorage.getItem(ADMIN_INFO_KEY) || "null")
  );
  const role = ref<string>(localStorage.getItem(ADMIN_ROLE_KEY) || "");
  const permissions = ref<string[]>(
    JSON.parse(localStorage.getItem(ADMIN_PERMISSIONS_KEY) || "[]")
  );
  const menus = ref<AdminMenuItem[]>(
    JSON.parse(localStorage.getItem(ADMIN_MENUS_KEY) || "[]")
  );

  const isLoggedIn = computed(() => !!token.value);
  const username = computed(() => adminInfo.value?.username || "");
  const isDefault = computed(() => adminInfo.value?.is_default || false);
  const isAdmin = computed(() => !!role.value);
  const currentRole = computed(() => role.value);

  /**
   * 检查是否有指定权限码
   * 支持通配符 *:*:*（匹配所有权限）
   * 支持 module:*:*（匹配模块下所有资源）
   * 支持 module:resource:*（匹配资源下所有操作）
   */
  const hasPermission = (code: string): boolean => {
    if (!permissions.value.length) return false;
    if (permissions.value.includes("*:*:*")) return true;
    if (permissions.value.includes(code)) return true;

    // 支持 module:*:* 和 module:resource:* 通配
    const parts = code.split(":");
    if (parts.length === 3) {
      const [module, resource] = parts;
      if (permissions.value.includes(`${module}:*:*`)) return true;
      if (permissions.value.includes(`${module}:${resource}:*`)) return true;
    }
    return false;
  };

  /**
   * 检查角色是否匹配
   */
  const hasRole = (code: string): boolean => {
    if (!role.value) return false;
    return role.value === code;
  };

  const login = async (data: AdminLoginRequest): Promise<boolean> => {
    try {
      const response = await adminLoginApi(data);
      const result = response.data;

      token.value = result.token;

      // 登录成功后获取完整管理员信息（角色、权限、菜单）
      const adminInfoResponse = await getCurrentAdmin();
      const adminInfoData = adminInfoResponse.data;

      adminInfo.value = adminInfoData;
      role.value = adminInfoData.role;
      permissions.value = adminInfoData.permissions;
      menus.value = adminInfoData.menus;

      // 同步保存到 localStorage
      localStorage.setItem(ADMIN_TOKEN_KEY, result.token);
      localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(adminInfo.value));
      localStorage.setItem(ADMIN_ROLE_KEY, role.value);
      localStorage.setItem(ADMIN_PERMISSIONS_KEY, JSON.stringify(permissions.value));
      localStorage.setItem(ADMIN_MENUS_KEY, JSON.stringify(menus.value));

      return true;
    } catch (error: any) {
      notifyError(error?.response?.data?.msg || "登录失败");
      return false;
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await adminLogoutApi();
    } catch {
      // ignore
    } finally {
      token.value = null;
      adminInfo.value = null;
      role.value = "";
      permissions.value = [];
      menus.value = [];

      // 同步清除 localStorage
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      localStorage.removeItem(ADMIN_INFO_KEY);
      localStorage.removeItem(ADMIN_ROLE_KEY);
      localStorage.removeItem(ADMIN_PERMISSIONS_KEY);
      localStorage.removeItem(ADMIN_MENUS_KEY);

      // 清空菜单 store
      const adminMenuStore = useAdminMenuStore();
      adminMenuStore.clearMenus();
    }
  };

  const checkAuth = (): boolean => {
    const savedToken = localStorage.getItem(ADMIN_TOKEN_KEY);
    const savedInfo = localStorage.getItem(ADMIN_INFO_KEY);
    const savedRole = localStorage.getItem(ADMIN_ROLE_KEY);
    const savedPermissions = localStorage.getItem(ADMIN_PERMISSIONS_KEY);
    const savedMenus = localStorage.getItem(ADMIN_MENUS_KEY);

    if (savedToken && savedInfo) {
      token.value = savedToken;
      adminInfo.value = JSON.parse(savedInfo);
      role.value = savedRole || "";
      permissions.value = savedPermissions ? JSON.parse(savedPermissions) : [];
      menus.value = savedMenus ? JSON.parse(savedMenus) : [];
      return true;
    }

    return false;
  };

  return {
    token,
    adminInfo,
    role,
    permissions,
    menus,
    isLoggedIn,
    username,
    isDefault,
    isAdmin,
    currentRole,
    login,
    logout,
    checkAuth,
    hasPermission,
    hasRole,
  };
});
