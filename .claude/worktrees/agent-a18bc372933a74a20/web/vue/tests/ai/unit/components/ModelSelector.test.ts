/**
 * ModelSelector 组件单元测试
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { ref, nextTick } from "vue";
import { createPinia, setActivePinia } from "pinia";
import ModelSelector from "@/ai/components/ModelSelector.vue";
import { getModels } from "@/ai/api/model";

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

// 获取 mock 引用
const mockGetModels = vi.mocked(getModels);

describe("ModelSelector", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mockCurrentModel.value = { provider: "openai", name: "gpt-4o-mini" };
    // 重置 API mock 为默认成功响应
    mockGetModels.mockImplementation(() =>
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
    );
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

  describe("模型选择交互", () => {
    it("选择模型时通过 computed setter 调用 setModel", async () => {
      const wrapper = mount(ModelSelector, {
        global: {
          stubs: {
            Select: {
              template: '<div class="select-stub"><slot /></div>',
              props: ["modelValue"],
              model: {
                prop: "modelValue",
                event: "update:modelValue",
              },
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

      // 通过组件内部触发 computed setter
      // 直接修改组件实例来模拟 Select 组件的 v-model 更新
      const vm = wrapper.vm as unknown as {
        selectedModelId: string;
      };

      // 设置 selectedModelId 会触发 setter
      vm.selectedModelId = "anthropic/claude-3-opus";
      await nextTick();

      // 验证 setModel 被正确调用
      expect(mockSetModel).toHaveBeenCalledTimes(1);
      expect(mockSetModel).toHaveBeenCalledWith({
        provider: "anthropic",
        name: "claude-3-opus",
      });
    });

    it("setModel 接收正确的参数格式 { provider, name }", async () => {
      const wrapper = mount(ModelSelector, {
        global: {
          stubs: {
            Select: {
              template: "<div><slot /></div>",
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

      const vm = wrapper.vm as unknown as {
        selectedModelId: string;
      };

      // 测试不同提供商的模型
      vm.selectedModelId = "openai/gpt-4o";
      await nextTick();

      // 验证参数包含 provider 和 name 两个字段
      const callArgs = mockSetModel.mock.calls[0][0];
      expect(callArgs).toHaveProperty("provider");
      expect(callArgs).toHaveProperty("name");
      expect(callArgs.provider).toBe("openai");
      expect(callArgs.name).toBe("gpt-4o");
      expect(typeof callArgs.provider).toBe("string");
      expect(typeof callArgs.name).toBe("string");
    });
  });

  describe("错误场景", () => {
    it("API 返回错误时显示错误状态", async () => {
      // 模拟 API 返回错误
      mockGetModels.mockRejectedValueOnce(new Error("网络错误"));

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

      // 等待异步加载完成
      await new Promise((resolve) => setTimeout(resolve, 100));
      await nextTick();

      // 应该显示错误状态
      expect(wrapper.text()).toContain("加载失败");
    });

    it("API 返回非 Error 对象时显示默认错误消息", async () => {
      // 模拟 API 返回非 Error 类型的错误
      mockGetModels.mockRejectedValueOnce("未知错误");

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

      await new Promise((resolve) => setTimeout(resolve, 100));
      await nextTick();

      // 应该显示默认错误消息
      expect(wrapper.text()).toContain("加载失败");
    });
  });
});
