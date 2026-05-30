import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { adminLogin as adminLoginApi, adminLogout as adminLogoutApi } from "../api/admin";
import type { AdminLoginRequest, AdminInfo } from "../types/admin";
import { notifyError } from "@/framework/utils/feedback";

const ADMIN_TOKEN_KEY = "admin_token";
const ADMIN_INFO_KEY = "admin_info";

export const useAdminAuthStore = defineStore("admin-auth", () => {
  const token = ref<string | null>(localStorage.getItem(ADMIN_TOKEN_KEY));
  const adminInfo = ref<AdminInfo | null>(
    JSON.parse(localStorage.getItem(ADMIN_INFO_KEY) || "null")
  );

  const isLoggedIn = computed(() => !!token.value);
  const username = computed(() => adminInfo.value?.username || "");
  const isDefault = computed(() => adminInfo.value?.is_default || false);

  const login = async (data: AdminLoginRequest): Promise<boolean> => {
    try {
      const response = await adminLoginApi(data);
      const result = response.data;

      token.value = result.token;
      adminInfo.value = {
        id: "",
        username: result.username,
        is_default: result.is_default,
        is_active: true,
      };

      localStorage.setItem(ADMIN_TOKEN_KEY, result.token);
      localStorage.setItem(ADMIN_INFO_KEY, JSON.stringify(adminInfo.value));

      return true;
    } catch (error: any) {
      notifyError(error?.response?.data?.message || "登录失败");
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
      localStorage.removeItem(ADMIN_TOKEN_KEY);
      localStorage.removeItem(ADMIN_INFO_KEY);
    }
  };

  const checkAuth = (): boolean => {
    const savedToken = localStorage.getItem(ADMIN_TOKEN_KEY);
    const savedInfo = localStorage.getItem(ADMIN_INFO_KEY);

    if (savedToken && savedInfo) {
      token.value = savedToken;
      adminInfo.value = JSON.parse(savedInfo);
      return true;
    }

    return false;
  };

  return {
    token,
    adminInfo,
    isLoggedIn,
    username,
    isDefault,
    login,
    logout,
    checkAuth,
  };
});
