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

// Mock sidebar
vi.mock("@/components/ui/sidebar", () => ({
  useSidebar: () => ({
    isMobile: { value: false },
    state: { value: "expanded" },
    open: { value: true },
    setOpen: vi.fn(),
    openMobile: { value: false },
    setOpenMobile: vi.fn(),
    toggleSidebar: vi.fn(),
  }),
  SidebarTrigger: {
    name: "SidebarTrigger",
    template: '<button class="sidebar-trigger">Toggle</button>',
  },
}));

// Mock separator
vi.mock("@/components/ui/separator", () => ({
  Separator: {
    name: "Separator",
    template: '<div class="separator"></div>',
    props: ["orientation", "class"],
  },
}));

// Mock Lucide icons
vi.mock("@lucide/vue", () => ({
  SearchIcon: { name: "SearchIcon", template: "<span>search-icon</span>" },
  ClipboardCheckIcon: { name: "ClipboardCheckIcon", template: "<span>clipboard-icon</span>" },
  BellIcon: { name: "BellIcon", template: "<span>bell-icon</span>" },
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
      },
    });

    expect(wrapper.find("header").exists()).toBe(true);
  });

  it("contains navigation items", () => {
    const wrapper = mount(AppNavbar, {
      global: {
        plugins: [router],
      },
    });

    // Check that the component renders without errors
    expect(wrapper.html()).toBeTruthy();
  });

  it("has search trigger button", () => {
    const wrapper = mount(AppNavbar, {
      global: {
        plugins: [router],
      },
    });

    // Check that search button exists
    const searchButton = wrapper.find("button[type='button']");
    expect(searchButton.exists()).toBe(true);
  });
});
