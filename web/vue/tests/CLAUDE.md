# CLAUDE.md

本文件为 Claude Code 在 Vue 前端测试目录中工作时提供指导。

## 测试目录结构

```text
tests/
├── demo/                      # Demo 模块测试
│   ├── components/            # 组件测试
│   ├── composables/           # Composable 测试
│   └── stores/                # Store 测试
├── framework/                 # Framework 模块测试
│   ├── components/            # 组件测试
│   ├── composables/           # Composable 测试
│   └── stores/                # Store 测试
└── README.md                  # 测试说明文档
```

## 运行测试

```bash
# 运行所有测试
pnpm test:unit

# 详细输出
pnpm test:unit -- --run

# 运行特定模块测试
pnpm test:unit tests/demo/ --run
pnpm test:unit tests/framework/ --run

# 生成覆盖率报告
pnpm test:unit -- --coverage
```

## 测试规范

### Demo 模块测试

| 目录         | 说明                 |
|--------------|----------------------|
| components/  | 组件测试             |
| composables/ | Composable 函数测试  |
| stores/      | Pinia Store 测试     |

### Framework 模块测试

| 目录         | 说明                 |
|--------------|----------------------|
| components/  | 组件测试             |
| composables/ | Composable 函数测试  |
| stores/      | Pinia Store 测试     |

## 测试标记

| 标记       | 说明     |
|------------|----------|
| unit       | 单元测试 |
| integration | 集成测试 |
| slow       | 慢测试   |

## 常用 Fixtures

| Fixture | 说明               |
|---------|--------------------|
| wrapper | Vue 组件包装器     |
| pinia   | Pinia 测试实例     |
| router  | Vue Router 测试实例 |

## 详细文档

- **Demo 测试**：[demo/CLAUDE.md](demo/CLAUDE.md)
- **Framework 测试**：[framework/CLAUDE.md](framework/CLAUDE.md)
