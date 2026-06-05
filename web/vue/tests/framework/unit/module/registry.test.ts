import type { RouteRecordRaw } from "vue-router";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ModuleRegistry } from "@/framework/module/registry";
import type { ModuleDescriptor } from "@/framework/module/types";

describe("ModuleRegistry", () => {
  let registry: ModuleRegistry;

  beforeEach(() => {
    registry = new ModuleRegistry();
  });

  describe("register", () => {
    it("注册有效模块成功", () => {
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(() => registry.register(module)).not.toThrow();
    });

    it("注册成功后输出日志", () => {
      const consoleSpy = vi.spyOn(console, "log").mockImplementation(() => {});
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      registry.register(module);

      expect(consoleSpy).toHaveBeenCalledWith(
        "[ModuleRegistry] Module registered: demo@1.0.0"
      );
      consoleSpy.mockRestore();
    });

    it("拒绝无效模块抛出 TypeError", () => {
      const invalidModule = {
        name: "demo",
        // 缺少 version 和 getRoutes
      };

      expect(() => registry.register(invalidModule)).toThrow(TypeError);
      expect(() => registry.register(invalidModule)).toThrow(
        "Invalid module descriptor"
      );
    });

    it("拒绝重复注册抛出 Error", () => {
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      registry.register(module);

      const module2: ModuleDescriptor = {
        name: "demo",
        version: "2.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(() => registry.register(module2)).toThrow(Error);
      expect(() => registry.register(module2)).toThrow(
        "Module 'demo' is already registered"
      );
    });
  });

  describe("getRoutes", () => {
    it("收集单个模块路由", () => {
      const routes = [{ path: "/demo", name: "Demo" }] as RouteRecordRaw[];
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => routes,
      };

      registry.register(module);
      const result = registry.getRoutes();

      expect(result).toEqual(routes);
    });

    it("收集多个模块路由", () => {
      const demoRoutes = [{ path: "/demo", name: "Demo" }] as RouteRecordRaw[];
      const iamRoutes = [{ path: "/iam", name: "IAM" }] as RouteRecordRaw[];

      const demoModule: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => demoRoutes,
      };
      const iamModule: ModuleDescriptor = {
        name: "iam",
        version: "1.0.0",
        getRoutes: () => iamRoutes,
      };

      registry.register(demoModule);
      registry.register(iamModule);
      const result = registry.getRoutes();

      expect(result).toEqual([...demoRoutes, ...iamRoutes]);
    });

    it("无注册模块返回空数组", () => {
      expect(registry.getRoutes()).toEqual([]);
    });
  });

  describe("getMenuItems", () => {
    it("收集模块菜单项", () => {
      const menuItems = [{ title: "Demo", path: "/demo" }];
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
        getMenuItems: () => menuItems,
      };

      registry.register(module);
      const result = registry.getMenuItems();

      expect(result).toEqual(menuItems);
    });

    it("模块无菜单项返回空数组", () => {
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      registry.register(module);
      const result = registry.getMenuItems();

      expect(result).toEqual([]);
    });
  });

  describe("getModule", () => {
    it("根据名称获取模块", () => {
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      registry.register(module);
      const result = registry.getModule("demo");

      expect(result).toBe(module);
    });

    it("模块不存在返回 undefined", () => {
      expect(registry.getModule("nonexistent")).toBeUndefined();
    });
  });

  describe("依赖验证", () => {
    it("依赖满足时注册成功", () => {
      const baseModule: ModuleDescriptor = {
        name: "base",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };
      const dependentModule: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
        dependencies: ["base"],
      };

      registry.register(baseModule);
      expect(() => registry.register(dependentModule)).not.toThrow();
    });

    it("依赖不满足时抛出 Error", () => {
      const dependentModule: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
        dependencies: ["nonexistent"],
      };

      expect(() => registry.register(dependentModule)).toThrow(Error);
      expect(() => registry.register(dependentModule)).toThrow(
        "Module 'demo' depends on 'nonexistent' which is not registered"
      );
    });

    it("多个依赖部分不满足时抛出 Error", () => {
      const baseModule: ModuleDescriptor = {
        name: "base",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      registry.register(baseModule);

      const dependentModule: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
        dependencies: ["base", "nonexistent"],
      };

      expect(() => registry.register(dependentModule)).toThrow(
        "Module 'demo' depends on 'nonexistent' which is not registered"
      );
    });
  });
});
