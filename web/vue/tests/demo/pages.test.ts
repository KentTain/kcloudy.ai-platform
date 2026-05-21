import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import HomePage from "@/demo/pages/HomePage.vue";
import HealthPage from "@/demo/pages/HealthPage.vue";
import DatasetsPage from "@/demo/pages/DatasetsPage.vue";

// Mock API
vi.mock("@/demo/api/health", () => ({
  getHealth: vi.fn(() =>
    Promise.resolve({
      status: "healthy",
      timestamp: "2025-01-01T00:00:00Z",
    })
  ),
}));

vi.mock("@/demo/api/datasets", () => ({
  getDatasets: vi.fn(() =>
    Promise.resolve([
      { id: "1", name: "知识库1", description: "描述1" },
      { id: "2", name: "知识库2", description: "描述2" },
    ])
  ),
}));

describe("Demo Pages", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("HomePage", () => {
    it("renders correctly", () => {
      const wrapper = mount(HomePage, {
        global: { plugins: [createPinia()] },
      });

      expect(wrapper.find(".home-page").exists()).toBe(true);
    });

    it("shows welcome message", () => {
      const wrapper = mount(HomePage, {
        global: { plugins: [createPinia()] },
      });

      expect(wrapper.text()).toContain("欢迎使用 AI 助手平台");
    });

    it("shows feature cards", () => {
      const wrapper = mount(HomePage, {
        global: { plugins: [createPinia()] },
      });

      expect(wrapper.text()).toContain("设计令牌系统");
      expect(wrapper.text()).toContain("AdminLayout 布局");
      expect(wrapper.text()).toContain("UI 组件库");
      expect(wrapper.text()).toContain("权限控制");
    });
  });

  describe("HealthPage", () => {
    it("renders correctly", () => {
      const wrapper = mount(HealthPage, {
        global: { plugins: [createPinia()] },
      });

      expect(wrapper.find(".health-page").exists()).toBe(true);
    });

    it("shows title", () => {
      const wrapper = mount(HealthPage, {
        global: { plugins: [createPinia()] },
      });

      expect(wrapper.text()).toContain("健康检查");
    });
  });

  describe("DatasetsPage", () => {
    it("renders correctly", async () => {
      const wrapper = mount(DatasetsPage, {
        global: { plugins: [createPinia()] },
      });

      expect(wrapper.find(".datasets-page").exists()).toBe(true);
      await wrapper.vm.$nextTick();
      expect(wrapper.text()).toContain("知识库列表");
    });

    it("loads datasets from store", async () => {
      const wrapper = mount(DatasetsPage, {
        global: { plugins: [createPinia()] },
      });

      await vi.waitFor(() => {
        expect(wrapper.text()).toContain("知识库1");
      });
    });
  });
});
