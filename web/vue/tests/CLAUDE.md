# 测试目录指南

本文件为 Claude Code 在 Vue 前端测试目录中工作时提供指导。

## 测试目录结构

```text
tests/
├── components/            # 通用组件测试
├── ai/                    # AI 模块测试
│   ├── components/        # 组件测试
│   ├── composables/       # Composable 测试
│   ├── pages/             # 页面测试
│   └── stores/            # Store 测试
├── iam/                   # IAM 模块测试
│   ├── api/               # API 测试
│   ├── components/        # 组件测试
│   ├── stores/            # Store 测试
│   └── router.test.ts     # 路由测试
├── framework/             # Framework 模块测试
│   ├── components/        # 组件测试
│   ├── composables/       # Composable 测试
│   ├── events/            # 事件测试
│   ├── module/            # 模块系统测试
│   ├── stores/            # Store 测试
│   └── utils/             # 工具函数测试
├── tenant/                # Tenant 模块测试
└── demo/                  # Demo 模块测试
```

## 运行测试

```bash
# 运行所有测试
pnpm test:unit

# 详细输出
pnpm test:unit -- --run

# 运行特定模块测试
pnpm test:unit tests/ai/ --run
pnpm test:unit tests/iam/ --run
pnpm test:unit tests/framework/ --run
pnpm test:unit tests/demo/ --run

# 生成覆盖率报告
pnpm test:unit -- --coverage
```

## 模块测试说明

### AI 模块测试

| 目录 | 说明 |
|------|------|
| components/ | ModelSelector、ToolCallItem 组件测试 |
| composables/ | useChat 组合式函数测试 |
| pages/ | ChatPage、ConversationListPage 页面测试 |
| stores/ | conversation Store 测试 |

### IAM 模块测试

| 目录 | 说明 |
|------|------|
| api/ | auth、user、role、permission、department API 测试 |
| components/ | DepartmentTree、PermissionTree 组件测试 |
| stores/ | auth、user、role、department Store 测试 |

### Framework 模块测试

| 目录 | 说明 |
|------|------|
| components/ | AppPage、AppNavbar、CommandPalette 等组件测试 |
| composables/ | useMenuPermission 组合式函数测试 |
| events/ | EventBus 事件系统测试 |
| module/ | 模块注册、路由解析、动态路由测试 |
| stores/ | app、menu、permission Store 测试 |
| utils/ | tree 工具函数测试 |

## 测试标记

| 标记 | 说明 |
|------|------|
| unit | 单元测试 |
| integration | 集成测试 |
| slow | 慢测试 |

## 常用 Fixtures

| Fixture | 说明 |
|---------|------|
| wrapper | Vue 组件包装器 |
| pinia | Pinia 测试实例 |
| router | Vue Router 测试实例 |
