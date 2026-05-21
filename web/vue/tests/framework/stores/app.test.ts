import { beforeEach, describe, expect, it } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAppStore } from "@/framework/stores/app";

describe("useAppStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("setDevice mobile 时自动折叠侧边栏", () => {
    const store = useAppStore();
    store.setSidebarCollapsed(false);
    store.setDevice("mobile");
    expect(store.device).toBe("mobile");
    expect(store.sidebarCollapsed).toBe(true);
  });

  it("setDevice desktop 时不强制折叠", () => {
    const store = useAppStore();
    store.setSidebarCollapsed(false);
    store.setDevice("desktop");
    expect(store.device).toBe("desktop");
    expect(store.sidebarCollapsed).toBe(false);
  });

  it("toggleSidebar 切换折叠状态", () => {
    const store = useAppStore();
    expect(store.sidebarCollapsed).toBe(false);
    store.toggleSidebar();
    expect(store.sidebarCollapsed).toBe(true);
    store.toggleSidebar();
    expect(store.sidebarCollapsed).toBe(false);
  });
});
