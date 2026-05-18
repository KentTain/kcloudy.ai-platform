import { defineStore } from "pinia";
import { ref } from "vue";
import { createDataset as createDatasetApi, getDatasets as fetchDatasetsApi } from "@/api";
import type { CreateDatasetRequest, Dataset } from "@/types";

export const useDatasetsStore = defineStore("datasets", () => {
  const datasets = ref<Dataset[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function fetchDatasets() {
    loading.value = true;
    error.value = null;

    try {
      datasets.value = await fetchDatasetsApi();
    } catch (e) {
      error.value = e instanceof Error ? e.message : "获取知识库列表失败";
    } finally {
      loading.value = false;
    }
  }

  async function createDataset(data: CreateDatasetRequest) {
    await createDatasetApi(data);
    await fetchDatasets();
  }

  function $reset() {
    datasets.value = [];
    loading.value = false;
    error.value = null;
  }

  return {
    datasets,
    loading,
    error,
    fetchDatasets,
    createDataset,
    $reset,
  };
});
