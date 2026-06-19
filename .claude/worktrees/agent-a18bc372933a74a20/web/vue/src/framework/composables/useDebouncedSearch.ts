import { ref, watch, type Ref } from "vue";

/**
 * 防抖搜索 composable
 * @param delay 防抖延迟时间（毫秒）
 */
export function useDebouncedSearch(delay = 300) {
  const searchText = ref("");
  const debouncedText = ref("");
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  watch(searchText, (newVal) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      debouncedText.value = newVal;
    }, delay);
  });

  const clearSearch = () => {
    searchText.value = "";
    debouncedText.value = "";
    if (timeoutId) {
      clearTimeout(timeoutId);
    }
  };

  return {
    searchText,
    debouncedText,
    clearSearch,
  };
}

/**
 * 创建防抖函数
 */
export function createDebounce<T extends (...args: any[]) => any>(
  fn: T,
  delay = 300
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout> | null = null;

  return (...args: Parameters<T>) => {
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    timeoutId = setTimeout(() => {
      fn(...args);
    }, delay);
  };
}
