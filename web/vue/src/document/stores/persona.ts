/**
 * 人设 Store
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import { getPersonas, getPersona, createPersona, updatePersona, deletePersona } from "../api/persona";
import { getErrorMessage, notifyError, notifySuccess } from "@/framework/utils/feedback";
import type { Persona, PaginatedQuery } from "../types";

export const usePersonaStore = defineStore("documentPersona", () => {
  const personas = ref<Persona[]>([]);
  const currentPersona = ref<Persona | null>(null);
  const loading = ref(false);
  const total = ref(0);

  const fetchPersonas = async (params?: PaginatedQuery) => {
    loading.value = true;
    try {
      const response = await getPersonas(params);
      if (response.data) {
        personas.value = Array.isArray(response.data) ? response.data : [];
        total.value = response.total ?? 0;
      }
    } catch (error) {
      notifyError(getErrorMessage(error, "获取人设列表失败"));
    } finally {
      loading.value = false;
    }
  };

  const fetchPersona = async (id: string) => {
    try {
      const response = await getPersona(id);
      currentPersona.value = response.data ?? null;
    } catch (error) {
      notifyError(getErrorMessage(error, "获取人设详情失败"));
    }
  };

  const create = async (data: Partial<Persona>) => {
    try {
      const response = await createPersona(data);
      notifySuccess("人设创建成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "创建人设失败"));
      throw error;
    }
  };

  const update = async (id: string, data: Partial<Persona>) => {
    try {
      const response = await updatePersona(id, data);
      notifySuccess("人设更新成功");
      return response.data;
    } catch (error) {
      notifyError(getErrorMessage(error, "更新人设失败"));
      throw error;
    }
  };

  const remove = async (id: string) => {
    try {
      await deletePersona(id);
      notifySuccess("人设删除成功");
    } catch (error) {
      notifyError(getErrorMessage(error, "删除人设失败"));
      throw error;
    }
  };

  return { personas, currentPersona, loading, total, fetchPersonas, fetchPersona, create, update, remove };
});
