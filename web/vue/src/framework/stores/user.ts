import { defineStore } from "pinia";
import { ref, computed } from "vue";

/**
 * 用户信息类型
 */
export interface UserInfo {
  id: string;
  username: string;
  nickname: string;
  avatar?: string;
  email?: string;
  roles: string[];
  permissions: string[];
}

/**
 * 用户状态管理
 */
export const useUserStore = defineStore("user", () => {
  // 用户信息
  const userInfo = ref<UserInfo | null>(null);

  // Token
  const token = ref<string | null>(localStorage.getItem("token"));

  // 是否登录
  const isLoggedIn = computed(() => !!token.value);

  // 设置 Token
  const setToken = (newToken: string) => {
    token.value = newToken;
    localStorage.setItem("token", newToken);
  };

  // 设置用户信息
  const setUserInfo = (info: UserInfo) => {
    userInfo.value = info;
  };

  // 登出
  const logout = () => {
    token.value = null;
    userInfo.value = null;
    localStorage.removeItem("token");
  };

  // 检查是否有权限
  const hasPermission = (permission: string): boolean => {
    if (!userInfo.value) return false;
    return userInfo.value.permissions.includes(permission);
  };

  // 检查是否有角色
  const hasRole = (role: string): boolean => {
    if (!userInfo.value) return false;
    return userInfo.value.roles.includes(role);
  };

  return {
    userInfo,
    token,
    isLoggedIn,
    setToken,
    setUserInfo,
    logout,
    hasPermission,
    hasRole,
  };
});

export default useUserStore;
