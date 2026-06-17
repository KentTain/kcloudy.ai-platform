import type { App } from "vue";
import type { Router } from "vue-router";
import type { Pinia } from "pinia";
import type { ModuleDescriptor } from "./types";
import { ModuleRegistry } from "./registry";
import { ModuleEvents, getEventBus } from "@/framework/events";

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
 * 动态路由是否已准备好
 * 用于刷新页面时判断路由是否已注册
 */
let dynamicRoutesReady = false;

/**
 * 动态路由准备完成的 Promise resolve 函数
 */
let dynamicRoutesReadyResolve: (() => void) | null = null;

/**
 * 动态路由准备完成的 Promise
 */
let dynamicRoutesReadyPromise: Promise<void> | null = null;

/**
 * 检查动态路由是否已准备好
 */
export function isDynamicRoutesReady(): boolean {
  return dynamicRoutesReady;
}

/**
 * 等待动态路由准备好
 * 用于路由守卫中等待路由注册完成
 */
export function waitForDynamicRoutes(): Promise<void> {
  if (dynamicRoutesReady) {
    return Promise.resolve();
  }

  // 如果还没有创建 Promise，创建一个
  if (!dynamicRoutesReadyPromise) {
    dynamicRoutesReadyPromise = new Promise<void>((resolve) => {
      dynamicRoutesReadyResolve = resolve;
    });
  }

  return dynamicRoutesReadyPromise;
}

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

  console.log("[setupFramework] Starting with modules:", modules.map(m => m.name));

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
  console.log("[setupFramework] Module routes to register:", moduleRoutes.map(r => r.path));
  registerRoutes(router, moduleRoutes);

  // 标记动态路由已准备好
  dynamicRoutesReady = true;
  console.log("[setupFramework] Dynamic routes ready");

  // resolve 等待中的 Promise
  if (dynamicRoutesReadyResolve) {
    dynamicRoutesReadyResolve();
  }
}

/**
 * 动态注册路由
 */
function registerRoutes(router: Router, routes: ReturnType<ModuleDescriptor["getRoutes"]>): void {
  // 找到 AdminLayout 父路由（path: '/'）
  // 注意：刚添加的路由 children 可能是空数组，不能用 .length 判断
  const allRoutes = router.getRoutes();
  console.log("[registerRoutes] All routes before registration:", allRoutes.map(r => ({ name: r.name, path: r.path, hasChildren: !!r.children?.length })));

  const rootRoute = allRoutes.find((r) => r.path === "/" && r.name === "Root");

  console.log("[registerRoutes] Found rootRoute:", rootRoute ? { name: rootRoute.name, path: rootRoute.path } : null);

  if (rootRoute) {
    // 将模块路由添加到 rootRoute 的 children
    for (const route of routes) {
      console.log("[registerRoutes] Adding route to Root:", route.path, "as child of", rootRoute.name);
      router.addRoute(rootRoute.name!, route);
    }
  } else {
    // 如果没有找到 rootRoute，直接添加到根路由
    console.log("[registerRoutes] No Root found, adding routes directly");
    for (const route of routes) {
      router.addRoute(route);
    }
  }

  console.log("[registerRoutes] All routes after registration:", router.getRoutes().map(r => ({ name: r.name, path: r.path })));
}
