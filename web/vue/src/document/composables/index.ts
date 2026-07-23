/**
 * 企业知识库管理模块 Composables
 */

import { ref } from "vue";
import { useDocumentLibraryStore, useKnowledgeBaseStore, useReviewStore } from "../stores";

export function useDocumentLibrary() {
  const store = useDocumentLibraryStore();
  return {
    libraries: store.libraries,
    loading: store.loading,
  };
}

export function useKnowledgeBase() {
  const store = useKnowledgeBaseStore();
  return {
    knowledgeBases: store.knowledgeBases,
    loading: store.loading,
  };
}

export function useReview() {
  const store = useReviewStore();
  return {
    reviews: store.reviews,
    loading: store.loading,
  };
}
