# Framework 模块测试

本文件为 Claude Code 在 Framework 模块测试目录中工作时提供指导。

## 测试目录结构

```
tests/framework/
├── components/           # 组件测试
│   ├── layout.test.ts    # 布局组件测试
│   └── ui.test.ts        # UI 组件测试
├── stores/               # Store 测试
│   └── permission.test.ts # 权限 Store 测试
└── design-tokens.test.ts # 设计令牌测试
```

## 运行测试

```bash
# 运行所有 Framework 测试
pnpm test:unit tests/framework/ --run

# 运行组件测试
pnpm test:unit tests/framework/components/ --run

# 运行 Store 测试
pnpm test:unit tests/framework/stores/ --run

# 运行设计令牌测试
pnpm test:unit tests/framework/design-tokens.test.ts --run

# 生成覆盖率报告
pnpm test:unit tests/framework/ --run --coverage
```

## 测试分类

### 组件测试

| 目录 | 说明 |
|------|------|
| layout.test.ts | AdminLayout、AppSidebar、AppNavbar、AppTagsView、AppMain |
| ui.test.ts | AppButton、AppCard、AppInput、AppLoading、AppModal |

### Store 测试

| 目录 | 说明 |
|------|------|
| permission.test.ts | AppStore、UserStore、PermissionStore |

### 设计令牌测试

| 文件 | 说明 |
|------|------|
| design-tokens.test.ts | 颜色、字体、圆角、阴影令牌验证 |

## 测试工具

### Vue Test Utils

```typescript
import { mount } from "@vue/test-utils";
import MyComponent from "@/framework/components/MyComponent.vue";

test("renders correctly", () => {
  const wrapper = mount(MyComponent);
  expect(wrapper.text()).toContain("expected text");
});
```

### Pinia Testing

```typescript
import { setActivePinia, createPinia } from "pinia";
import { useAppStore } from "@/framework/stores";

beforeEach(() => {
  setActivePinia(createPinia());
});

test("store works", () => {
  const store = useAppStore();
  expect(store.sidebarCollapsed).toBe(false);
});
```

### Mock vue-router

```typescript
import { vi } from "vitest";

vi.mock("vue-router", () => ({
  useRoute: () => ({ path: "/" }),
  useRouter: () => ({ push: vi.fn() }),
}));
```

### Mock localStorage

```typescript
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => { store[key] = value; }),
    removeItem: vi.fn((key) => { delete store[key]; }),
    clear: vi.fn(() => { store = {}; }),
  };
})();

Object.defineProperty(window, "localStorage", { value: localStorageMock });
```

## 测试覆盖

| 模块 | 组件测试 | Store 测试 |
|------|----------|------------|
| layouts | ✅ | - |
| components/ui | ✅ | - |
| stores | - | ✅ |
| styles | ✅ | - |

## 最佳实践

1. 每个组件至少有一个渲染测试
2. 测试组件的所有 props 变体
3. 测试用户交互（点击、输入等）
4. Mock 外部依赖（router、localStorage）
5. 测试边界条件和错误状态
