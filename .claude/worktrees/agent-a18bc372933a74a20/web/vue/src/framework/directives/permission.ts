import type { Directive, DirectiveBinding } from "vue";
import { usePermissionStore } from "@/framework/stores";

/**
 * v-permission 权限指令
 * 用法: v-permission="['user:add', 'user:edit']"
 */
export const permissionDirective: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding<string | string[]>) {
    const permissionStore = usePermissionStore();
    const permissions = Array.isArray(binding.value) ? binding.value : [binding.value];

    const hasPermission = permissionStore.hasPermission(permissions);

    if (!hasPermission) {
      el.parentNode?.removeChild(el);
    }
  },
};

/**
 * 注册权限指令
 */
export const setupPermissionDirective = (app: import("vue").App) => {
  app.directive("permission", permissionDirective);
};

export default permissionDirective;
