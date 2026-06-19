import { beforeEach, describe, expect, it, vi } from "vitest";
import { EventBus, ModuleEvents } from "@/framework/events";

describe("EventBus", () => {
  let eventBus: EventBus;

  beforeEach(() => {
    eventBus = new EventBus();
  });

  describe("on", () => {
    it("订阅事件并返回取消订阅函数", () => {
      const handler = vi.fn();
      const unsubscribe = eventBus.on("test", handler);

      expect(typeof unsubscribe).toBe("function");
    });

    it("调用取消订阅函数后不再触发", () => {
      const handler = vi.fn();
      const unsubscribe = eventBus.on("test", handler);

      unsubscribe();
      eventBus.emit("test", "payload");

      expect(handler).not.toHaveBeenCalled();
    });
  });

  describe("emit", () => {
    it("发布事件触发订阅者回调", () => {
      const handler = vi.fn();
      eventBus.on("test", handler);

      eventBus.emit("test", "payload");

      expect(handler).toHaveBeenCalledWith("payload");
    });

    it("同一事件多个订阅者按注册顺序调用", () => {
      const order: string[] = [];
      const handler1 = vi.fn(() => order.push("first"));
      const handler2 = vi.fn(() => order.push("second"));

      eventBus.on("test", handler1);
      eventBus.on("test", handler2);
      eventBus.emit("test");

      expect(order).toEqual(["first", "second"]);
    });

    it("无订阅者时发布事件不报错", () => {
      expect(() => eventBus.emit("nonexistent", "payload")).not.toThrow();
    });
  });

  describe("off", () => {
    it("取消订阅后不再触发", () => {
      const handler = vi.fn();
      eventBus.on("test", handler);

      eventBus.off("test", handler);
      eventBus.emit("test", "payload");

      expect(handler).not.toHaveBeenCalled();
    });

    it("只取消指定订阅者", () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();

      eventBus.on("test", handler1);
      eventBus.on("test", handler2);
      eventBus.off("test", handler1);
      eventBus.emit("test");

      expect(handler1).not.toHaveBeenCalled();
      expect(handler2).toHaveBeenCalled();
    });
  });
});

describe("ModuleEvents", () => {
  it("定义 USER_LOGGED_IN 事件", () => {
    expect(ModuleEvents.USER_LOGGED_IN).toBe("user:logged-in");
  });

  it("定义 USER_LOGGED_OUT 事件", () => {
    expect(ModuleEvents.USER_LOGGED_OUT).toBe("user:logged-out");
  });

  it("定义 TENANT_CHANGED 事件", () => {
    expect(ModuleEvents.TENANT_CHANGED).toBe("tenant:changed");
  });

  it("定义 MODULE_LOADED 事件", () => {
    expect(ModuleEvents.MODULE_LOADED).toBe("module:loaded");
  });

  it("定义 MODULE_ERROR 事件", () => {
    expect(ModuleEvents.MODULE_ERROR).toBe("module:error");
  });

  it("定义 DATA_REFRESH_REQUESTED 事件", () => {
    expect(ModuleEvents.DATA_REFRESH_REQUESTED).toBe("data:refresh-requested");
  });
});
