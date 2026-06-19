import { defineStore } from "pinia";
import { ref, computed } from "vue";

/**
 * 租户信息类型
 */
export interface TenantInfo {
  id: string;
  name: string;
  code: string;
  is_default?: boolean;
}

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
  tenantId?: string;
  tenantName?: string;
  tenantCode?: string;
  tenants?: TenantInfo[];
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

  // 当前租户（从 tenants 列表中获取完整信息，包含 is_default）
  const currentTenant = computed<TenantInfo | null>(() => {
    if (!userInfo.value?.tenantId) return null;
    // 从 tenants 列表中找到当前租户，这样可以保留 is_default 字段
    const tenant = userInfo.value.tenants?.find((t) => t.id === userInfo.value.tenantId);
    if (tenant) {
      return tenant;
    }
    // 如果 tenants 列表中没有找到，使用基本信息
    return {
      id: userInfo.value.tenantId,
      name: userInfo.value.tenantName || "",
      code: userInfo.value.tenantCode || "",
    };
  });

  // 租户列表
  const tenants = computed<TenantInfo[]>(() => userInfo.value?.tenants || []);

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
    currentTenant,
    tenants,
    setToken,
    setUserInfo,
    logout,
    hasPermission,
    hasRole,
  };
});

export default useUserStore;
