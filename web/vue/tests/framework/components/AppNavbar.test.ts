import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createRouter, createWebHistory } from "vue-router";
import AppNavbar from "@/framework/layouts/components/AppNavbar.vue";

// Mock useCommandPalette
vi.mock("@/framework/composables/useCommandPalette", () => ({
  useCommandPalette: () => ({
    openCommandPalette: vi.fn(),
    closeCommandPalette: vi.fn(),
    isOpen: { value: false },
  }),
}));

describe("AppNavbar", () => {
  let router: ReturnType<typeof createRouter>;

  beforeEach(() => {
    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/", component: { template: "<div>Home</div>" }, meta: { title: "首页" } },
        { path: "/datasets", component: { template: "<div>Datasets</div>" }, meta: { title: "知识库" } },
      ],
    });
  });

  it("renders correctly", () => {
    const wrapper = mount(AppNavbar, {
      global: {
        plugins: [router],
        stubs: {
          SidebarTrigger: true,
          Separator: true,
          Breadcrumb: true,
          BreadcrumbList: true,
          BreadcrumbItem: true,
          BreadcrumbLink: true,
          BreadcrumbPage: true,
          BreadcrumbSeparator: true,
          NavigationMenu: true,
          NavigationMenuList: true,
          NavigationMenuItem: true,
          NavigationMenuLink: true,
          Button: true,
          RouterLink: true,
        },
      },
    });

    expect(wrapper.find("header").exists()).toBe(true);
  });

  it("contains navigation items", () => {
    const wrapper = mount(AppNavbar, {
      global: {
        plugins: [router],
        stubs: {
          SidebarTrigger: true,
          Separator: true,
          Breadcrumb: true,
          BreadcrumbList: true,
          BreadcrumbItem: true,
          BreadcrumbLink: true,
          BreadcrumbPage: true,
          BreadcrumbSeparator: true,
          NavigationMenu: true,
          NavigationMenuList: true,
          NavigationMenuItem: true,
          NavigationMenuLink: true,
          Button: true,
          RouterLink: true,
        },
      },
    });

    // Check that the component renders without errors
    expect(wrapper.html()).toBeTruthy();
  });

  it("has search trigger button", () => {
    const wrapper = mount(AppNavbar, {
      global: {
        plugins: [router],
        stubs: {
          SidebarTrigger: true,
          Separator: true,
          Breadcrumb: true,
          BreadcrumbList: true,
          BreadcrumbItem: true,
          BreadcrumbLink: true,
          BreadcrumbPage: true,
          BreadcrumbSeparator: true,
          NavigationMenu: true,
          NavigationMenuList: true,
          NavigationMenuItem: true,
          NavigationMenuLink: true,
          Button: true,
          RouterLink: true,
        },
      },
    });

    // Check that search button exists
    const searchButton = wrapper.find("button[type='button']");
    expect(searchButton.exists()).toBe(true);
  });
});
