import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import AppSidebar from "@/framework/layouts/components/AppSidebar.vue";
import AppNavbar from "@/framework/layouts/components/AppNavbar.vue";
import AppMain from "@/framework/layouts/components/AppMain.vue";
import AppTagsView from "@/framework/layouts/components/AppTagsView.vue";
import { useTagsViewStore } from "@/framework/stores";

// Mock vue-router
vi.mock("vue-router", () => ({
  useRoute: () => ({
    path: "/",
    matched: [{ path: "/", meta: { title: "首页" } }],
    meta: { title: "首页" },
  }),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("Layout Components", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("AppSidebar", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppSidebar, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.find(".app-sidebar").exists()).toBe(true);
      expect(wrapper.text()).toContain("AI 助手平台");
    });

    it("renders default menu items", () => {
      const wrapper = mount(AppSidebar, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.text()).toContain("首页");
      expect(wrapper.text()).toContain("健康检查");
      expect(wrapper.text()).toContain("知识库");
    });
  });

  describe("AppNavbar", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppNavbar, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.find(".app-navbar").exists()).toBe(true);
    });

    it("renders user avatar", () => {
      const wrapper = mount(AppNavbar, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.find(".app-navbar__avatar").exists()).toBe(true);
    });
  });

  describe("AppMain", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppMain, {
        global: {
          plugins: [createPinia()],
          stubs: {
            "router-view": true,
          },
        },
      });

      expect(wrapper.find(".app-main").exists()).toBe(true);
    });
  });

  describe("AppTagsView", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppTagsView, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.find(".app-tagsview").exists()).toBe(true);
    });

    it("displays tags from store", () => {
      const pinia = createPinia();
      setActivePinia(pinia);

      // 直接操作 store 添加标签
      const tagsViewStore = useTagsViewStore();
      tagsViewStore.addTag({
        path: "/",
        meta: { title: "首页" },
      } as any);

      const wrapper = mount(AppTagsView, {
        global: {
          plugins: [pinia],
        },
      });

      expect(wrapper.text()).toContain("首页");
    });
  });
});
