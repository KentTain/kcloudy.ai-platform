<script setup lang="ts">
/**
 * AppTagsView 标签页组件
 */
import { watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useTagsViewStore } from "@/framework/stores";

const route = useRoute();
const router = useRouter();
const tagsViewStore = useTagsViewStore();

// 监听路由变化，自动添加标签
watch(
  () => route.path,
  () => {
    tagsViewStore.addTag(route);
  },
  { immediate: true }
);

const isActive = (path: string) => route.path === path;

const handleClick = (path: string) => {
  router.push(path);
};

const handleClose = (path: string, event: MouseEvent) => {
  event.stopPropagation();

  // 获取相邻标签
  const nextTag = tagsViewStore.getAdjacentTag(path);

  // 关闭当前标签
  tagsViewStore.closeTag(path);

  // 如果关闭的是当前激活的标签，跳转到相邻标签
  if (route.path === path && nextTag) {
    router.push(nextTag.path);
  }
};
</script>

<template>
  <div class="app-tagsview">
    <div class="app-tagsview__container">
      <div
        v-for="tag in tagsViewStore.visitedTags"
        :key="tag.path"
        :class="['app-tagsview__tag', { 'app-tagsview__tag--active': isActive(tag.path) }]"
        @click="handleClick(tag.path)"
      >
        <span class="app-tagsview__tag-text">{{ tag.title }}</span>
        <span
          v-if="tag.closable"
          class="app-tagsview__tag-close"
          @click="handleClose(tag.path, $event)"
        >
          <svg viewBox="0 0 24 24" width="12" height="12">
            <path fill="currentColor" d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
          </svg>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-tagsview {
  display: flex;
  align-items: center;
  padding: 0 0.5rem;
  background-color: var(--color-surface-raised);
  border-bottom: 1px solid var(--color-border);
}

.app-tagsview__container {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  overflow-x: auto;
}

.app-tagsview__tag {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  font-size: 0.75rem;
  color: var(--color-text-muted);
  background-color: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.app-tagsview__tag:hover {
  color: var(--color-primary);
}

.app-tagsview__tag--active {
  color: var(--color-primary);
  background-color: var(--color-primary-subtle);
  border-bottom: 2px solid var(--color-primary);
}

.app-tagsview__tag-close {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color var(--transition-fast);
}

.app-tagsview__tag-close:hover {
  background-color: rgba(0, 0, 0, 0.1);
}
</style>
