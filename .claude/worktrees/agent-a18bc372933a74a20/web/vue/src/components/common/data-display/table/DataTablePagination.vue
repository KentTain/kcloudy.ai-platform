<script setup lang="ts">
import type { RowData, Table } from "@tanstack/vue-table";
import { ChevronLeftIcon, ChevronRightIcon, ChevronsLeftIcon, ChevronsRightIcon } from "@lucide/vue";
import type { AcceptableValue } from "reka-ui";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface DataTablePaginationProps {
  table: Table<RowData>;
}
defineProps<DataTablePaginationProps>();
</script>

<template>
  <div class="flex items-center justify-between px-2">
    <div class="flex-1 text-sm text-muted-foreground"><!-- 此处可实现多选显示 --></div>
    <div class="flex items-center space-x-6 lg:space-x-4">
      <div class="flex w-[100px] items-center justify-center text-sm font-medium">总条数：{{ table.getRowCount() }}</div>
      <div class="flex items-center space-x-2">
        <p class="text-sm font-medium">每页条数</p>
        <Select :model-value="`${table.getState().pagination.pageSize}`" @update:model-value="(value: AcceptableValue) => table.setPageSize(value as number)">
          <SelectTrigger class="h-8 w-[70px]" style="height: 32px"> <SelectValue :placeholder="`${table.getState().pagination.pageSize}`" /> </SelectTrigger>
          <SelectContent side="top">
            <SelectItem v-for="pageSize in [10, 20, 30, 40, 50]" :key="pageSize" :value="`${pageSize}`"> {{ pageSize }} </SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div class="flex w-[100px] items-center justify-center text-sm font-medium">
        页数 {{ table.getState().pagination.pageIndex + 1 }} / {{ table.getPageCount() }}
      </div>
      <div class="flex items-center space-x-2">
        <Button variant="outline" class="hidden h-8 w-8 p-0 lg:flex" :disabled="!table.getCanPreviousPage()" @click="table.setPageIndex(0)">
          <span class="sr-only">第一页</span>
          <ChevronsLeftIcon class="h-4 w-4" />
        </Button>
        <Button variant="outline" class="h-8 w-8 p-0" :disabled="!table.getCanPreviousPage()" @click="table.previousPage()">
          <span class="sr-only">上一页</span>
          <ChevronLeftIcon class="h-4 w-4" />
        </Button>
        <Button variant="outline" class="h-8 w-8 p-0" :disabled="!table.getCanNextPage()" @click="table.nextPage()">
          <span class="sr-only">下一页</span>
          <ChevronRightIcon class="h-4 w-4" />
        </Button>
        <Button variant="outline" class="hidden h-8 w-8 p-0 lg:flex" :disabled="!table.getCanNextPage()" @click="table.setPageIndex(table.getPageCount() - 1)">
          <span class="sr-only">最后一页</span>
          <ChevronsRightIcon class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
</template>
