<script setup lang="ts">
/**
 * CommonTable 数据表格组件
 * 基于 shadcn-vue Table 原语，封装 columns/loading/empty
 */
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { ArrowUpIcon, ArrowDownIcon, LoaderIcon } from "@lucide/vue";

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

withDefaults(defineProps<Props>(), {
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

const alignClass = (align?: "left" | "center" | "right") => {
  switch (align) {
    case "center":
      return "text-center";
    case "right":
      return "text-right";
    default:
      return "text-left";
  }
};
</script>

<template>
  <div class="overflow-x-auto rounded-md border" v-if="border">
    <Table>
      <TableHeader>
        <TableRow class="bg-muted/50 hover:bg-muted/50">
          <TableHead
            v-for="column in columns"
            :key="column.key"
            :style="{ width: column.width }"
            :class="cn(alignClass(column.align))"
          >
            <div
              :class="cn(
                'flex items-center gap-1',
                column.sortable && 'cursor-pointer select-none hover:text-primary'
              )"
              @click="handleSort(column)"
            >
              <span>{{ column.title }}</span>
              <span v-if="column.sortable" class="flex flex-col">
                <ArrowUpIcon
                  :class="cn(
                    'size-3 -mb-1',
                    sortKey === column.key && sortOrder === 'asc' ? 'text-primary' : 'text-muted-foreground/50'
                  )"
                />
                <ArrowDownIcon
                  :class="cn(
                    'size-3',
                    sortKey === column.key && sortOrder === 'desc' ? 'text-primary' : 'text-muted-foreground/50'
                  )"
                />
              </span>
            </div>
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-if="loading">
          <TableCell :colspan="columns.length" class="h-24 text-center">
            <div class="flex items-center justify-center gap-2 text-muted-foreground">
              <LoaderIcon class="size-4 animate-spin" />
              <span>加载中...</span>
            </div>
          </TableCell>
        </TableRow>
        <TableRow v-else-if="data.length === 0">
          <TableCell :colspan="columns.length" class="h-24 text-center text-muted-foreground">
            {{ emptyText }}
          </TableCell>
        </TableRow>
        <template v-else>
          <TableRow
            v-for="(row, index) in data"
            :key="index"
            :class="cn(
              stripe && index % 2 === 1 && 'bg-muted/30',
              'hover:bg-primary/5'
            )"
          >
            <TableCell
              v-for="column in columns"
              :key="column.key"
              :class="alignClass(column.align)"
            >
              <slot :name="column.key" :row="row" :value="row[column.key]">
                {{ row[column.key] }}
              </slot>
            </TableCell>
          </TableRow>
        </template>
      </TableBody>
    </Table>
  </div>
  <Table v-else>
    <TableHeader>
      <TableRow class="bg-muted/50 hover:bg-muted/50">
        <TableHead
          v-for="column in columns"
          :key="column.key"
          :style="{ width: column.width }"
          :class="cn(alignClass(column.align))"
        >
          <div
            :class="cn(
              'flex items-center gap-1',
              column.sortable && 'cursor-pointer select-none hover:text-primary'
            )"
            @click="handleSort(column)"
          >
            <span>{{ column.title }}</span>
            <span v-if="column.sortable" class="flex flex-col">
              <ArrowUpIcon
                :class="cn(
                  'size-3 -mb-1',
                  sortKey === column.key && sortOrder === 'asc' ? 'text-primary' : 'text-muted-foreground/50'
                )"
              />
              <ArrowDownIcon
                :class="cn(
                  'size-3',
                  sortKey === column.key && sortOrder === 'desc' ? 'text-primary' : 'text-muted-foreground/50'
                )"
              />
            </span>
          </div>
        </TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow v-if="loading">
        <TableCell :colspan="columns.length" class="h-24 text-center">
          <div class="flex items-center justify-center gap-2 text-muted-foreground">
            <LoaderIcon class="size-4 animate-spin" />
            <span>加载中...</span>
          </div>
        </TableCell>
      </TableRow>
      <TableRow v-else-if="data.length === 0">
        <TableCell :colspan="columns.length" class="h-24 text-center text-muted-foreground">
          {{ emptyText }}
        </TableCell>
      </TableRow>
      <template v-else>
        <TableRow
          v-for="(row, index) in data"
          :key="index"
          :class="cn(
            stripe && index % 2 === 1 && 'bg-muted/30',
            'hover:bg-primary/5'
          )"
        >
          <TableCell
            v-for="column in columns"
            :key="column.key"
            :class="alignClass(column.align)"
          >
            <slot :name="column.key" :row="row" :value="row[column.key]">
              {{ row[column.key] }}
            </slot>
          </TableCell>
        </TableRow>
      </template>
    </TableBody>
  </Table>
</template>
