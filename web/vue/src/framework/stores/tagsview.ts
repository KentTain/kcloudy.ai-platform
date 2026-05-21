import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { RouteLocationNormalized } from "vue-router";

/**
 * 标签页信息
 */
export interface TagView {
  path: string;
  title: string;
  name?: string;
  query?: Record<string, string>;
  closable: boolean;
}

const STORAGE_KEY = "admin_tagsview";

/**
 * TagsView 状态管理
 */
export const useTagsViewStore = defineStore("tagsView", () => {
  // 已访问的标签列表
  const visitedTags = ref<TagView[]>([]);

  // 缓存的组件名称列表（用于 keep-alive）
  const cachedViews = ref<string[]>([]);

  // 从 localStorage 恢复状态
  const restoreFromStorage = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as TagView[];
        // 过滤掉无效数据
        visitedTags.value = parsed.filter(
          (tag) => tag.path && tag.title
        );
      }
    } catch {
      // 忽略解析错误
    }
  };

  // 保存到 localStorage
  const saveToStorage = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(visitedTags.value));
    } catch {
      // 忽略存储错误
    }
  };

  // 初始化时恢复
  restoreFromStorage();

  // 添加标签
  const addTag = (route: RouteLocationNormalized) => {
    // 忽略没有标题的路由
    if (!route.meta?.title) return;

    const tag: TagView = {
      path: route.path,
      title: route.meta.title as string,
      name: route.name as string | undefined,
      query: route.query as Record<string, string>,
      closable: route.path !== "/", // 首页不可关闭
    };

    // 检查是否已存在
    const exists = visitedTags.value.find((t) => t.path === tag.path);
    if (!exists) {
      visitedTags.value.push(tag);
      saveToStorage();
    }

    // 添加到缓存
    if (tag.name && !cachedViews.value.includes(tag.name)) {
      cachedViews.value.push(tag.name);
    }
  };

  // 关闭标签
  const closeTag = (path: string) => {
    const index = visitedTags.value.findIndex((t) => t.path === path);
    if (index > -1) {
      const tag = visitedTags.value[index];
      visitedTags.value.splice(index, 1);
      saveToStorage();

      // 从缓存中移除
      if (tag.name) {
        const cacheIndex = cachedViews.value.indexOf(tag.name);
        if (cacheIndex > -1) {
          cachedViews.value.splice(cacheIndex, 1);
        }
      }
    }
  };

  // 关闭其他标签
  const closeOtherTags = (path: string) => {
    visitedTags.value = visitedTags.value.filter(
      (t) => t.path === path || !t.closable
    );
    saveToStorage();

    // 更新缓存
    const tag = visitedTags.value.find((t) => t.path === path);
    if (tag?.name) {
      cachedViews.value = [tag.name];
    } else {
      cachedViews.value = [];
    }
  };

  // 关闭所有标签（保留首页）
  const closeAllTags = () => {
    visitedTags.value = visitedTags.value.filter((t) => !t.closable);
    saveToStorage();
    cachedViews.value = [];
  };

  // 关闭右侧标签
  const closeRightTags = (path: string) => {
    const index = visitedTags.value.findIndex((t) => t.path === path);
    if (index > -1) {
      visitedTags.value = visitedTags.value.filter(
        (t, i) => i <= index || !t.closable
      );
      saveToStorage();

      // 更新缓存
      cachedViews.value = visitedTags.value
        .filter((t) => t.name)
        .map((t) => t.name as string);
    }
  };

  // 获取相邻标签
  const getAdjacentTag = (path: string): TagView | undefined => {
    const index = visitedTags.value.findIndex((t) => t.path === path);
    if (index === -1) return undefined;

    // 优先返回右侧标签，否则返回左侧
    return visitedTags.value[index + 1] || visitedTags.value[index - 1];
  };

  // 当前激活的标签
  const activeTag = computed(() => visitedTags.value.find((t) => t.path));

  return {
    visitedTags,
    cachedViews,
    addTag,
    closeTag,
    closeOtherTags,
    closeAllTags,
    closeRightTags,
    getAdjacentTag,
    activeTag,
  };
});

export default useTagsViewStore;
