<script setup lang="ts">
/**
 * AppTable 数据表格组件
 */
import { computed } from "vue";

interface Column {
  key: string;
  title: string;
  width?: string;
  align?: "left" | "center" | "right";
  sortable?: boolean;
}

interface Props {
  columns: Column[];
  data: Record<string, any>[];
  loading?: boolean;
  stripe?: boolean;
  border?: boolean;
  emptyText?: string;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  stripe: false,
  border: false,
  emptyText: "暂无数据",
});

const emit = defineEmits<{
  sort: [{ key: string; order: "asc" | "desc" }];
}>();

const sortKey = defineModel<string>("sortKey");
const sortOrder = defineModel<"asc" | "desc">("sortOrder");

const handleSort = (column: Column) => {
  if (!column.sortable) return;

  if (sortKey.value === column.key) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortKey.value = column.key;
    sortOrder.value = "asc";
  }

  emit("sort", { key: sortKey.value, order: sortOrder.value! });
};

const getAlignClass = (align?: "left" | "center" | "right") =>
  align ? `app-table__cell--${align}` : "";
</script>

<template>
  <div class="app-table-wrapper">
    <table :class="['app-table', { 'app-table--stripe': stripe, 'app-table--border': border }]">
      <thead class="app-table__head">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :style="{ width: column.width }"
            :class="['app-table__cell', getAlignClass(column.align)]"
          >
            <div
              :class="['app-table__header', { 'app-table__header--sortable': column.sortable }]"
              @click="handleSort(column)"
            >
              <span>{{ column.title }}</span>
              <span v-if="column.sortable" class="app-table__sort">
                <svg
                  :class="[
                    'app-table__sort-icon',
                    { 'app-table__sort-icon--active': sortKey === column.key && sortOrder === 'asc' },
                  ]"
                  viewBox="0 0 24 24"
                  width="12"
                  height="12"
                >
                  <path fill="currentColor" d="M7 14l5-5 5 5z" />
                </svg>
                <svg
                  :class="[
                    'app-table__sort-icon',
                    { 'app-table__sort-icon--active': sortKey === column.key && sortOrder === 'desc' },
                  ]"
                  viewBox="0 0 24 24"
                  width="12"
                  height="12"
                >
                  <path fill="currentColor" d="M7 10l5 5 5-5z" />
                </svg>
              </span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody class="app-table__body">
        <tr v-if="loading">
          <td :colspan="columns.length" class="app-table__loading">
            <span class="app-table__loading-text">加载中...</span>
          </td>
        </tr>
        <tr v-else-if="data.length === 0">
          <td :colspan="columns.length" class="app-table__empty">
            {{ emptyText }}
          </td>
        </tr>
        <tr v-else v-for="(row, index) in data" :key="index" class="app-table__row">
          <td
            v-for="column in columns"
            :key="column.key"
            :class="['app-table__cell', getAlignClass(column.align)]"
          >
            <slot :name="column.key" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.app-table-wrapper {
  overflow-x: auto;
}

.app-table {
  width: 100%;
  border-collapse: collapse;
  background-color: var(--color-surface-raised);
}

.app-table--border {
  border: 1px solid var(--color-border);
}

.app-table--border .app-table__cell {
  border: 1px solid var(--color-border);
}

.app-table__head {
  background-color: var(--color-surface);
}

.app-table__cell {
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.app-table__cell--center {
  text-align: center;
}

.app-table__cell--right {
  text-align: right;
}

.app-table__header {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-weight: 600;
  color: var(--color-text);
}

.app-table__header--sortable {
  cursor: pointer;
  user-select: none;
}

.app-table__header--sortable:hover {
  color: var(--color-primary);
}

.app-table__sort {
  display: flex;
  flex-direction: column;
  gap: -4px;
}

.app-table__sort-icon {
  color: var(--color-text-disabled);
  transition: color var(--transition-fast);
}

.app-table__sort-icon--active {
  color: var(--color-primary);
}

.app-table--stripe .app-table__row:nth-child(even) {
  background-color: var(--color-surface);
}

.app-table__row:hover {
  background-color: var(--color-primary-subtle);
}

.app-table__loading,
.app-table__empty {
  padding: 2rem;
  text-align: center;
  color: var(--color-text-muted);
}

.app-table__loading-text {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.app-table__loading-text::before {
  content: "";
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--color-primary);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
