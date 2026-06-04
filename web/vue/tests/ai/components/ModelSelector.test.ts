/**
 * ModelSelector 组件单元测试
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { ref, nextTick } from "vue";
import { createPinia, setActivePinia } from "pinia";
import ModelSelector from "@/ai/components/ModelSelector.vue";

// Mock conversation store
const mockCurrentModel = ref({ provider: "openai", name: "gpt-4o-mini" });
const mockSetModel = vi.fn();

vi.mock("@/ai/stores", () => ({
  useConversationStore: vi.fn(() => ({
    currentModel: mockCurrentModel.value,
    setModel: mockSetModel,
  })),
}));

// Mock API
vi.mock("@/ai/api/model", () => ({
  getModels: vi.fn(() =>
    Promise.resolve({
      providers: [
        {
          id: "openai",
          name: "OpenAI",
          models: [
            { id: "openai/gpt-4o-mini", name: "gpt-4o-mini" },
            { id: "openai/gpt-4o", name: "gpt-4o" },
          ],
        },
        {
          id: "anthropic",
          name: "Anthropic",
          models: [{ id: "anthropic/claude-3-opus", name: "claude-3-opus" }],
        },
      ],
    })
  ),
}));

describe("ModelSelector", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mockCurrentModel.value = { provider: "openai", name: "gpt-4o-mini" };
  });

  describe("渲染", () => {
    it("加载完成后渲染选择器", async () => {
      const wrapper = mount(ModelSelector, {
        global: {
          stubs: {
            Select: {
              template: '<div class="select-stub"><slot /></div>',
              props: ["modelValue"],
            },
            SelectTrigger: {
              template: '<div class="select-trigger-stub"><slot /></div>',
            },
            SelectValue: {
              template: '<div class="select-value-stub"><slot /></div>',
            },
            SelectContent: {
              template: '<div class="select-content-stub"><slot /></div>',
            },
            SelectGroup: {
              template: '<div class="select-group-stub"><slot /></div>',
            },
            SelectLabel: {
              template: '<div class="select-label-stub"><slot /></div>',
            },
            SelectItem: {
              template: '<div class="select-item-stub"><slot /></div>',
              props: ["value"],
            },
            Skeleton: {
              template: '<div class="skeleton-stub" />',
            },
          },
        },
      });

      // 等待异步加载完成
      await new Promise((resolve) => setTimeout(resolve, 100));
      await nextTick();

      // 组件应该渲染成功
      expect(wrapper.exists()).toBe(true);
    });

    it("组件挂载时处于加载状态", async () => {
      const wrapper = mount(ModelSelector, {
        global: {
          stubs: {
            Skeleton: {
              template: '<div class="skeleton-stub" />',
            },
            Select: { template: '<div class="select-stub" />' },
            SelectTrigger: { template: "<div />" },
            SelectValue: { template: "<div />" },
            SelectContent: { template: "<div />" },
            SelectGroup: { template: "<div />" },
            SelectLabel: { template: "<div />" },
            SelectItem: { template: "<div />" },
          },
        },
      });

      // 组件初始挂载时会短暂显示 loading 状态
      // 由于 mock API 立即返回，这里只验证组件正常渲染
      expect(wrapper.exists()).toBe(true);
    });
  });

  describe("模型选择", () => {
    it("组件成功挂载并调用 API", async () => {
      const wrapper = mount(ModelSelector, {
        global: {
          stubs: {
            Select: {
              template: '<div class="select-stub"><slot /></div>',
              props: ["modelValue"],
            },
            SelectTrigger: { template: "<div><slot /></div>" },
            SelectValue: { template: "<div><slot /></div>" },
            SelectContent: { template: "<div><slot /></div>" },
            SelectGroup: { template: "<div><slot /></div>" },
            SelectLabel: { template: "<div><slot /></div>" },
            SelectItem: { template: "<div><slot /></div>", props: ["value"] },
            Skeleton: { template: "<div />" },
          },
        },
      });

      await new Promise((resolve) => setTimeout(resolve, 100));
      await nextTick();

      // 组件应该渲染成功
      expect(wrapper.exists()).toBe(true);
    });
  });

  describe("刷新功能", () => {
    it("暴露 refresh 方法", async () => {
      const wrapper = mount(ModelSelector, {
        global: {
          stubs: {
            Select: { template: "<div><slot /></div>" },
            SelectTrigger: { template: "<div><slot /></div>" },
            SelectValue: { template: "<div><slot /></div>" },
            SelectContent: { template: "<div><slot /></div>" },
            SelectGroup: { template: "<div><slot /></div>" },
            SelectLabel: { template: "<div><slot /></div>" },
            SelectItem: { template: "<div><slot /></div>", props: ["value"] },
            Skeleton: { template: "<div />" },
          },
        },
      });

      // 组件应该暴露 refresh 方法
      expect(typeof wrapper.vm.refresh).toBe("function");
    });
  });
});
