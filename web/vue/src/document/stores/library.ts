/**
 * 文档库 Store
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import { getLibraries, getLibrary, createLibrary, updateLibrary, deleteLibrary } from "../api/library";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { Library, PaginatedQuery } from "../types";

export const useLibraryStore = defineStore("documentLibrary", () => {
  const libraries = ref<Library[]>([]);
  const currentLibrary = ref<Library | null>(null);
  const loading = ref(false);
  const total = ref(0);

  const fetchLibraries = async (params?: PaginatedQuery & { library_type?: string }) => {
    loading.value = true;
    try {
      const response = await getLibraries(params);
      if (response.data) {
        libraries.value = Array.isArray(response.data) ? response.data : [];
        total.value = response.total ?? 0;
      }
    } catch (error) {
      notifyError(getErrorMessage(error, "获取文档库列表失败"));
    } finally {
      loading.value = false;
    }
  };

  const fetchLibrary = async (id: string) => {
    try {
      const response = await getLibrary(id);
      currentLibrary.value = response.data ?? null;
    } catch (error) {
      notifyError(getErrorMessage(error, "获取文档库详情失败"));
    }
  };

  const create = async (data: Partial<Library>) => {
    try {
      const response = await createLibrary(data);
      notifySuccess("文档库创建成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "创建文档库失败"));
      throw error;
    }
  };

  const update = async (id: string, data: Partial<Library>) => {
    try {
      const response = await updateLibrary(id, data);
      notifySuccess("文档库更新成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "更新文档库失败"));
      throw error;
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteLibrary(id);
      notifySuccess("文档库删除成功");
    } catch (error) {
      notifyError(getErrorMessage(error, "删除文档库失败"));
      throw error;
    }
  };

  return { libraries, currentLibrary, loading, total, fetchLibraries, fetchLibrary, create, update, remove };
});
