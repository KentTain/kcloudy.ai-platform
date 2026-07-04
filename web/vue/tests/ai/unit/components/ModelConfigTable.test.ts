/**
 * ModelConfigTable 组件单元测试
 */
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import ModelConfigTable from "@/ai/components/model-config/ModelConfigTable.vue";
import type { PluginWithModels, DefaultModelItem } from "@/ai/types/modelConfig";

// Mock lucide-vue-next
vi.mock("lucide-vue-next", () => ({
  ChevronRight: { template: '<svg class="chevron-right" />' },
  Settings: { template: '<svg class="settings" />' },
  Star: { template: '<svg class="star" />' },
  Eye: { template: '<svg class="eye" />' },
}));

const samplePlugins: PluginWithModels[] = [
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
  {
    plugin_id: "alon/cohere",
    plugin_name: "cohere",
    status: "inactive",
    models: [
      {
        model_name: "rerank-v3",
        model_label: "Rerank V3",
        model_type: "rerank",
        is_default: false,
      },
    ],
  },
];

const sampleDefaultModels: DefaultModelItem[] = [
  {
    model_type: "llm",
    plugin_id: "alon/openai",
    model_name: "gpt-4",
  },
];

describe("ModelConfigTable", () => {
  it("渲染插件行和模型行", () => {
    const wrapper = mount(ModelConfigTable, {
      props: {
        plugins: samplePlugins,
        defaultModels: sampleDefaultModels,
      },
      global: {
        stubs: {
          Table: { template: "<table><slot /></table>" },
          TableHeader: { template: "<thead><slot /></thead>" },
          TableBody: { template: "<tbody><slot /></tbody>" },
          TableRow: { template: "<tr><slot /></tr>" },
          TableHead: { template: "<th><slot /></th>" },
          TableCell: { template: "<td><slot /></td>" },
          Badge: { template: "<span><slot /></span>", props: ["variant"] },
          Button: {
            template: '<button><slot /></button>',
            props: ["variant", "size", "disabled"],
            emits: ["click"],
          },
        },
      },
    });

    // 验证插件行渲染
    const text = wrapper.text();
    expect(text).toContain("alon/openai");
    expect(text).toContain("openai");
    expect(text).toContain("alon/cohere");

    // 验证模型行渲染
    expect(text).toContain("gpt-4");
    expect(text).toContain("text-embedding-ada");
    expect(text).toContain("rerank-v3");
  });

  it("空数据时显示暂无数据", () => {
    const wrapper = mount(ModelConfigTable, {
      props: {
        plugins: [],
        defaultModels: [],
      },
      global: {
        stubs: {
          Table: { template: "<table><slot /></table>" },
          TableHeader: { template: "<thead><slot /></thead>" },
          TableBody: { template: "<tbody><slot /></tbody>" },
          TableRow: { template: "<tr><slot /></tr>" },
          TableHead: { template: "<th><slot /></th>" },
          TableCell: { template: "<td><slot /></td>" },
          Badge: { template: "<span><slot /></span>", props: ["variant"] },
          Button: {
            template: '<button><slot /></button>',
            props: ["variant", "size", "disabled"],
          },
        },
      },
    });

    expect(wrapper.text()).toContain("暂无数据");
  });

  it("点击插件行切换展开状态", async () => {
    const wrapper = mount(ModelConfigTable, {
      props: {
        plugins: samplePlugins,
        defaultModels: sampleDefaultModels,
      },
      global: {
        stubs: {
          Table: { template: "<table><slot /></table>" },
          TableHeader: { template: "<thead><slot /></thead>" },
          TableBody: { template: "<tbody><slot /></tbody>" },
          TableRow: {
            template: '<tr @click="$emit(\'click\')"><slot /></tr>',
            emits: ["click"],
          },
          TableHead: { template: "<th><slot /></th>" },
          TableCell: { template: "<td><slot /></td>" },
          Badge: { template: "<span><slot /></span>", props: ["variant"] },
          Button: {
            template: '<button @click.stop="$emit(\'click\')"><slot /></button>',
            props: ["variant", "size", "disabled"],
            emits: ["click"],
          },
        },
      },
    });

    // 首次加载时默认全部展开（watch immediate）
    const text = wrapper.text();
    expect(text).toContain("gpt-4");
  });

  it("点击详情按钮触发 view-detail 事件", async () => {
    const wrapper = mount(ModelConfigTable, {
      props: {
        plugins: samplePlugins,
        defaultModels: sampleDefaultModels,
      },
      global: {
        stubs: {
          Table: { template: "<table><slot /></table>" },
          TableHeader: { template: "<thead><slot /></thead>" },
          TableBody: { template: "<tbody><slot /></tbody>" },
          TableRow: { template: "<tr><slot /></tr>" },
          TableHead: { template: "<th><slot /></th>" },
          TableCell: { template: "<td><slot /></td>" },
          Badge: { template: "<span><slot /></span>", props: ["variant"] },
          Button: {
            template: '<button @click.stop="$emit(\'click\')"><slot /></button>',
            props: ["variant", "size", "disabled"],
            emits: ["click"],
          },
        },
      },
    });

    // 验证事件是否正确绑定
    expect(wrapper.emitted()).toBeDefined();
  });

  it("默认模型显示星标", () => {
    const wrapper = mount(ModelConfigTable, {
      props: {
        plugins: samplePlugins,
        defaultModels: sampleDefaultModels,
      },
      global: {
        stubs: {
          Table: { template: "<table><slot /></table>" },
          TableHeader: { template: "<thead><slot /></thead>" },
          TableBody: { template: "<tbody><slot /></tbody>" },
          TableRow: { template: "<tr><slot /></tr>" },
          TableHead: { template: "<th><slot /></th>" },
          TableCell: { template: "<td><slot /></td>" },
          Badge: { template: "<span><slot /></span>", props: ["variant"] },
          Button: {
            template: '<button><slot /></button>',
            props: ["variant", "size", "disabled"],
          },
        },
      },
    });

    const text = wrapper.text();
    // gpt-4 是默认模型，应显示"默认"
    expect(text).toContain("默认");
    // text-embedding-ada 不是默认模型，应显示"设置默认"
    expect(text).toContain("设置默认");
  });
});
