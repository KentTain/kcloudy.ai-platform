import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";
import { useDatasetsStore } from "../datasets";

// Mock the API module
vi.mock("@/api", () => ({
  getDatasets: vi.fn(),
  createDataset: vi.fn(),
}));

import { createDataset, getDatasets } from "@/api";

const mockedGetDatasets = vi.mocked(getDatasets);
const mockedCreateDataset = vi.mocked(createDataset);

describe("useDatasetsStore", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  describe("initial state", () => {
    it("has empty datasets by default", () => {
      const store = useDatasetsStore();
      expect(store.datasets).toEqual([]);
    });

    it("has loading set to false", () => {
      const store = useDatasetsStore();
      expect(store.loading).toBe(false);
    });

    it("has error set to null", () => {
      const store = useDatasetsStore();
      expect(store.error).toBeNull();
    });
  });

  describe("fetchDatasets", () => {
    it("populates datasets on success", async () => {
      const store = useDatasetsStore();
      const mockDatasets = [
        { id: "1", name: "Dataset 1", description: "Description 1" },
        { id: "2", name: "Dataset 2", description: "Description 2" },
      ];
      mockedGetDatasets.mockResolvedValue(mockDatasets);

      await store.fetchDatasets();

      expect(store.datasets).toEqual(mockDatasets);
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });

    it("sets error on failure", async () => {
      const store = useDatasetsStore();
      mockedGetDatasets.mockRejectedValue(new Error("Network error"));

      await store.fetchDatasets();

      expect(store.error).toBe("Network error");
      expect(store.loading).toBe(false);
      expect(store.datasets).toEqual([]);
    });

    it("uses default error message for non-Error failures", async () => {
      const store = useDatasetsStore();
      mockedGetDatasets.mockRejectedValue("Unknown error");

      await store.fetchDatasets();

      expect(store.error).toBe("获取知识库列表失败");
    });
  });

  describe("createDataset", () => {
    it("calls createDataset API and refreshes list", async () => {
      const store = useDatasetsStore();
      const mockDatasets = [{ id: "1", name: "Dataset 1", description: "" }];
      mockedCreateDataset.mockResolvedValue({ id: "1", name: "New Dataset", description: "New" });
      mockedGetDatasets.mockResolvedValue(mockDatasets);

      await store.createDataset({ name: "New Dataset", description: "New" });

      expect(mockedCreateDataset).toHaveBeenCalledWith({
        name: "New Dataset",
        description: "New",
      });
      expect(mockedGetDatasets).toHaveBeenCalled();
      expect(store.datasets).toEqual(mockDatasets);
    });
  });

  describe("$reset", () => {
    it("resets store to initial state", async () => {
      const store = useDatasetsStore();
      mockedGetDatasets.mockResolvedValue([
        { id: "1", name: "Dataset 1", description: "" },
      ]);

      await store.fetchDatasets();
      expect(store.datasets.length).toBe(1);

      store.$reset();

      expect(store.datasets).toEqual([]);
      expect(store.loading).toBe(false);
      expect(store.error).toBeNull();
    });
  });
});
