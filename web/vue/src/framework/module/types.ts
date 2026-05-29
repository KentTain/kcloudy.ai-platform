import type { RouteRecordRaw } from "vue-router";
import type { App } from "vue";
import type { Pinia } from "pinia";

/** 模块名称格式正则：小写字母、数字、连字符 */
const MODULE_NAME_REGEX = /^[a-z0-9-]+$/;

/**
 * 模块描述符接口
 * 定义前端模块的标准结构
 */
export interface ModuleDescriptor {
  /** 模块名称，小写字母、数字、连字符 */
  name: string;
  /** 模块版本，遵循 semver 格式 */
  version: string;
  /** 返回模块路由配置 */
  getRoutes: () => RouteRecordRaw[];
  /** 依赖的其他模块名称 */
  dependencies?: string[];
  /** 模块图标标识 */
  icon?: string;
  /** 返回菜单项数组 */
  getMenuItems?: () => MenuItem[];
  /** 返回 Store 对象 */
  getStores?: () => Record<string, unknown>;
  /** 模块初始化函数 */
  setup?: (app: App, pinia: Pinia) => void | Promise<void>;
}

/**
 * 菜单项接口
 */
export interface MenuItem {
  title: string;
  path?: string;
  icon?: string;
  children?: MenuItem[];
}

/**
 * 类型守卫函数，验证对象是否为有效的 ModuleDescriptor
 * @param value 待验证的值
 * @returns 是否为有效的 ModuleDescriptor
 */
export function isModuleDescriptor(value: unknown): value is ModuleDescriptor {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value !== "object" || Array.isArray(value)) {
    return false;
  }

  const obj = value as Record<string, unknown>;

  return (
    typeof obj.name === "string" &&
    MODULE_NAME_REGEX.test(obj.name) &&
    typeof obj.version === "string" &&
    typeof obj.getRoutes === "function"
  );
}
