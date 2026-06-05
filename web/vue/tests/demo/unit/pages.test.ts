import { beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import HomePage from "@/demo/pages/HomePage.vue";
import HealthPage from "@/demo/pages/HealthPage.vue";
import DatasetsPage from "@/demo/pages/DatasetsPage.vue";
import { getHealth } from "@/demo/api/health";
import { getDatasets } from "@/demo/api/datasets";

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
      { id: "1", name: "知识库1", description: "描述1", createdAt: "2025-01-01", updatedAt: "2025-01-01" },
      { id: "2", name: "知识库2", description: "描述2", createdAt: "2025-01-02", updatedAt: "2025-01-02" },
    ])
  ),
}));

describe("Demo Pages", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("HomePage", () => {
    it("renders AppPage skeleton with title", () => {
      const wrapper = mount(HomePage);
      expect(wrapper.text()).toContain("欢迎使用 AI 助手平台");
    });

    it("shows feature cards via shadcn Card", () => {
      const wrapper = mount(HomePage);
      expect(wrapper.text()).toContain("设计令牌系统");
      expect(wrapper.text()).toContain("AdminLayout 布局");
      expect(wrapper.text()).toContain("UI 组件库");
      expect(wrapper.text()).toContain("权限控制");
    });

    it("does not use CommonCard", () => {
      const wrapper = mount(HomePage);
      expect(wrapper.findComponent({ name: "CommonCard" }).exists()).toBe(false);
    });
  });

  describe("HealthPage", () => {
    it("renders AppPage skeleton with title", () => {
      const wrapper = mount(HealthPage);
      expect(wrapper.text()).toContain("健康检查");
    });

    it("shows Badge for health status", async () => {
      const wrapper = mount(HealthPage);
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain("healthy");
      });
    });

    it("renders error state with retry button", async () => {
      vi.mocked(getHealth).mockRejectedValueOnce(new Error("服务不可用"));
      const wrapper = mount(HealthPage);
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain("服务不可用");
        expect(wrapper.text()).toContain("重试");
      });
    });

    it("does not use Common components", () => {
      const wrapper = mount(HealthPage);
      expect(wrapper.findComponent({ name: "CommonCard" }).exists()).toBe(false);
      expect(wrapper.findComponent({ name: "CommonButton" }).exists()).toBe(false);
      expect(wrapper.findComponent({ name: "CommonLoading" }).exists()).toBe(false);
    });
  });

  describe("DatasetsPage", () => {
    it("renders AppPage skeleton with title", () => {
      const wrapper = mount(DatasetsPage);
      expect(wrapper.text()).toContain("知识库列表");
    });

    it("renders Table columns after data loads", async () => {
      const wrapper = mount(DatasetsPage);
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain("知识库1");
        expect(wrapper.text()).toContain("知识库2");
      });
    });

    it("provides search input for filtering", () => {
      const wrapper = mount(DatasetsPage);
      expect(wrapper.find("input").exists()).toBe(true);
    });

    it("filters datasets by search query", async () => {
      const wrapper = mount(DatasetsPage);
      await vi.waitFor(() => {
        expect(wrapper.text()).toContain("知识库1");
        expect(wrapper.text()).toContain("知识库2");
      });

      const input = wrapper.find("input");
      await input.setValue("知识库1");
      expect(wrapper.text()).toContain("知识库1");
      expect(wrapper.text()).not.toContain("知识库2");
    });

    it("does not use Common components", () => {
      const wrapper = mount(DatasetsPage);
      expect(wrapper.findComponent({ name: "CommonCard" }).exists()).toBe(false);
      expect(wrapper.findComponent({ name: "CommonButton" }).exists()).toBe(false);
      expect(wrapper.findComponent({ name: "CommonLoading" }).exists()).toBe(false);
    });
  });
});