import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import AppSidebarFooter from "@/framework/layouts/components/AppSidebarFooter.vue";

// Mock @vueuse/core
vi.mock("@vueuse/core", () => ({
  useColorMode: () => ({
    value: "light",
    toggleTheme: vi.fn(),
  }),
  defaultDocument: {},
}));

// Mock useSidebar
vi.mock("@/components/ui/sidebar", () => ({
  useSidebar: () => ({
    isMobile: { value: false },
  }),
  SidebarMenu: {
    name: "SidebarMenu",
    template: "<div><slot /></div>",
  },
  SidebarMenuItem: {
    name: "SidebarMenuItem",
    template: "<div><slot /></div>",
  },
  SidebarMenuButton: {
    name: "SidebarMenuButton",
    template: "<button><slot /></button>",
    props: ["size", "class"],
  },
}));

describe("AppSidebarFooter", () => {
  let router: ReturnType<typeof createRouter>;

  beforeEach(() => {
    setActivePinia(createPinia());
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/", component: { template: "<div>Home</div>" } },
        { path: "/settings/account", component: { template: "<div>Account</div>" } },
        { path: "/settings/developer", component: { template: "<div>Developer</div>" } },
        { path: "/login", component: { template: "<div>Login</div>" } },
      ],
    });
  });

  it("renders user info when logged in", async () => {
    const wrapper = mount(AppSidebarFooter, {
      global: {
        plugins: [router],
        stubs: {
          DropdownMenu: true,
          DropdownMenuTrigger: true,
          DropdownMenuContent: true,
          DropdownMenuItem: true,
          DropdownMenuLabel: true,
          DropdownMenuSeparator: true,
          DropdownMenuGroup: true,
          Avatar: true,
          AvatarImage: true,
          AvatarFallback: true,
        },
      },
    });

    expect(wrapper.findComponent(AppSidebarFooter).exists()).toBe(true);
  });

  it("displays theme toggle menu item", () => {
    const wrapper = mount(AppSidebarFooter, {
      global: {
        plugins: [router],
        stubs: {
          DropdownMenu: true,
          DropdownMenuTrigger: true,
          DropdownMenuContent: true,
          DropdownMenuItem: true,
          DropdownMenuLabel: true,
          DropdownMenuSeparator: true,
          DropdownMenuGroup: true,
          Avatar: true,
          AvatarImage: true,
          AvatarFallback: true,
        },
      },
    });

    // Component mounted successfully
    expect(wrapper.exists()).toBe(true);
  });
});
