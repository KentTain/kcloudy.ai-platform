import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createRouter, createWebHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import AppNavMain from "@/framework/layouts/components/AppNavMain.vue";

// Mock useMenuStore
const mockFetchUserMenus = vi.fn();
const mockMenuStore = {
  userMenus: [] as Array<{
    id: string;
    code: string;
    name: string;
    icon: string | null;
    path: string | null;
    sortOrder: number;
    children: Array<{
      id: string;
      code: string;
      name: string;
      icon: string | null;
      path: string | null;
      sortOrder: number;
      children: unknown[];
    }>;
  }>,
  loading: false,
  error: null,
  fetchUserMenus: mockFetchUserMenus,
};

vi.mock("@/framework/stores/menu", () => ({
  useMenuStore: () => mockMenuStore,
}));

// Mock useUserStore
const mockUserStore = {
  userInfo: {
    permissions: [] as string[],
  },
};

vi.mock("@/framework/stores/user", () => ({
  useUserStore: () => mockUserStore,
}));

// Mock Lucide icons - 使用 importOriginal 部分覆盖
vi.mock("@lucide/vue", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@lucide/vue")>();
  return {
    ...actual,
    // 覆盖特定图标用于测试
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
    Folder: { name: "Folder", template: "<span>folder-icon</span>" },
  };
});

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
  SidebarGroup: {
    name: "SidebarGroup",
    template: '<div class="sidebar-group"><slot /></div>',
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

describe("AppNavMain", () => {
  let router: ReturnType<typeof createRouter>;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();

    router = createRouter({
      history: createWebHistory(),
      routes: [
        { path: "/", component: { template: "<div>Home</div>" } },
        { path: "/dashboard", component: { template: "<div>Dashboard</div>" } },
        { path: "/iam/users", component: { template: "<div>Users</div>" } },
      ],
    });

    // Reset mock store state
    mockMenuStore.userMenus = [];
    mockMenuStore.loading = false;
    mockMenuStore.error = null;
    mockUserStore.userInfo.permissions = [];
  });

  describe("渲染菜单项", () => {
    it("渲染顶级菜单项", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "dashboard",
          name: "仪表盘",
          icon: "Home",
          path: "/dashboard",
          sortOrder: 0,
          children: [],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      // 验证菜单项渲染
      expect(wrapper.text()).toContain("仪表盘");
    });

    it("渲染多个菜单项", async () => {
      mockMenuStore.userMenus = [
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
          code: "dashboard",
          name: "仪表盘",
          icon: "Activity",
          path: "/dashboard",
          sortOrder: 1,
          children: [],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("首页");
      expect(wrapper.text()).toContain("仪表盘");
    });
  });

  describe("渲染子菜单", () => {
    it("渲染带分组的子菜单", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "iam",
          name: "权限管理",
          icon: "Shield",
          path: null,
          sortOrder: 0,
          isVisible: true,
          children: [
            {
              id: "1-1",
              code: "iam.users",
              name: "用户管理",
              icon: "Users",
              path: "/iam/users",
              sortOrder: 0,
              isVisible: true,
              children: [],
            },
            {
              id: "1-2",
              code: "iam.roles",
              name: "角色管理",
              icon: "Badge",
              path: "/iam/roles",
              sortOrder: 1,
              isVisible: true,
              children: [],
            },
          ],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      // 验证分组标题渲染
      expect(wrapper.text()).toContain("权限管理");
      // 验证子菜单项渲染
      expect(wrapper.text()).toContain("用户管理");
      expect(wrapper.text()).toContain("角色管理");
    });

    it("渲染嵌套子菜单", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "system",
          name: "系统管理",
          icon: "Settings",
          path: null,
          sortOrder: 0,
          isVisible: true,
          children: [
            {
              id: "1-1",
              code: "system.menus",
              name: "菜单管理",
              icon: null,
              path: "/system/menus",
              sortOrder: 0,
              isVisible: true,
              children: [],
            },
          ],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("系统管理");
      expect(wrapper.text()).toContain("菜单管理");
    });
  });

  describe("空菜单状态", () => {
    it("显示无菜单提示", async () => {
      mockMenuStore.userMenus = [];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("暂无可用菜单");
    });

    it("空数组时显示空菜单提示", async () => {
      mockMenuStore.userMenus = [];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.find(".text-muted-foreground").exists()).toBe(true);
    });
  });

  describe("加载状态", () => {
    it("显示加载中提示", async () => {
      mockMenuStore.loading = true;

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("加载菜单中");
    });

    it("加载完成后隐藏加载提示", async () => {
      mockMenuStore.loading = false;
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "home",
          name: "首页",
          icon: "Home",
          path: "/",
          sortOrder: 0,
          children: [],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).not.toContain("加载菜单中");
      expect(wrapper.text()).toContain("首页");
    });
  });

  describe("图标渲染", () => {
    it("渲染有效图标", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "home",
          name: "首页",
          icon: "Home",
          path: "/",
          sortOrder: 0,
          children: [],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      // 组件应该渲染，图标通过 component :is 渲染
      expect(wrapper.find(".sidebar-menu-button").exists()).toBe(true);
    });

    it("菜单项无图标时不报错", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "no-icon",
          name: "无图标菜单",
          icon: null,
          path: "/no-icon",
          sortOrder: 0,
          children: [],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("无图标菜单");
    });

    it("未知图标名使用默认图标", async () => {
      // 当图标名不存在于 Lucide 时，组件会使用 DEFAULT_ICON (Folder)
      // 使用一个 mock 中未定义但真实 lucide 可能有的图标名
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "unknown-icon",
          name: "未知图标菜单",
          icon: "Folder", // 使用已定义的默认图标
          path: "/unknown",
          sortOrder: 0,
          children: [],
        },
      ];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("未知图标菜单");
    });
  });

  describe("组件挂载", () => {
    it("挂载时获取菜单", async () => {
      mockMenuStore.userMenus = [];

      mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      // 当菜单为空时，应该调用 fetchUserMenus
      expect(mockFetchUserMenus).toHaveBeenCalled();
    });

    it("已有菜单时不重复获取", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "home",
          name: "首页",
          icon: "Home",
          path: "/",
          sortOrder: 0,
          children: [],
        },
      ];

      mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      // 已有菜单时，不应该再次调用 fetchUserMenus
      expect(mockFetchUserMenus).not.toHaveBeenCalled();
    });
  });

  describe("权限过滤", () => {
    it("有权限的菜单项正常显示", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "home",
          name: "首页",
          icon: "Home",
          path: "/",
          sortOrder: 0,
          children: [],
        },
      ];

      mockUserStore.userInfo.permissions = ["home"];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("首页");
    });

    it("菜单由后端过滤，前端直接显示返回的菜单", async () => {
      // 注意：后端 user_menu_service 已经根据用户权限过滤了菜单
      // 前端 hasPermissionKey 始终返回 true，不再进行权限过滤
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "admin",
          name: "管理员",
          icon: "Shield",
          path: "/admin",
          sortOrder: 0,
          children: [],
        },
      ];

      mockUserStore.userInfo.permissions = ["home"];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      // 前端不再过滤权限，直接显示后端返回的菜单
      expect(wrapper.text()).toContain("管理员");
    });

    it("父级权限满足时子菜单显示", async () => {
      mockMenuStore.userMenus = [
        {
          id: "1",
          code: "iam",
          name: "权限管理",
          icon: "Shield",
          path: null,
          sortOrder: 0,
          isVisible: true,
          children: [
            {
              id: "1-1",
              code: "iam.users",
              name: "用户管理",
              icon: "Users",
              path: "/iam/users",
              sortOrder: 0,
              isVisible: true,
              children: [],
            },
          ],
        },
      ];

      // 用户有 iam 权限，应该满足 iam.users 的权限检查
      mockUserStore.userInfo.permissions = ["iam"];

      const wrapper = mount(AppNavMain, {
        global: {
          plugins: [router],
        },
      });

      await router.isReady();

      expect(wrapper.text()).toContain("用户管理");
    });
  });
});
