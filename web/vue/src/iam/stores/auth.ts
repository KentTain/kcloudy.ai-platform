import { defineStore } from "pinia";
import { ref } from "vue";
import { useUserStore } from "@/framework/stores";
import { useMenuStore } from "@/framework/stores/menu";
import type { UserInfo } from "@/framework/stores/user";
import {
  getCurrentUser as getCurrentUserApi,
  login as loginApi,
  logout as logoutApi,
  refreshToken as refreshTokenApi,
} from "../api/auth";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { LoginRequest, LoginResponse, User } from "../types";
import { isSuccess } from "@/framework/api/types";

/**
 * 将 IAM User 转换为 Framework UserInfo
 */
const convertToUserInfo = (user: User): UserInfo => {
  // 找到默认租户
  const defaultTenant = user.tenants?.find((t) => t.is_default);
  // user.tenant_id 是后端返回的字段名（下划线）
  const currentTenant = user.tenants?.find((t) => t.id === user.tenant_id) || defaultTenant;

  return {
    id: user.id,
    username: user.username,
    nickname: user.nickname || user.username,
    avatar: user.avatar,
    email: user.email,
    roles: user.roles || [],
    permissions: user.permissions || [],
    tenantId: user.tenant_id,
    tenantName: currentTenant?.name,
    tenantCode: currentTenant?.code,
    tenants: user.tenants?.map((t) => ({
      id: t.id,
      name: t.name,
      code: t.code,
      is_default: t.is_default,
    })),
  };
};

const decodeJwtPayload = (token: string): Record<string, any> => {
  try {
    const [, payload] = token.split(".");
    if (!payload) return {};
    const normalized = payload.replace(/-/g, "+").replace(/_/g, "/");
    const padded = normalized.padEnd(normalized.length + ((4 - (normalized.length % 4)) % 4), "=");
    return JSON.parse(atob(padded));
  } catch {
    return {};
  }
};

const getExpiresAt = (token: string, response: LoginResponse) => {
  const payload = decodeJwtPayload(token);
  if (typeof payload.exp === "number") {
    return payload.exp * 1000;
  }
  return Date.now() + response.expires_in * 1000;
};

const createFallbackUserInfo = (account: string, accessToken: string): UserInfo => {
  const payload = decodeJwtPayload(accessToken);
  const username = payload.username || payload.preferred_username || payload.sub || account;
  const roles = Array.isArray(payload.roles) ? payload.roles : [];
  const permissions = Array.isArray(payload.permissions) ? payload.permissions : [];

  return {
    id: String(payload.user_id || payload.uid || payload.sub || username),
    username,
    nickname: payload.nickname || username,
    avatar: payload.avatar,
    email: payload.email,
    roles,
    permissions,
  };
};

export const useAuthStore = defineStore("iam-auth", () => {
  const loading = ref(false);
  const userStore = useUserStore();
  const menuStore = useMenuStore();

  const login = async (data: LoginRequest) => {
    loading.value = true;
    try {
      const response = await loginApi(data);
      if (!isSuccess(response)) {
        notifyError(response.msg || "登录失败");
        throw new Error(response.msg || "登录失败");
      }

      const { access_token, refresh_token, tenant_id } = response.data;
      const expires_at = getExpiresAt(access_token, response.data);

      // 保存 token
      localStorage.setItem("token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      localStorage.setItem("token_expires_at", String(expires_at));

      // 保存租户 ID
      if (tenant_id) {
        localStorage.setItem("tenant_id", tenant_id);
      }

      userStore.setToken(access_token);

      try {
        const userResponse = await getCurrentUserApi();
        if (!isSuccess(userResponse)) {
          console.warn("getCurrentUser failed after login, using fallback user info");
          userStore.setUserInfo(createFallbackUserInfo(data.account, access_token));
        } else {
          userStore.setUserInfo(convertToUserInfo(userResponse.data));

          // 登录时已返回菜单数据，直接设置到 menuStore
          if (userResponse.data.menus && Array.isArray(userResponse.data.menus)) {
            menuStore.setUserMenus(userResponse.data.menus);
          }
        }
      } catch (error) {
        console.warn("getCurrentUser failed after login, using fallback user info:", error);
        userStore.setUserInfo(createFallbackUserInfo(data.account, access_token));
      }

      notifySuccess("登录成功");
      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "登录失败"));
      console.error("login error:", error);
      throw error;
    } finally {
      loading.value = false;
    }
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch {
      // ignore
    } finally {
      // 清理本地存储
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("token_expires_at");
      localStorage.removeItem("tenant_id");
      userStore.logout();
      menuStore.clearMenus();
    }
  };

  const refresh = async () => {
    const refresh_token = localStorage.getItem("refresh_token");
    if (!refresh_token) {
      throw new Error("No refresh token");
    }

    const response = await refreshTokenApi(refresh_token);
    if (!isSuccess(response)) {
      throw new Error(response.msg || "Token refresh failed");
    }

    const { access_token, refresh_token: new_refresh_token } = response.data;

    localStorage.setItem("token", access_token);
    localStorage.setItem("refresh_token", new_refresh_token);
    userStore.setToken(access_token);

    return response.data;
  };

  const checkAuth = (): boolean => {
    const token = localStorage.getItem("token");
    const expiresAt = localStorage.getItem("token_expires_at");

    if (!token) {
      return false;
    }

    if (expiresAt && Date.now() > parseInt(expiresAt, 10)) {
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("token_expires_at");
      localStorage.removeItem("tenant_id");
      return false;
    }

    userStore.setToken(token);
    return true;
  };

  return {
    loading,
    login,
    logout,
    refresh,
    checkAuth,
  };
});
