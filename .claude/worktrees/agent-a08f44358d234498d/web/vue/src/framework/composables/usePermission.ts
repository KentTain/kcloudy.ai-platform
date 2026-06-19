import { useUserStore } from "@/framework/stores";

/**
 * 权限检查 composable
 */
export function usePermission() {
  const userStore = useUserStore();

  /**
   * 检查用户是否拥有指定权限
   */
  const hasPermission = (permission: string): boolean => {
    return userStore.hasPermission(permission);
  };

  /**
   * 检查用户是否拥有任一权限
   */
  const hasAnyPermission = (permissions: string[]): boolean => {
    return permissions.some((perm) => userStore.hasPermission(perm));
  };

  /**
   * 检查用户是否拥有全部权限
   */
  const hasAllPermissions = (permissions: string[]): boolean => {
    return permissions.every((perm) => userStore.hasPermission(perm));
  };

  /**
   * 检查用户是否拥有指定角色
   */
  const hasRole = (role: string): boolean => {
    return userStore.hasRole(role);
  };

  /**
   * 检查用户是否拥有任一角色
   */
  const hasAnyRole = (roles: string[]): boolean => {
    return roles.some((r) => userStore.hasRole(r));
  };

  /**
   * 检查用户是否拥有全部角色
   */
  const hasAllRoles = (roles: string[]): boolean => {
    return roles.every((r) => userStore.hasRole(r));
  };

  return {
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    hasRole,
    hasAnyRole,
    hasAllRoles,
  };
}
