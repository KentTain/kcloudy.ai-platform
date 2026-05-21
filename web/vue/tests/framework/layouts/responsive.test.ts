import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { nextTick } from "vue";
import AdminLayout from "@/framework/layouts/AdminLayout.vue";
import { useAppStore } from "@/framework/stores/app";

vi.mock("vue-router", () => ({
  useRoute: () => ({
    path: "/",
    matched: [{ path: "/", meta: { title: "首页" } }],
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

const layoutStubs = {
  AppSidebar: { template: '<div class="app-sidebar-stub" />' },
  AppNavbar: { template: '<div class="app-navbar-stub" />' },
  AppTagsView: { template: '<div class="app-tagsview-stub" />' },
  AppMain: { template: '<div class="app-main-stub" />' },
};

describe("AdminLayout responsive", () => {
  let innerWidth = 1280;

  beforeEach(() => {
    setActivePinia(createPinia());
    innerWidth = 1280;
    vi.stubGlobal(
      "innerWidth",
      new Proxy(
        {},
        {
          get: () => innerWidth,
        }
      )
    );
    Object.defineProperty(window, "innerWidth", {
      configurable: true,
      get: () => innerWidth,
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("视口宽度小于 768px 时自动折叠侧边栏", async () => {
    innerWidth = 500;
    const pinia = createPinia();
    const store = useAppStore(pinia);

    mount(AdminLayout, {
      global: {
        plugins: [pinia],
        stubs: layoutStubs,
      },
    });

    await nextTick();
    expect(store.device).toBe("mobile");
    expect(store.sidebarCollapsed).toBe(true);
  });

  it("视口宽度大于等于 768px 时使用桌面布局", async () => {
    innerWidth = 1024;
    const pinia = createPinia();
    const store = useAppStore(pinia);
    store.setSidebarCollapsed(true);

    mount(AdminLayout, {
      global: {
        plugins: [pinia],
        stubs: layoutStubs,
      },
    });

    await nextTick();
    expect(store.device).toBe("desktop");
  });

  it("resize 时根据视口更新设备类型", async () => {
    innerWidth = 1024;
    const pinia = createPinia();
    const store = useAppStore(pinia);

    mount(AdminLayout, {
      global: {
        plugins: [pinia],
        stubs: layoutStubs,
      },
    });

    await nextTick();
    expect(store.device).toBe("desktop");

    innerWidth = 600;
    window.dispatchEvent(new Event("resize"));
    await nextTick();

    expect(store.device).toBe("mobile");
    expect(store.sidebarCollapsed).toBe(true);
  });
});
