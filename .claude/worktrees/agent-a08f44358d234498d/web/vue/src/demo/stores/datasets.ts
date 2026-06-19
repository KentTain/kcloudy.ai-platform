import { defineStore } from "pinia";
import { ref } from "vue";
import { createDataset, deleteDataset, getDatasets, updateDataset } from "@/demo/api/datasets";
import type { DatasetCreate, Dataset, DatasetUpdate } from "@/demo/api/datasets";

/**
 * 知识库状态管理
 */
export const useDatasetStore = defineStore("dataset", () => {
  const datasets = ref<Dataset[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const fetchDatasets = async () => {
    loading.value = true;
    error.value = null;

    try {
      datasets.value = await getDatasets();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "获取知识库列表失败";
    } finally {
      loading.value = false;
    }
  };

  const addDataset = async (params: DatasetCreate) => {
    const dataset = await createDataset(params);
    datasets.value.push(dataset);
    return dataset;
  };

  const editDataset = async (id: string, params: DatasetUpdate) => {
    const dataset = await updateDataset(id, params);
    const index = datasets.value.findIndex((d) => d.id === id);
    if (index !== -1) {
      datasets.value[index] = dataset;
    }
    return dataset;
  };

  const removeDataset = async (id: string) => {
    await deleteDataset(id);
    datasets.value = datasets.value.filter((d) => d.id !== id);
  };

  return {
    datasets,
    loading,
    error,
    fetchDatasets,
    addDataset,
    editDataset,
    removeDataset,
  };
});

export default useDatasetStore;
