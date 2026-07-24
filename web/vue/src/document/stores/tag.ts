/**
 * 标签 Store
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import { getTags, getTag, createTag, updateTag, deleteTag } from "../api/tag";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { Tag, PaginatedQuery } from "../types";

export const useTagStore = defineStore("documentTag", () => {
  const tags = ref<Tag[]>([]);
  const currentTag = ref<Tag | null>(null);
  const loading = ref(false);
  const total = ref(0);

  const fetchTags = async (params?: PaginatedQuery) => {
    loading.value = true;
    try {
      const response = await getTags(params);
      if (response.data) {
        tags.value = Array.isArray(response.data) ? response.data : [];
        total.value = response.total ?? 0;
      }
    } catch (error) {
      notifyError(getErrorMessage(error, "获取标签列表失败"));
    } finally {
      loading.value = false;
    }
  };

  const fetchTag = async (id: string) => {
    try {
      const response = await getTag(id);
      currentTag.value = response.data ?? null;
    } catch (error) {
      notifyError(getErrorMessage(error, "获取标签详情失败"));
    }
  };

  const create = async (data: Partial<Tag>) => {
    try {
      const response = await createTag(data);
      notifySuccess("标签创建成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "创建标签失败"));
      throw error;
    }
  };

  const update = async (id: string, data: Partial<Tag>) => {
    try {
      const response = await updateTag(id, data);
      notifySuccess("标签更新成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "更新标签失败"));
      throw error;
    }
  };

  const remove = async (id: string) => {
    try {
      await deleteTag(id);
      notifySuccess("标签删除成功");
    } catch (error) {
      notifyError(getErrorMessage(error, "删除标签失败"));
      throw error;
    }
  };

  return { tags, currentTag, loading, total, fetchTags, fetchTag, create, update, remove };
});
