import { beforeEach, describe, expect, it, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useDatasetStore } from "@/demo/stores/datasets";

// Mock API
vi.mock("@/demo/api/datasets", () => ({
  getDatasets: vi.fn(() =>
    Promise.resolve([
      { id: "1", name: "知识库1", description: "描述1", createdAt: "2025-01-01", updatedAt: "2025-01-01" },
    ])
  ),
  createDataset: vi.fn((params: { name: string }) =>
    Promise.resolve({
      id: "2",
      name: params.name,
      description: "",
      createdAt: "2025-01-01",
      updatedAt: "2025-01-01",
    })
  ),
  updateDataset: vi.fn((id: string, params: { name?: string }) =>
    Promise.resolve({
      id,
      name: params.name || "Updated",
      description: "",
      createdAt: "2025-01-01",
      updatedAt: "2025-01-01",
    })
  ),
  deleteDataset: vi.fn(() => Promise.resolve()),
}));

describe("Demo Stores", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  describe("DatasetsStore", () => {
    it("initializes with default state", () => {
      const store = useDatasetStore();

      expect(store.datasets).toEqual([]);
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it("fetches datasets", async () => {
      const store = useDatasetStore();

      await store.fetchDatasets();

      expect(store.datasets).toHaveLength(1);
      expect(store.datasets[0].name).toBe("知识库1");
    });

    it("adds dataset", async () => {
      const store = useDatasetStore();

      await store.addDataset({ name: "新知识库" });

      expect(store.datasets).toHaveLength(1);
      expect(store.datasets[0].name).toBe("新知识库");
    });

    it("removes dataset", async () => {
      const store = useDatasetStore();

      await store.fetchDatasets();
      await store.removeDataset("1");

      expect(store.datasets).toHaveLength(0);
    });
  });
});
