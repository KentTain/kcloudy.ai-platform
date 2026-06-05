import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import AppContentHeader from "@/framework/layouts/components/AppContentHeader.vue";

// Mock vue-router
vi.mock("vue-router", () => ({
  useRoute: vi.fn(() => ({
    path: "/",
    matched: [],
    meta: {},
  })),
  useRouter: () => ({
    push: vi.fn(),
  }),
}));

describe("AppContentHeader", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("shows '首页' when on root path with no matched routes", async () => {
    const wrapper = mount(AppContentHeader, {
      global: {
        plugins: [createPinia()],
        stubs: {
          SidebarTrigger: true,
          Separator: true,
          RouterLink: true,
        },
      },
    });

    // 等待 computed 计算
    await wrapper.vm.$nextTick();

    // 当 route.path === "/" 且 matched 为空时，应显示首页面包屑
    expect(wrapper.text()).toContain("首页");
  });
});
