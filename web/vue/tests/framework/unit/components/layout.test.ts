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

// Mock useMenuStore
const mockMenuStore = {
  userMenus: [
    {
      id: "1",
      code: "home",
      name: "首页",
      icon: "Home",
      path: "/",
      sortOrder: 0,
      children: [],
    },
    {
      id: "2",
      code: "system",
      name: "系统管理",
      icon: "Settings",
      path: null,
      sortOrder: 1,
      children: [
        {
          id: "2-1",
          code: "system.health",
          name: "健康检查",
          icon: "Activity",
          path: "/system/health",
          sortOrder: 0,
          children: [],
        },
        {
          id: "2-2",
          code: "system.knowledge",
          name: "知识库",
          icon: "Database",
          path: "/system/knowledge",
          sortOrder: 1,
          children: [],
        },
      ],
    },
  ],
  loading: false,
  error: null,
  fetchUserMenus: vi.fn(),
};

vi.mock("@/framework/stores/menu", () => ({
  useMenuStore: () => mockMenuStore,
}));

// Mock useUserStore
vi.mock("@/framework/stores/user", () => ({
  useUserStore: () => ({
    userInfo: {
      permissions: [],
    },
  }),
}));

// Mock sidebar components and useSidebar
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
  SidebarProvider: {
    name: "SidebarProvider",
    template: '<div class="sidebar-provider"><slot /></div>',
  },
  Sidebar: {
    name: "Sidebar",
    template: '<div class="sidebar" data-slot="sidebar"><slot /></div>',
  },
  SidebarTrigger: {
    name: "SidebarTrigger",
    template: '<button class="sidebar-trigger">Toggle</button>',
  },
  SidebarGroup: {
    name: "SidebarGroup",
    template: '<div class="sidebar-group" data-slot="sidebar-group"><slot /></div>',
  },
  SidebarGroupContent: {
    name: "SidebarGroupContent",
    template: '<div class="sidebar-group-content"><slot /></div>',
  },
  SidebarGroupLabel: {
    name: "SidebarGroupLabel",
    template: '<div class="sidebar-group-label"><slot /></div>',
  },
  SidebarMenu: {
    name: "SidebarMenu",
    template: '<ul class="sidebar-menu"><slot /></ul>',
  },
  SidebarMenuItem: {
    name: "SidebarMenuItem",
    template: '<li class="sidebar-menu-item"><slot /></li>',
  },
  SidebarMenuButton: {
    name: "SidebarMenuButton",
    template: '<button class="sidebar-menu-button"><slot /></button>',
    props: ["tooltip", "isActive"],
  },
  SidebarMenuSub: {
    name: "SidebarMenuSub",
    template: '<ul class="sidebar-menu-sub"><slot /></ul>',
  },
  SidebarMenuSubItem: {
    name: "SidebarMenuSubItem",
    template: '<li class="sidebar-menu-sub-item"><slot /></li>',
  },
  SidebarMenuSubButton: {
    name: "SidebarMenuSubButton",
    template: '<button class="sidebar-menu-sub-button"><slot /></button>',
    props: ["isActive"],
  },
}));

// Mock Separator
vi.mock("@/components/ui/separator", () => ({
  Separator: {
    name: "Separator",
    template: '<div class="separator"></div>',
    props: ["orientation", "class"],
  },
}));

// Mock collapsible components
vi.mock("@/components/ui/collapsible", () => ({
  Collapsible: {
    name: "Collapsible",
    template: '<div class="collapsible" :data-state="open ? \'open\' : \'closed\'"><slot /></div>',
    props: ["open"],
  },
  CollapsibleContent: {
    name: "CollapsibleContent",
    template: '<div class="collapsible-content"><slot /></div>',
  },
  CollapsibleTrigger: {
    name: "CollapsibleTrigger",
    template: '<div class="collapsible-trigger"><slot /></div>',
  },
}));

// Mock Lucide icons
vi.mock("@lucide/vue", () => ({
  ChevronRight: { name: "ChevronRight", template: "<span>chevron</span>" },
  Home: { name: "Home", template: "<span>home-icon</span>" },
  Activity: { name: "Activity", template: "<span>activity-icon</span>" },
  Database: { name: "Database", template: "<span>database-icon</span>" },
  Settings: { name: "Settings", template: "<span>settings-icon</span>" },
  Users: { name: "Users", template: "<span>users-icon</span>" },
  Shield: { name: "Shield", template: "<span>shield-icon</span>" },
  Badge: { name: "Badge", template: "<span>badge-icon</span>" },
  Building: { name: "Building", template: "<span>building-icon</span>" },
  Key: { name: "Key", template: "<span>key-icon</span>" },
  Package: { name: "Package", template: "<span>package-icon</span>" },
  Puzzle: { name: "Puzzle", template: "<span>puzzle-icon</span>" },
  SearchIcon: { name: "SearchIcon", template: "<span>search-icon</span>" },
  ClipboardCheckIcon: { name: "ClipboardCheckIcon", template: "<span>clipboard-icon</span>" },
  BellIcon: { name: "BellIcon", template: "<span>bell-icon</span>" },
}));

describe("Layout Components", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("AppNavMain", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.find(".sidebar-group").exists()).toBe(true);
    });

    it("renders default menu items", () => {
      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.text()).toContain("首页");
      expect(wrapper.text()).toContain("健康检查");
      expect(wrapper.text()).toContain("知识库");
    });

    it("renders grouped menu items", () => {
      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.text()).toContain("系统管理");
    });
  });

  describe("AppNavbar", () => {
    it("renders correctly", () => {
      const wrapper = mount(AppNavbar, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.find("header").exists()).toBe(true);
    });

    it("renders breadcrumbs", () => {
      const wrapper = mount(AppNavbar, {
        global: {
          plugins: [createPinia()],
        },
      });

      expect(wrapper.exists()).toBe(true);
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
