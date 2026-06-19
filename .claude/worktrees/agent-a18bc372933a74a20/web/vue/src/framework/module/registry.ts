import type { RouteRecordRaw } from "vue-router";
import { isModuleDescriptor, type MenuItem, type ModuleDescriptor } from "./types";

/**
 * 模块注册中心
 * 管理模块的注册、查询和路由收集
 */
export class ModuleRegistry {
  private modules: Map<string, ModuleDescriptor> = new Map();

  /**
   * 注册模块
   * @param module 模块描述符
   * @throws {TypeError} 模块描述符无效
   * @throws {Error} 模块已注册或依赖不满足
   */
  register(module: unknown): void {
    if (!isModuleDescriptor(module)) {
      throw new TypeError("Invalid module descriptor");
    }

    if (this.modules.has(module.name)) {
      throw new Error(`Module '${module.name}' is already registered`);
    }

    this.validateDependencies(module);

    this.modules.set(module.name, module);
    console.log(`[ModuleRegistry] Module registered: ${module.name}@${module.version}`);
  }

  /**
   * 验证模块依赖
   * @param module 模块描述符
   * @throws {Error} 依赖不满足
   */
  private validateDependencies(module: ModuleDescriptor): void {
    const dependencies = module.dependencies || [];
    for (const dep of dependencies) {
      if (!this.modules.has(dep)) {
        throw new Error(
          `Module '${module.name}' depends on '${dep}' which is not registered`
        );
      }
    }
  }

  /**
   * 收集所有已注册模块的路由
   * @returns 合并后的路由数组
   */
  getRoutes(): RouteRecordRaw[] {
    const routes: RouteRecordRaw[] = [];
    for (const module of this.modules.values()) {
      routes.push(...module.getRoutes());
    }
    return routes;
  }

  /**
   * 收集所有已注册模块的菜单项
   * @returns 合并后的菜单项数组
   */
  getMenuItems(): MenuItem[] {
    const items: MenuItem[] = [];
    for (const module of this.modules.values()) {
      if (module.getMenuItems) {
        items.push(...module.getMenuItems());
      }
    }
    return items;
  }

  /**
   * 根据名称获取模块
   * @param name 模块名称
   * @returns 模块描述符或 undefined
   */
  getModule(name: string): ModuleDescriptor | undefined {
    return this.modules.get(name);
  }
}
