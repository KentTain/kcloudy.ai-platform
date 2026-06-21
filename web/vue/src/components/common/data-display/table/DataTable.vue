<script setup lang="ts">
import { type Column, FlexRender } from "@tanstack/vue-table";
import { FileX, Loader2Icon } from "@lucide/vue";
import { computed } from "vue";

import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import ScrollBar from "@/components/ui/scroll-area/ScrollBar.vue";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import DataTablePagination from "./DataTablePagination.vue";
import type { DataTableState } from "./use-data-table";

interface DataTableProps {
  // biome-ignore lint/suspicious/noExplicitAny: DataTable accepts table states with any row shape.
  dataTable: DataTableState<any>;
  fixedLayout?: boolean;
}

const props = defineProps<DataTableProps>();

const visibleColumns = computed(() => props.dataTable.table.getVisibleLeafColumns());
const rows = computed(() => props.dataTable.table.getRowModel().rows ?? []);
const isInitialLoading = computed(() => props.dataTable.loading.value && rows.value.length === 0);
const isRefreshing = computed(() => props.dataTable.loading.value && rows.value.length > 0);
const tableStyle = computed(() => {
  if (!props.fixedLayout) {
    return undefined;
  }
  const minWidth = visibleColumns.value.reduce((total, column) => total + column.getSize(), 0);
  return { minWidth: `${minWidth}px` };
});

// biome-ignore lint/suspicious/noExplicitAny: Column type follows the generic row shape from dataTable.
function getColumnStyle(column: Column<any>) {
  if (!props.fixedLayout) {
    return undefined;
  }
  return { width: `${column.getSize()}px` };
}
</script>

<template>
  <div class="flex flex-col flex-1 overflow-hidden space-y-4">
    <ScrollArea class="rounded-md border custom-scroll-area" style="max-height: calc(100% - 70px)">
      <Table :class="['bg-background', fixedLayout ? 'table-fixed' : '']" :style="tableStyle">
        <colgroup v-if="fixedLayout">
          <col v-for="column in visibleColumns" :key="column.id" :style="getColumnStyle(column)" />
        </colgroup>
        <TableHeader class="sticky top-0 z-50 bg-background/55 backdrop-blur rounded-t-md">
          <TableRow v-for="headerGroup in dataTable.table.getHeaderGroups()" :key="headerGroup.id">
            <TableHead v-for="header in headerGroup.headers" :key="header.id" :style="getColumnStyle(header.column)">
              <FlexRender v-if="!header.isPlaceholder" :render="header.column.columnDef.header" :props="header.getContext()" />
            </TableHead>
          </TableRow>
        </TableHeader>
        <!-- 骨架屏 -->
        <TableBody :class="isRefreshing ? 'relative' : undefined">
          <template v-if="isInitialLoading">
            <TableRow v-for="i in 5" :key="i">
              <TableCell v-for="j in dataTable.table.getAllColumns().length" :key="j"> <Skeleton class="w-full h-8" /> </TableCell>
            </TableRow>
          </template>

          <!-- 数据行 -->
          <template v-if="rows.length">
            <TableRow class="group" v-for="row in rows" :key="row.id" :data-state="row.getIsSelected() && 'selected'">
              <TableCell v-for="cell in row.getVisibleCells()" :key="cell.id" :style="getColumnStyle(cell.column)">
                <FlexRender :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </TableCell>
            </TableRow>
          </template>

          <!-- 空状态 -->
          <TableRow v-else-if="!dataTable.loading.value">
            <TableCell :colspan="dataTable.table.getAllColumns().length" class="h-24 text-center">
              <div class="flex items-center justify-center h-full p-10">
                <div class="flex flex-col items-center">
                  <FileX class="w-12 h-12 text-muted-foreground mb-2" />
                  <span class="text-muted-foreground">无数据</span>
                </div>
              </div>
            </TableCell>
          </TableRow>

          <TableRow v-if="isRefreshing" class="absolute inset-0 z-40 flex items-center justify-center bg-background/60 backdrop-blur-[1px]">
            <TableCell :colspan="dataTable.table.getAllColumns().length" class="border-0 p-0">
              <div class="flex items-center gap-2 rounded-md bg-background px-3 py-2 text-sm text-muted-foreground">
                <Loader2Icon class="size-4 animate-spin" />
                <span>加载中...</span>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <ScrollBar orientation="horizontal" />
    </ScrollArea>

    <DataTablePagination :table="dataTable.table" />
  </div>
</template>
