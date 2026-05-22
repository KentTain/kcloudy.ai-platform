# Composables 组合式函数目录

## 概述

`composables/` 目录存放 Vue 3 组合式函数（Composables），用于封装可复用的响应式逻辑。这是 Vue 3 Composition API 的核心特性之一。

## 目录结构

```text
composables/
├── useAsync.ts                # 异步操作封装
├── useDebounce.ts             # 防抖函数
├── useLocalStorage.ts         # 本地存储
├── usePagination.ts           # 分页逻辑
├── usePermission.ts           # 权限检查
├── useTheme.ts                # 主题切换
└── CLAUDE.md                  # 本文档
```

## 常用 Composables

| 函数 | 说明 | 用途 |
|------|------|------|
| `useAsync` | 异步状态管理 | API 调用、加载状态 |
| `useDebounce` | 防抖处理 | 搜索输入、窗口调整 |
| `useLocalStorage` | 本地存储响应式封装 | 持久化数据 |
| `usePagination` | 分页逻辑 | 列表分页 |
| `usePermission` | 权限检查 | 按钮级权限控制 |
| `useTheme` | 主题切换 | 深色/浅色模式 |

## 开发规范

### 命名规范

- 使用 `use` 前缀命名（如 `useDebounce`）
- 文件名与函数名一致
- 使用 camelCase

### 函数结构

```typescript
// composables/useExample.ts
import { ref, computed, onMounted, onUnmounted, type Ref } from "vue";

/**
 * 示例组合式函数
 * @param initialValue 初始值
 * @returns 响应式状态和方法
 */
export function useExample(initialValue: string) {
  // 响应式状态
  const value = ref(initialValue);
  const loading = ref(false);

  // 计算属性
  const doubled = computed(() => value.value + value.value);

  // 方法
  function update(newValue: string) {
    value.value = newValue;
  }

  // 生命周期
  onMounted(() => {
    // 初始化逻辑
  });

  onUnmounted(() => {
    // 清理逻辑
  });

  // 返回值
  return {
    value,
    loading,
    doubled,
    update,
  };
}
```

### 最佳实践

1. **单一职责**
   - 每个 composable 只做一件事
   - 避免过于复杂的封装

2. **参数设计**
   - 使用 TypeScript 类型约束
   - 提供合理的默认值
   - 接收 `ref` 或 `reactive` 作为参数

3. **返回值设计**
   - 返回对象而非数组（便于扩展）
   - 使用描述性命名
   - 包含状态和方法

4. **副作用管理**
   - 在 `onUnmounted` 中清理副作用
   - 清理定时器、事件监听器

## 使用示例

### useAsync

```typescript
import { useAsync } from "@/composables/useAsync";

const { data, loading, error, execute } = useAsync(async () => {
  const response = await fetch("/api/data");
  return response.json();
});

// 执行
await execute();
```

### useDebounce

```typescript
import { useDebounce } from "@/composables/useDebounce";

const searchTerm = ref("");
const debouncedSearch = useDebounce(searchTerm, 300);

watch(debouncedSearch, (value) => {
  // 300ms 后执行搜索
  search(value);
});
```

### useLocalStorage

```typescript
import { useLocalStorage } from "@/composables/useLocalStorage";

// 自动同步到 localStorage
const theme = useLocalStorage("theme", "light");

// 修改会自动持久化
theme.value = "dark";
```

### usePagination

```typescript
import { usePagination } from "@/composables/usePagination";

const { page, pageSize, total, setPage, setTotal } = usePagination({
  defaultPage: 1,
  defaultPageSize: 10,
});

// 监听分页变化
watch([page, pageSize], () => {
  fetchData();
});
```

## 与其他模块的关系

| 模块 | 关系 |
|------|------|
| `framework/stores/` | Pinia Store 用于全局状态，Composables 用于局部逻辑 |
| `framework/api/` | Composables 可以调用 API，封装业务逻辑 |
| `components/` | Composables 提供组件所需的可复用逻辑 |

## 何时使用 Composable vs Store

| 场景 | 推荐 |
|------|------|
| 组件内局部状态 | Composable |
| 跨组件共享状态 | Pinia Store |
| 一次性的逻辑封装 | Composable |
| 需要持久化的全局状态 | Pinia Store |
| API 调用 + 状态 | Composable (useAsync) |

## 注意事项

1. 避免在 composable 中直接修改全局状态
2. 保持函数纯净，副作用明确
3. 提供清晰的 TypeScript 类型
4. 添加 JSDoc 注释说明用法
