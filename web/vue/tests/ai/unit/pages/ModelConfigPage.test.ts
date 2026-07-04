/**
 * ModelConfigPage 页面单元测试
 */
import { describe, expect, it, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import ModelConfigPage from "@/ai/pages/ModelConfigPage.vue";

// Mock API
const mockGetModelConfigOverview = vi.fn();
vi.mock("@/ai/api/modelConfig", () => ({
  getModelConfigOverview: (...args: any[]) => mockGetModelConfigOverview(...args),
}));

// Mock vue-router
const mockPush = vi.fn();
vi.mock("vue-router", () => ({
  useRouter: () => ({ push: mockPush }),
  useRoute: () => ({ path: "/ai/model-config" }),
}));

// Mock feedback utils
vi.mock("@/framework/utils/feedback", () => ({
  notifySuccess: vi.fn(),
  notifyError: vi.fn(),
  confirmAction: vi.fn(() => true),
}));

// Mock lucide-vue-next — use original for tree-shaken imports
vi.mock("lucide-vue-next", async (importOriginal) => {
  const actual = await importOriginal();
  return actual;
});

const mockOverviewData = {
  total_plugins: 2,
  configured_plugins: 1,
  total_models: 3,
  default_models: [
    {
      model_type: "llm",
      plugin_id: "alon/openai",
      model_name: "gpt-4",
      is_valid: true,
    },
  ],
  plugins: [
    {
      plugin_id: "alon/openai",
      plugin_name: "openai",
      status: "active",
      models: [
        {
          model_name: "gpt-4",
          model_label: "GPT-4",
          model_type: "llm",
          is_default: true,
        },
        {
          model_name: "text-embedding-ada",
          model_label: "Embedding Ada",
          model_type: "text-embedding",
          is_default: false,
        },
      ],
    },
  ],
};

describe("ModelConfigPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    mockGetModelConfigOverview.mockResolvedValue(mockOverviewData);
  });

  it("挂载后加载概览数据", async () => {
    mount(ModelConfigPage, {
      global: {
        stubs: {
          ModelConfigStats: true,
          DefaultModelDisplay: true,
          ModelConfigTable: true,
          ConfigureModelsDialog: true,
          SetDefaultModelDialog: true,
          Button: true,
          Input: true,
        },
      },
    });

    await flushPromises();

    expect(mockGetModelConfigOverview).toHaveBeenCalledTimes(1);
  });

  it("加载失败时显示错误通知", async () => {
    mockGetModelConfigOverview.mockRejectedValue(new Error("network error"));

    mount(ModelConfigPage, {
      global: {
        stubs: {
          ModelConfigStats: true,
          DefaultModelDisplay: true,
          ModelConfigTable: true,
          ConfigureModelsDialog: true,
          SetDefaultModelDialog: true,
          Button: true,
          Input: true,
        },
      },
    });

    await flushPromises();

    const { notifyError } = await import("@/framework/utils/feedback");
    expect(notifyError).toHaveBeenCalledWith("获取模型配置数据失败");
  });

  it("view-detail 事件跳转到插件配置页", async () => {
    const wrapper = mount(ModelConfigPage, {
      global: {
        stubs: {
          ModelConfigStats: true,
          DefaultModelDisplay: true,
          ConfigureModelsDialog: true,
          SetDefaultModelDialog: true,
          Button: true,
          Input: true,
          ModelConfigTable: {
            template: '<div data-testid="model-config-table" />',
            props: ["plugins", "defaultModels"],
            emits: ["configure-models", "set-default", "view-detail"],
          },
        },
      },
    });

    await flushPromises();

    const table = wrapper.findComponent({ name: "ModelConfigTable" });
    expect(table.exists()).toBe(true);

    table.vm.$emit("view-detail", "alon/openai");
    await flushPromises();

    expect(mockPush).toHaveBeenCalledWith({
      name: "AIPluginConfig",
      params: { pluginId: "alon/openai" },
    });
  });

  it("configure-models 事件打开配置弹窗", async () => {
    const wrapper = mount(ModelConfigPage, {
      global: {
        stubs: {
          ModelConfigStats: true,
          DefaultModelDisplay: true,
          SetDefaultModelDialog: true,
          Button: true,
          Input: true,
          ModelConfigTable: {
            template: '<div />',
            props: ["plugins", "defaultModels"],
            emits: ["configure-models", "set-default", "view-detail"],
          },
          ConfigureModelsDialog: {
            template: '<div />',
            props: ["open", "pluginId", "pluginName"],
            emits: ["update:open", "saved"],
          },
        },
      },
    });

    await flushPromises();

    const table = wrapper.findComponent({ name: "ModelConfigTable" });
    table.vm.$emit("configure-models", mockOverviewData.plugins[0]);
    await flushPromises();

    const dialog = wrapper.findComponent({ name: "ConfigureModelsDialog" });
    expect(dialog.exists()).toBe(true);
    expect(dialog.props("open")).toBe(true);
    expect(dialog.props("pluginId")).toBe("alon/openai");
  });

  it("saved 事件触发重新加载", async () => {
    const wrapper = mount(ModelConfigPage, {
      global: {
        stubs: {
          ModelConfigStats: true,
          DefaultModelDisplay: true,
          ModelConfigTable: true,
          SetDefaultModelDialog: true,
          Button: true,
          Input: true,
          ConfigureModelsDialog: {
            template: '<div />',
            props: ["open", "pluginId", "pluginName"],
            emits: ["update:open", "saved"],
          },
        },
      },
    });

    await flushPromises();

    expect(mockGetModelConfigOverview).toHaveBeenCalledTimes(1);

    const dialog = wrapper.findComponent({ name: "ConfigureModelsDialog" });
    dialog.vm.$emit("saved");
    await flushPromises();

    expect(mockGetModelConfigOverview).toHaveBeenCalledTimes(2);
  });

  it("set-default 事件打开设置默认模型弹窗", async () => {
    const wrapper = mount(ModelConfigPage, {
      global: {
        stubs: {
          ModelConfigStats: true,
          DefaultModelDisplay: true,
          ConfigureModelsDialog: true,
          Button: true,
          Input: true,
          ModelConfigTable: {
            template: '<div />',
            props: ["plugins", "defaultModels"],
            emits: ["configure-models", "set-default", "view-detail"],
          },
          SetDefaultModelDialog: {
            template: '<div />',
            props: ["open", "modelType", "currentDefault", "pluginId"],
            emits: ["update:open", "saved"],
          },
        },
      },
    });

    await flushPromises();

    const model = { model_name: "gpt-4", model_type: "llm", is_default: true };
    const plugin = mockOverviewData.plugins[0];

    const table = wrapper.findComponent({ name: "ModelConfigTable" });
    table.vm.$emit("set-default", model, plugin);
    await flushPromises();

    const dialog = wrapper.findComponent({ name: "SetDefaultModelDialog" });
    expect(dialog.exists()).toBe(true);
    expect(dialog.props("open")).toBe(true);
    expect(dialog.props("modelType")).toBe("llm");
  });
});
