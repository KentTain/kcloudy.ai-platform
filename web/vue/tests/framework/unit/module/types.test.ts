import type { RouteRecordRaw } from "vue-router";
import { describe, expect, it } from "vitest";
import { isModuleDescriptor, type ModuleDescriptor } from "@/framework/module/types";

describe("ModuleDescriptor", () => {
  describe("接口定义", () => {
    it("接受合法的模块描述符", () => {
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(module.name).toBe("demo");
      expect(module.version).toBe("1.0.0");
      expect(typeof module.getRoutes).toBe("function");
    });

    it("支持可选字段", () => {
      const module: ModuleDescriptor = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
        dependencies: ["iam"],
        icon: "database",
        getMenuItems: () => [],
        getStores: () => ({}),
        setup: () => {},
      };

      expect(module.dependencies).toEqual(["iam"]);
      expect(module.icon).toBe("database");
      expect(typeof module.getMenuItems).toBe("function");
      expect(typeof module.getStores).toBe("function");
      expect(typeof module.setup).toBe("function");
    });
  });

  describe("isModuleDescriptor 类型守卫", () => {
    it("验证有效描述符返回 true", () => {
      const module = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(true);
    });

    it("验证缺少 name 字段返回 false", () => {
      const module = {
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证缺少 version 字段返回 false", () => {
      const module = {
        name: "demo",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证缺少 getRoutes 字段返回 false", () => {
      const module = {
        name: "demo",
        version: "1.0.0",
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证 getRoutes 不是函数返回 false", () => {
      const module = {
        name: "demo",
        version: "1.0.0",
        getRoutes: "not a function",
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证 null 返回 false", () => {
      expect(isModuleDescriptor(null)).toBe(false);
    });

    it("验证 undefined 返回 false", () => {
      expect(isModuleDescriptor(undefined)).toBe(false);
    });

    it("验证非对象类型返回 false", () => {
      expect(isModuleDescriptor("string")).toBe(false);
      expect(isModuleDescriptor(123)).toBe(false);
      expect(isModuleDescriptor([])).toBe(false);
    });

    it("验证空对象返回 false", () => {
      expect(isModuleDescriptor({})).toBe(false);
    });

    it("验证带可选字段的有效描述符返回 true", () => {
      const module = {
        name: "demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
        dependencies: ["iam"],
        icon: "database",
        getMenuItems: () => [],
        getStores: () => ({}),
        setup: () => {},
      };

      expect(isModuleDescriptor(module)).toBe(true);
    });

    it("验证模块名称包含大写字母返回 false", () => {
      const module = {
        name: "Demo",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证模块名称包含特殊字符返回 false", () => {
      const module = {
        name: "demo-module!",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证模块名称包含空格返回 false", () => {
      const module = {
        name: "demo module",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(false);
    });

    it("验证模块名称使用连字符和小写字母返回 true", () => {
      const module = {
        name: "demo-module-123",
        version: "1.0.0",
        getRoutes: () => [] as RouteRecordRaw[],
      };

      expect(isModuleDescriptor(module)).toBe(true);
    });
  });
});
