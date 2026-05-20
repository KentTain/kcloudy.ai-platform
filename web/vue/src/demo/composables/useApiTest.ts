// src/demo/composables/useApiTest.ts
import { ref } from "vue";
import type { ApiTestResult } from "../types";

export function useApiTest(apiFn?: () => Promise<unknown>) {
  const result = ref<ApiTestResult>({
    status: "idle",
    data: null,
    error: null,
    duration: null,
  });

  async function execute(fn?: () => Promise<unknown>) {
    const fnToCall = fn ?? apiFn;
    if (!fnToCall) return;

    result.value = { status: "loading", data: null, error: null, duration: null };
    const start = performance.now();

    try {
      const data = await fnToCall();
      const duration = performance.now() - start;
      result.value = { status: "success", data, error: null, duration };
    } catch (e: unknown) {
      const duration = performance.now() - start;
      const error = e instanceof Error ? e.message : "请求失败";
      result.value = { status: "error", data: null, error, duration };
    }
  }

  function reset() {
    result.value = { status: "idle", data: null, error: null, duration: null };
  }

  return { result, execute, reset };
}
