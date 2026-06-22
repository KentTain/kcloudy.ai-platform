import type { ModuleDescriptor } from "@/framework/module/types";

/**
 * Tenant 模块描述符
 *
 * 注意：租户管理功能仅供超级管理员使用，路由通过 adminRoutes 直接注册，
 * 不通过模块系统注册到普通用户界面。
 */
export const tenantModule: ModuleDescriptor = {
  name: "tenant",
  version: "1.0.0",
  getRoutes: () => [],
  icon: "building",
};

export * from "./api/tenant";
export * from "./types";
