/**
 * 文档库管理模块 Composables
 */

import { useLibraryStore } from "../stores/library";
import { useFolderStore } from "../stores/folder";
import { useTagStore } from "../stores/tag";
import { usePersonaStore } from "../stores/persona";

export function useDocumentLibrary() {
  return useLibraryStore();
}

export function useDocumentFolder() {
  return useFolderStore();
}

export function useDocumentTag() {
  return useTagStore();
}

export function useDocumentPersona() {
  return usePersonaStore();
}
