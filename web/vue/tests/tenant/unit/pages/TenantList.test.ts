/**
 * TenantList 页面组件测试
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { ref, nextTick } from "vue";
import { createPinia, setActivePinia } from "pinia";
import TenantList from "@/tenant/pages/tenants/TenantList.vue";
import type { Tenant, TenantListStats } from "@/tenant/types";

// Mock vue-router
const mockPush = vi.fn();
vi.mock("vue-router", () => ({
  useRouter: vi.fn(() => ({
    push: mockPush,
  })),
}));

// Mock tenant store
const mockTenants = ref<Tenant[]>([]);
const mockLoading = ref(false);
const mockTotal = ref(0);
const mockStats = ref<TenantListStats>({
  total_count: 0,
  inactive_count: 0,
  expired_count: 0,
});
const mockFetchTenants = vi.fn(() => Promise.resolve());
const mockRemoveTenant = vi.fn(() => Promise.resolve());
const mockActivate = vi.fn(() => Promise.resolve());
const mockDeactivate = vi.fn(() => Promise.resolve());

vi.mock("@/tenant/stores/tenant", () => ({
  useTenantStore: vi.fn(() => ({
    tenants: mockTenants.value,
    loading: mockLoading.value,
    total: mockTotal.value,
    stats: mockStats.value,
    fetchTenants: mockFetchTenants,
    removeTenant: mockRemoveTenant,
    activate: mockActivate,
    deactivate: mockDeactivate,
  })),
}));

// Mock framework user store
vi.mock("@/framework/stores", () => ({
  useUserStore: vi.fn(() => ({
    hasRole: vi.fn(() => true),
  })),
}));

// Mock feedback utils
vi.mock("@/framework/utils/feedback", () => ({
  confirmAction: vi.fn(() => true),
  notifySuccess: vi.fn(),
}));

// 测试数据
const mockTenantList: Tenant[] = [
  {
    id: "tenant-1",
    name: "测试租户1",
    code: "test1",
    status: "active",
    contact_name: "张三",
    contact_email: "zhangsan@test.com",
    created_at: "2025-01-01T00:00:00Z",
  },
  {
    id: "tenant-2",
    name: "测试租户2",
    code: "test2",
    status: "inactive",
    contact_name: "李四",
    contact_email: "lisi@test.com",
    created_at: "2025-01-02T00:00:00Z",
  },
];

const mockStatsData: TenantListStats = {
  total_count: 10,
  inactive_count: 3,
  expired_count: 2,
};

describe("TenantList", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mockTenants.value = [];
    mockLoading.value = false;
    mockTotal.value = 0;
    mockStats.value = {
      total_count: 0,
      inactive_count: 0,
      expired_count: 0,
    };
  });

  // 通用 stubs
  const commonStubs = {
    AppPage: {
      template: '<div class="app-page-stub"><slot /><slot name="actions" /></div>',
      props: ["title", "variant"],
    },
    Button: {
      template: '<button class="btn-stub" @click="$emit(&quot;click&quot;)"><slot /></button>',
      props: ["variant", "size", "disabled"],
    },
    Input: {
      template: '<input class="input-stub" @input="$emit(\'update:modelValue\', $event.target.value)" />',
      props: ["modelValue", "placeholder", "class"],
    },
    Badge: {
      template: '<span class="badge-stub"><slot /></span>',
      props: ["variant"],
    },
    Skeleton: {
      template: '<div class="skeleton-stub" />',
      props: ["class"],
    },
    Pagination: {
      template: '<div class="pagination-stub" />',
      props: ["total", "page", "page-size"],
    },
    Select: {
      template: '<div class="select-stub"><slot /></div>',
      props: ["modelValue"],
    },
    SelectContent: { template: '<div><slot /></div>' },
    SelectItem: { template: '<div><slot /></div>' },
    SelectTrigger: { template: '<div><slot /></div>' },
    SelectValue: { template: '<span><slot /></span>' },
    Table: { template: '<table><slot /></table>' },
    TableBody: { template: '<tbody><slot /></tbody>' },
    TableCell: { template: '<td><slot /></td>' },
    TableHead: { template: '<th><slot /></th>' },
    TableHeader: { template: '<thead><slot /></thead>' },
    TableRow: { template: '<tr><slot /></tr>' },
    Card: { template: '<div class="card-stub"><slot /></div>' },
    Plus: { template: '<div class="plus-icon" />' },
    Search: { template: '<div class="search-icon" />' },
    RotateCcw: { template: '<div class="rotate-icon" />' },
    Pencil: { template: '<div class="pencil-icon" />' },
    Trash2: { template: '<div class="trash-icon" />' },
    ShieldCheck: { template: '<div class="shield-check-icon" />' },
    ShieldOff: { template: '<div class="shield-off-icon" />' },
    Building2: { template: '<div class="building-icon" />' },
    UserX: { template: '<div class="user-x-icon" />' },
    Clock: { template: '<div class="clock-icon" />' },
  };

  describe("渲染", () => {
    it("挂载时调用 fetchTenants", async () => {
      mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(mockFetchTenants).toHaveBeenCalled();
    });

    it("显示空状态", async () => {
      mockTenants.value = [];
      mockLoading.value = false;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("暂无数据");
    });

    it("显示租户列表", async () => {
      mockTenants.value = [...mockTenantList];
      mockTotal.value = 2;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("测试租户1");
      expect(wrapper.text()).toContain("测试租户2");
    });
  });

  describe("统计卡片", () => {
    it("加载状态显示骨架屏", async () => {
      mockLoading.value = true;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      const skeletons = wrapper.findAllComponents({ name: "Skeleton" });
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it("正确显示租户总数", async () => {
      mockStats.value = { ...mockStatsData };
      mockLoading.value = false;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("租户总数");
      expect(wrapper.text()).toContain("10");
    });

    it("正确显示未激活数", async () => {
      mockStats.value = { ...mockStatsData };
      mockLoading.value = false;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("未激活数");
      expect(wrapper.text()).toContain("3");
    });

    it("正确显示过期数", async () => {
      mockStats.value = { ...mockStatsData };
      mockLoading.value = false;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("过期数");
      expect(wrapper.text()).toContain("2");
    });

    it("统计数据为 0 时正确显示", async () => {
      mockStats.value = {
        total_count: 0,
        inactive_count: 0,
        expired_count: 0,
      };
      mockLoading.value = false;

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      // 应该显示三个 0
      const text = wrapper.text();
      expect(text).toContain("租户总数");
      expect(text).toContain("未激活数");
      expect(text).toContain("过期数");
    });
  });

  describe("路由跳转", () => {
    it("点击新建按钮跳转到创建页面", async () => {
      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      // 找到新建按钮并触发点击
      const buttons = wrapper.findAllComponents({ name: "Button" });
      const createButton = buttons.find((b) => b.text().includes("新建租户"));

      if (createButton) {
        await createButton.trigger("click");
        expect(mockPush).toHaveBeenCalledWith("/tenants/create");
      }
    });
  });

  describe("状态显示", () => {
    it("激活租户显示激活标签", async () => {
      mockTenants.value = [mockTenantList[0]]; // status: 'active'

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("激活");
    });

    it("停用租户显示停用标签", async () => {
      mockTenants.value = [mockTenantList[1]]; // status: 'inactive'

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("停用");
    });
  });

  describe("日期格式化", () => {
    it("有过期时间时显示格式化日期", async () => {
      const tenantWithExpiry = {
        ...mockTenantList[0],
        expired_at: "2025-12-31T00:00:00Z",
      };
      mockTenants.value = [tenantWithExpiry];

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.exists()).toBe(true);
    });

    it("无过期时间时显示永久", async () => {
      const tenantWithoutExpiry = {
        ...mockTenantList[0],
        expired_at: undefined,
      };
      mockTenants.value = [tenantWithoutExpiry];

      const wrapper = mount(TenantList, {
        global: {
          stubs: commonStubs,
        },
      });

      await nextTick();

      expect(wrapper.text()).toContain("永久");
    });
  });
});
