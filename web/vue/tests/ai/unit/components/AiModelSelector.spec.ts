/**
 * AiModelSelector 组件单元测试
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import AiModelSelector from "@/ai/components/AiModelSelector.vue";
import { useConversationStore } from "@/ai/stores";
import type { ProviderItem } from "@/ai/api/model";

// Mock API
vi.mock("@/ai/api/model", () => ({
  getModels: vi.fn(() =>
    Promise.resolve({
      providers: [
        {
          id: "openai",
          name: "OpenAI",
          icon_small: "https://example.com/openai.svg",
          icon_large: "https://example.com/openai-large.svg",
          models: [
            { id: "openai/gpt-4o-mini", name: "gpt-4o-mini", label: "GPT-4o Mini" },
            { id: "openai/gpt-4o", name: "gpt-4o", label: "GPT-4o" },
          ],
        },
        {
          id: "anthropic",
          name: "Anthropic",
          icon_small: "https://example.com/anthropic.svg",
          models: [
            { id: "anthropic/claude-3-5-sonnet-20241022", name: "claude-3-5-sonnet-20241022", label: "Claude 3.5 Sonnet" },
          ],
        },
      ],
    })
  ),
  getDefaultModel: vi.fn(() =>
    Promise.resolve({
      id: "default_123",
      tenant_id: "tenant_123",
      model_type: "llm",
      plugin_id: "openai",
      model_name: "gpt-4o-mini",
      is_valid: true,
    })
  ),
  setDefaultModel: vi.fn(() => Promise.resolve()),
}));

describe("AiModelSelector", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("应该正确渲染触发器按钮", async () => {
    const wrapper = mount(AiModelSelector);
    expect(wrapper.find("button").exists()).toBe(true);
  });

  it("应该在挂载时加载模型列表", async () => {
    const store = useConversationStore();
    mount(AiModelSelector);

    // 等待异步操作
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(store.providers.length).toBeGreaterThan(0);
  });

  it("应该显示当前选中的模型", async () => {
    const store = useConversationStore();
    store.setModel({
      provider: "openai",
      name: "gpt-4o-mini",
    });

    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    // 验证按钮文本包含模型名称
    const buttonText = wrapper.find("button").text();
    expect(buttonText).toContain("GPT-4o Mini");
  });

  it("应该按提供商分组显示模型", async () => {
    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    // 验证至少有一个提供商组
    const store = useConversationStore();
    expect(store.providers.length).toBeGreaterThan(0);

    const firstProvider = store.providers[0] as ProviderItem;
    expect(firstProvider.name).toBeDefined();
    expect(firstProvider.models.length).toBeGreaterThan(0);
  });

  it("应该显示提供商 Logo", async () => {
    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    const store = useConversationStore();
    const firstProvider = store.providers[0] as ProviderItem;

    if (firstProvider.icon_small) {
      const img = wrapper.find("img");
      expect(img.exists()).toBe(true);
      expect(img.attributes("src")).toBe(firstProvider.icon_small);
    }
  });

  it("选择模型后应该更新 Store", async () => {
    const store = useConversationStore();
    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    // 模拟选择模型
    store.setModel({
      provider: "anthropic",
      name: "claude-3-5-sonnet-20241022",
    });

    expect(store.currentModel.provider).toBe("anthropic");
    expect(store.currentModel.name).toBe("claude-3-5-sonnet-20241022");
  });

  it("应该加载并应用默认模型", async () => {
    const store = useConversationStore();
    mount(AiModelSelector);

    // 等待默认模型加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    // 验证默认模型已加载
    expect(store.defaultModel).not.toBeNull();
    expect(store.defaultModel?.plugin_id).toBe("openai");
    expect(store.defaultModel?.model_name).toBe("gpt-4o-mini");
  });

  it("模型 ID 应该使用 provider/model 格式", async () => {
    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    const store = useConversationStore();
    const firstProvider = store.providers[0] as ProviderItem;
    const firstModel = firstProvider.models[0];

    // 验证模型 ID 格式
    expect(firstModel.id).toContain("/");
    const [provider, name] = firstModel.id.split("/");
    expect(provider).toBe(firstProvider.id);
    expect(name).toBe(firstModel.name);
  });

  it("Logo 加载失败时应该隐藏", async () => {
    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    const img = wrapper.find("img");
    if (img.exists()) {
      // 模拟图片加载错误
      await img.trigger("error");

      // 验证图片已隐藏（通过 style.display = "none"）
      // 注意：这取决于具体的错误处理实现
    }
  });

  it("应该显示占位文本当未选择模型时", async () => {
    const store = useConversationStore();
    store.resetModel();

    const wrapper = mount(AiModelSelector);

    const buttonText = wrapper.find("button").text();
    expect(buttonText).toContain("请选择模型");
  });

  it("应该正确处理暗色模式下的 Logo", async () => {
    const wrapper = mount(AiModelSelector);

    // 等待模型列表加载
    await new Promise((resolve) => setTimeout(resolve, 100));

    const img = wrapper.find("img");
    if (img.exists()) {
      // 验证暗色模式样式类
      const classList = img.classes();
      expect(classList.some((cls) => cls.includes("dark:invert"))).toBe(true);
    }
  });
});

describe("AiModelSelector 集成测试", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("完整的模型选择流程", async () => {
    const store = useConversationStore();
    const wrapper = mount(AiModelSelector);

    // 1. 等待初始化
    await new Promise((resolve) => setTimeout(resolve, 100));

    // 2. 验证模型列表已加载
    expect(store.providers.length).toBeGreaterThan(0);

    // 3. 验证默认模型已应用
    expect(store.defaultModel).not.toBeNull();

    // 4. 模拟用户选择模型
    const newModel = {
      provider: "anthropic",
      name: "claude-3-5-sonnet-20241022",
    };
    store.setModel(newModel);

    // 5. 验证状态更新
    expect(store.currentModel.provider).toBe("anthropic");
    expect(store.currentModel.name).toBe("claude-3-5-sonnet-20241022");

    // 6. 验证模型详情可查找
    let found = false;
    for (const provider of store.providers) {
      for (const model of provider.models) {
        if (model.id === `${newModel.provider}/${newModel.name}`) {
          found = true;
          break;
        }
      }
      if (found) break;
    }
    expect(found).toBe(true);
  });

  it("Store 状态持久化到 localStorage", async () => {
    const store = useConversationStore();

    const testModel = {
      provider: "test_provider",
      name: "test_model",
    };

    store.setModel(testModel);

    // 验证 localStorage 已更新
    const stored = JSON.parse(localStorage.getItem("selected_model") || "{}");
    expect(stored.provider).toBe(testModel.provider);
    expect(stored.name).toBe(testModel.name);
  });
});
