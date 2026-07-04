/**
 * modelConfig API 函数单元测试
 */
import { describe, expect, it, vi, beforeEach } from "vitest";

// Mock API client
const mockGet = vi.fn();
const mockPost = vi.fn();

vi.mock("@/framework/api/client", () => ({
  get: (...args: any[]) => mockGet(...args),
  post: (...args: any[]) => mockPost(...args),
}));

describe("modelConfig API", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getModelConfigOverview", () => {
    it("调用正确的 GET 端点", async () => {
      const { getModelConfigOverview } = await import("@/ai/api/modelConfig");

      mockGet.mockResolvedValue({
        data: {
          total_plugins: 2,
          configured_plugins: 1,
          total_models: 3,
          default_models: [],
          plugins: [],
        },
      });

      const result = await getModelConfigOverview();

      expect(mockGet).toHaveBeenCalledWith(
        "/ai/console/v1/model-config/overview",
      );
      expect(result.total_plugins).toBe(2);
    });

    it("data 为 null 时返回默认值", async () => {
      const { getModelConfigOverview } = await import("@/ai/api/modelConfig");

      mockGet.mockResolvedValue({ data: null });

      const result = await getModelConfigOverview();

      // res.data! 强制解包，null 时会得到 null
      expect(result).toBeNull();
    });
  });

  describe("getAvailableModels", () => {
    it("调用正确的 GET 端点并提取 models 数组", async () => {
      const { getAvailableModels } = await import("@/ai/api/modelConfig");

      const models = [
        { model_name: "gpt-4", model_type: "llm", is_enabled: true },
      ];

      mockGet.mockResolvedValue({ data: { models } });

      const result = await getAvailableModels("alon/openai");

      expect(mockGet).toHaveBeenCalledWith(
        "/ai/console/v1/model-config/plugins/alon/openai/available-models",
      );
      expect(result).toEqual(models);
    });

    it("data 为空时返回空数组", async () => {
      const { getAvailableModels } = await import("@/ai/api/modelConfig");

      mockGet.mockResolvedValue({ data: null });

      const result = await getAvailableModels("alon/openai");

      expect(result).toEqual([]);
    });
  });

  describe("setEnabledModels", () => {
    it("调用正确的 POST 端点", async () => {
      const { setEnabledModels } = await import("@/ai/api/modelConfig");

      mockPost.mockResolvedValue({ data: null });

      await setEnabledModels("alon/openai", {
        model_names: ["gpt-4", "gpt-3.5"],
      });

      expect(mockPost).toHaveBeenCalledWith(
        "/ai/console/v1/model-config/plugins/alon/openai/enabled-models",
        { model_names: ["gpt-4", "gpt-3.5"] },
      );
    });
  });

  describe("getModelsByType", () => {
    it("调用正确的 GET 端点并传递 model_type 参数", async () => {
      const { getModelsByType } = await import("@/ai/api/modelConfig");

      const models = [
        {
          plugin_id: "alon/openai",
          plugin_name: "openai",
          provider: "openai",
          model_name: "gpt-4",
          model_type: "llm",
        },
      ];

      mockGet.mockResolvedValue({ data: models });

      const result = await getModelsByType("llm");

      expect(mockGet).toHaveBeenCalledWith(
        "/ai/console/v1/model-config/models",
        { params: { model_type: "llm" } },
      );
      expect(result).toEqual(models);
    });

    it("data 为 null 时返回空数组", async () => {
      const { getModelsByType } = await import("@/ai/api/modelConfig");

      mockGet.mockResolvedValue({ data: null });

      const result = await getModelsByType("llm");

      expect(result).toEqual([]);
    });
  });

  describe("batchSetDefaultModels", () => {
    it("调用正确的 POST 端点", async () => {
      const { batchSetDefaultModels } = await import("@/ai/api/modelConfig");

      mockPost.mockResolvedValue({ data: null });

      const items = [
        { model_type: "llm", plugin_id: "alon/openai", model_name: "gpt-4" },
      ];

      await batchSetDefaultModels({ items });

      expect(mockPost).toHaveBeenCalledWith(
        "/ai/console/v1/model-config/default-models/batch",
        { items },
      );
    });
  });
});
