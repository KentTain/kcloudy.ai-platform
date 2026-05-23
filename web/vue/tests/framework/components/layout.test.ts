import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { SidebarProvider, Sidebar } from "@/components/ui/sidebar";
import AppNavbar from "@/framework/layouts/components/AppNavbar.vue";
import AppMain from "@/framework/layouts/components/AppMain.vue";
import AppNavMain from "@/framework/layouts/components/AppNavMain.vue";

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

  describe("AppNavMain", () => {
    it("renders correctly", () => {
      const wrapper = mount(
        {
          components: { SidebarProvider, Sidebar, AppNavMain },
          template: `
            <SidebarProvider>
              <Sidebar>
                <AppNavMain />
              </Sidebar>
            </SidebarProvider>
          `,
        },
        {
          global: {
            plugins: [createPinia()],
          },
        }
      );

      expect(wrapper.find("[data-slot='sidebar-group']").exists()).toBe(true);
    });

    it("renders default menu items", () => {
      const wrapper = mount(
        {
          components: { SidebarProvider, Sidebar, AppNavMain },
          template: `
            <SidebarProvider>
              <Sidebar>
                <AppNavMain />
              </Sidebar>
            </SidebarProvider>
          `,
        },
        {
          global: {
            plugins: [createPinia()],
          },
        }
      );

      expect(wrapper.text()).toContain("首页");
      expect(wrapper.text()).toContain("健康检查");
      expect(wrapper.text()).toContain("知识库");
    });

    it("renders grouped menu items", () => {
      const wrapper = mount(
        {
          components: { SidebarProvider, Sidebar, AppNavMain },
          template: `
            <SidebarProvider>
              <Sidebar>
                <AppNavMain />
              </Sidebar>
            </SidebarProvider>
          `,
        },
        {
          global: {
            plugins: [createPinia()],
          },
        }
      );

      expect(wrapper.text()).toContain("系统管理");
    });
  });

  describe("AppNavbar", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppNavbar, {
        global: {
          plugins: [createPinia()],
          stubs: {
            SidebarTrigger: true,
            Separator: true,
          },
        },
      });

      expect(wrapper.find("header").exists()).toBe(true);
    });

    it("renders breadcrumbs", () => {
      const wrapper = mount(AppNavbar, {
        global: {
          plugins: [createPinia()],
          stubs: {
            SidebarTrigger: true,
            Separator: true,
          },
        },
      });

      expect(wrapper.text()).toContain("首页");
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
});
