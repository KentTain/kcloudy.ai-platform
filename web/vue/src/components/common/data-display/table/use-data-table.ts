import {
  type ColumnDef,
  type ColumnPinningState,
  getCoreRowModel,
  getPaginationRowModel,
  type InitialTableState,
  type PaginationState,
  type RowData,
  type Table,
  type Updater,
  useVueTable,
  type VisibilityState,
} from "@tanstack/vue-table";
import { computed, effect, type Ref, ref, shallowRef } from "vue";
import type { SuccessExtra } from "@/framework/types";

export interface DataTableState<TData extends RowData> {
  loading: Ref<boolean>;
  refresh: (firstPage?: boolean, skipLoading?: boolean) => void;
  table: Table<TData>;
}

export function useDataTable<TData extends RowData>(initialOptions: {
  columns: ColumnDef<TData>[];
  columnVisibility?: () => VisibilityState;
  initialState?: InitialTableState;
  remoteFetchFn: (pageQuery: { page: number; page_size: number; signal: AbortSignal }) => Promise<SuccessExtra<TData[]>>;
  enabled?: () => boolean;
}): DataTableState<TData> {
  const dataList = shallowRef<TData[]>([]);
  const loading = ref(true);
  let controller: AbortController | undefined;

  const pagination = ref<PaginationState>({
    pageIndex: 0,
    pageSize: 10,
  });
  const columnPinning = ref<ColumnPinningState>({
    left: [],
    right: [],
  });
  const rowCount = ref<number>(0);
  const columnVisibility = computed(() => initialOptions.columnVisibility?.() ?? {});

  const table = useVueTable({
    columns: initialOptions.columns,
    get data() {
      return dataList.value;
    },
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: initialOptions.initialState,
    manualPagination: true,
    onPaginationChange(updater: Updater<PaginationState>) {
      if (typeof updater === "function") {
        const updatedPagination = updater({
          pageIndex: pagination.value.pageIndex,
          pageSize: pagination.value.pageSize,
        });
        pagination.value.pageIndex = updatedPagination.pageIndex;
        pagination.value.pageSize = updatedPagination.pageSize;
      } else {
        pagination.value.pageIndex = updater.pageIndex;
        pagination.value.pageSize = updater.pageSize;
      }
      refresh();
    },
    get rowCount() {
      return rowCount.value;
    },
    state: {
      get columnPinning() {
        return columnPinning.value;
      },
      get columnVisibility() {
        return columnVisibility.value;
      },
      get pagination() {
        return pagination.value;
      },
    },
  });

  async function remoteFetch(paginationState: PaginationState, skipLoading: boolean = false) {
    if (!skipLoading) {
      loading.value = true;
    }
    // 远程查询数据，tanstack第一页下标为0需要加
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();
    await initialOptions
      .remoteFetchFn({ page: paginationState.pageIndex + 1, page_size: paginationState.pageSize, signal: controller.signal })
      .then((res) => {
        dataList.value = res.data;
        rowCount.value = res.total;
      })
      .finally(() => {
        if (!skipLoading) {
          loading.value = false;
        }
      });
  }

  effect(() => {
    if (initialOptions.enabled && !initialOptions.enabled()) return;
    refresh(true);
  });

  async function refresh(firstPage: boolean = false, skipLoading: boolean = false) {
    // 第一页
    const pagination = firstPage ? { pageIndex: 0, pageSize: 10 } : table.getState().pagination;
    await remoteFetch(pagination, skipLoading);
  }

  return { loading, refresh, table };
}
