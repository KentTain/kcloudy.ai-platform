import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useAppStore } from "@/framework/stores/app";

// Mock window.innerWidth
const mockInnerWidth = (width: number) => {
  Object.defineProperty(window, "innerWidth", {
    configurable: true,
    get: () => width,
  });
};

describe("useAppStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("device 返回正确的设备类型", () => {
    mockInnerWidth(1024);
    const store = useAppStore();
    expect(store.device).toBe("desktop");
  });

  it("device 在移动端视口返回 mobile", () => {
    mockInnerWidth(500);
    const store = useAppStore();
    expect(store.device).toBe("mobile");
  });
});
