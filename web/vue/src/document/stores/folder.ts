/**
 * 文件夹 Store
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import { getFolders, getFolder, createFolder, updateFolder, deleteFolder } from "../api/folder";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { Folder, PaginatedQuery } from "../types";

export const useFolderStore = defineStore("documentFolder", () => {
  const folders = ref<Folder[]>([]);
  const currentFolder = ref<Folder | null>(null);
  const loading = ref(false);
  const total = ref(0);

  const fetchFolders = async (params?: PaginatedQuery & { library_id?: string }) => {
    loading.value = true;
    try {
      const response = await getFolders(params);
      if (response.data) {
        folders.value = Array.isArray(response.data) ? response.data : [];
        total.value = response.total ?? 0;
      }
    } catch (error) {
      notifyError(getErrorMessage(error, "获取文件夹列表失败"));
    } finally {
      loading.value = false;
    }
  };

  const fetchFolder = async (id: string) => {
    try {
      const response = await getFolder(id);
      currentFolder.value = response.data ?? null;
    } catch (error) {
      notifyError(getErrorMessage(error, "获取文件夹详情失败"));
    }
  };

  const create = async (data: Partial<Folder>) => {
    try {
      const response = await createFolder(data);
      notifySuccess("文件夹创建成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "创建文件夹失败"));
      throw error;
    }
  };

  const update = async (id: string, data: Partial<Folder>) => {
    try {
      const response = await updateFolder(id, data);
      notifySuccess("文件夹更新成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "更新文件夹失败"));
      throw error;
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteFolder(id);
      notifySuccess("文件夹删除成功");
    } catch (error) {
      notifyError(getErrorMessage(error, "删除文件夹失败"));
      throw error;
    }
  };

  return { folders, currentFolder, loading, total, fetchFolders, fetchFolder, create, update, remove };
});
