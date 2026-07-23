/**
 * 企业知识库管理模块状态管理
 */

import { defineStore } from "pinia";
import { ref } from "vue";

export const useDocumentLibraryStore = defineStore("documentLibrary", () => {
  const libraries = ref([]);
  const loading = ref(false);

  return {
    libraries,
    loading,
  };
});

export const useKnowledgeBaseStore = defineStore("knowledgeBase", () => {
  const knowledgeBases = ref([]);
  const loading = ref(false);

  return {
    knowledgeBases,
    loading,
  };
});

export const useReviewStore = defineStore("review", () => {
  const reviews = ref([]);
  const loading = ref(false);

  return {
    reviews,
    loading,
  };
});
