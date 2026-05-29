import type { App } from "vue";
import type { Router } from "vue-router";
import type { Pinia } from "pinia";
import type { ModuleDescriptor } from "./types";
import { ModuleRegistry } from "./registry";
import { EventBus, ModuleEvents, getEventBus } from "@/framework/events";

/**
 * 框架设置选项
 */
export interface SetupFrameworkOptions {
  app: App;
  router: Router;
  pinia: Pinia;
  modules: ModuleDescriptor[];
}

/**
 * 全局模块注册中心实例
 */
let globalRegistry: ModuleRegistry | null = null;

/**
 * 获取全局模块注册中心
 */
export function getModuleRegistry(): ModuleRegistry {
  if (!globalRegistry) {
    throw new Error("Framework not initialized. Call setupFramework first.");
  }
  return globalRegistry;
}

// Re-export getEventBus from events module
export { getEventBus } from "@/framework/events";

/**
 * 设置框架
 * 注册模块并配置路由
 */
export async function setupFramework(options: SetupFrameworkOptions): Promise<void> {
  const { app, router, pinia, modules } = options;

  // 初始化全局实例
  globalRegistry = new ModuleRegistry();
  const eventBus = getEventBus();

  // 注册所有模块
  for (const module of modules) {
    try {
      globalRegistry.register(module);

      // 调用模块的 setup 函数
      if (module.setup) {
        await module.setup(app, pinia);
      }

      // 发出模块加载完成事件
      eventBus.emit(ModuleEvents.MODULE_LOADED, { name: module.name });
    } catch (error) {
      console.error(`[setupFramework] Failed to register module '${module.name}':`, error);
      eventBus.emit(ModuleEvents.MODULE_ERROR, {
        name: module.name,
        error,
      });
      throw error;
    }
  }

  // 收集并注册路由
  const moduleRoutes = globalRegistry.getRoutes();
  registerRoutes(router, moduleRoutes);
}

/**
 * 动态注册路由
 */
function registerRoutes(router: Router, routes: ReturnType<ModuleDescriptor["getRoutes"]>): void {
  // 找到 AdminLayout 父路由（path: '/'）
  const rootRoute = router
    .getRoutes()
    .find((r) => r.path === "/" && r.children?.length);

  if (rootRoute) {
    // 将模块路由添加到 rootRoute 的 children
    for (const route of routes) {
      router.addRoute(rootRoute.name!, route);
    }
  } else {
    // 如果没有找到 rootRoute，直接添加到根路由
    for (const route of routes) {
      router.addRoute(route);
    }
  }

  if (import.meta.env?.DEV) {
    console.log(
      "[setupFramework] Registered routes:",
      routes.map((r) => r.path)
    );
  }
}
