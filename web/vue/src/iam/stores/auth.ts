import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { useUserStore } from "@/framework/stores";
import type { UserInfo } from "@/framework/stores/user";
import {
  getCurrentUser as getCurrentUserApi,
  login as loginApi,
  logout as logoutApi,
  refreshToken as refreshTokenApi,
} from "../api/auth";
import { getErrorMessage, notifyError, notifySuccess } from "../utils/feedback";
import type { LoginRequest, LoginResponse, User } from "../types";

/**
 * 将 IAM User 转换为 Framework UserInfo
 */
const convertToUserInfo = (user: User): UserInfo => ({
  id: user.id,
  username: user.username,
  nickname: user.nickname || user.username,
  avatar: user.avatar,
  email: user.email,
  roles: [],
  permissions: [],
});

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

  const login = async (data: LoginRequest) => {
    loading.value = true;
    try {
      const response = await loginApi(data);
      const { access_token, refresh_token } = response.data;
      const expires_at = getExpiresAt(access_token, response.data);

      // 保存 token
      localStorage.setItem("token", access_token);
      localStorage.setItem("refresh_token", refresh_token);
      localStorage.setItem("token_expires_at", String(expires_at));
      userStore.setToken(access_token);

      try {
        const userResponse = await getCurrentUserApi();
        userStore.setUserInfo(convertToUserInfo(userResponse.data));
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
    loading.value = true;
    try {
      await logoutApi();
    } catch (error: any) {
      notifyError(getErrorMessage(error, "登出失败"));
      console.error("logout error:", error);
    } finally {
      userStore.logout();
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      localStorage.removeItem("token_expires_at");
      loading.value = false;
    }
  };

  const refreshToken = async () => {
    const refresh_token = localStorage.getItem("refresh_token");
    if (!refresh_token) {
      throw new Error("No refresh token");
    }

    try {
      const response = await refreshTokenApi(refresh_token);
      const { access_token, refresh_token: new_refresh_token, expires_in } = response.data;

      localStorage.setItem("token", access_token);
      localStorage.setItem("refresh_token", new_refresh_token);
      localStorage.setItem("token_expires_at", String(Date.now() + expires_in * 1000));
      userStore.setToken(access_token);

      return response.data;
    } catch (error: any) {
      notifyError(getErrorMessage(error, "刷新令牌失败"));
      console.error("refreshToken error:", error);
      throw error;
    }
  };

  const isTokenExpired = computed(() => {
    const expires_at = localStorage.getItem("token_expires_at");
    if (!expires_at) return true;
    return Date.now() > Number.parseInt(expires_at, 10);
  });

  return {
    loading,
    login,
    logout,
    refreshToken,
    isTokenExpired,
  };
});
