## 上下文

本项目需要一套完整的人员选择组件，用于 AI 助手平台演示项目。现有 `people-select` 组件功能不完善，缺少 Popover 快速搜索、三态复选框、头像展示、人员详情卡片等核心功能。

参考 Alon 项目成熟的人员选择组件实现，需要将其迁移至本项目。迁移过程中需要：

1. 遵循本项目统一的树模型类型体系（`TreeNode`、`TreeNodeTree`、`TreeSelectNode`）
2. 遵循本项目统一的 API 响应格式（`ApiResponse`）
3. 遵循本项目的目录结构和命名规范
4. 遵循本项目的后端树模型（`TreeNodeVoMixin`）

### 约束条件

- 后端使用 Python 3.12 + FastAPI + SQLAlchemy 2.0
- 前端使用 Vue 3.5 + TypeScript 5.8 + Vite 6.x
- UI 组件库使用 shadcn-vue + Tailwind CSS v4
- API 路由遵循 `/{module}/{type}/v1/{resource}` 格式
- 人员选择组件放置在 `/iam/console/v1/` 下

## 目标 / 非目标

**目标：**

- 提供完整的人员选择组件，支持 Popover 快速搜索、左右布局选择、三态复选框
- 提供独立的组织选择组件
- 提供统一的组织人员树 API，支持懒加载和搜索
- 遵循本项目现有的类型体系和代码规范

**非目标：**

- 不修改现有的用户/组织数据模型
- 不实现用户头像上传功能（仅展示）
- 不实现人员选择的权限过滤（由调用方控制）

## 决策

### 决策 1：API 路由设计

**选择**：所有人员选择相关 API 放置在 `/iam/console/v1/` 下

**理由**：
- 人员选择是用户控制台功能，需要 JWT 认证
- 与 IAM 模块的用户、组织数据紧密相关
- 遵循本项目的 API 路由规范

**替代方案**：
- 放在 `/iam/inner/v1/` — 不需要认证，但不符合使用场景
- 新建 `/common/console/v1/` — 增加模块复杂度

### 决策 2：组织人员树数据结构

**选择**：扩展 `TreeNodeTreeVo` 添加 `users[]` 字段，形成 `OrgUserTreeVo`

```python
class OrgUserTreeVo(TreeNodeTreeVo):
    has_org_num: int = 0    # 直属子组织数量
    has_user_num: int = 0   # 直属人员数量
    users: list[UserSimpleVo] = []  # 直属人员列表
```

**理由**：
- 遵循本项目现有的 `TreeNodeVoMixin` 体系
- 前端可以直接使用 `TreeNodeTree` 类型
- `has_org_num`/`has_user_num` 用于判断是否需要懒加载

**替代方案**：
- 使用独立的 `OrgUserTreeNode` 类型 — 不遵循项目规范
- 分离组织树和人员列表 API — 增加请求次数

### 决策 3：三态复选框实现

**选择**：在前端 `useOrgPeopleTree` composable 中实现三态逻辑

**三态定义**：
- `checked`：该组织下所有可选用户均已选中
- `indeterminate`：部分可选用户已选中
- `none`：没有可选用户被选中

**理由**：
- 三态逻辑是纯前端交互，无需后端支持
- 参考 Alon 项目的成熟实现
- 支持懒加载场景（展开时动态计算）

### 决策 4：API 封装位置

**选择**：API 封装放在组件目录 `people-select/service.ts`

**理由**：
- 组件自包含，所有相关代码在一处
- 参考 Alon 项目做法，迁移更直观
- 人员选择组件是独立功能单元，API 仅被该组件使用

**替代方案**：
- 放在 `iam/api/` — 符合项目规范但增加跨目录导入

### 决策 5：请求合并与缓存

**选择**：在前端 `service.ts` 中实现请求合并和缓存

**机制**：
- 50ms 内的多个 `fetchUserDetails` 请求合并为一次批量查询
- 使用 `Map` 缓存已获取的用户/组织详情
- 组件销毁时不清除缓存（跨组件复用）

**理由**：
- 避免重复请求同一用户/组织详情
- 批量查询 API `/users/batch` 减少请求次数
- 参考 Alon 项目的实现

### 决策 6：组件目录结构

**选择**：平铺结构，无下级目录

```
components/common/feedback/
├── people-select/              # 人员选择组件
│   ├── types.ts                # 类型定义
│   ├── service.ts              # API 封装
│   ├── useOrgPeopleTree.ts     # 核心逻辑 composable
│   ├── PeopleSelect.vue        # 主入口
│   ├── PeopleSelectView.vue    # 选择视图
│   ├── PeopleSelectDialog.vue  # 弹窗
│   ├── PeopleDisplay.vue       # 详情卡片
│   ├── PeopleAvatar.vue        # 头像
│   ├── OrgTreeNode.vue         # 组织树节点
│   ├── UserTreeNode.vue        # 人员树节点
│   └── index.ts
│
└── org-select/                 # 组织选择组件
    ├── types.ts
    ├── useOrgTree.ts
    ├── OrganizationSelect.vue
    ├── OrganizationSelectView.vue
    ├── OrganizationSelectDialog.vue
    ├── OrgTreeNode.vue         # 独立副本，非复用
    └── index.ts
```

**理由**：
- 平铺结构符合现有 `loading/`、`modal/` 等组件的模式
- 两个组件的 OrgTreeNode.vue 各自独立，不同命名（实际上同名但功能可能略有差异）

### 决策 7：Composable 公共抽取

**选择**：抽取树操作公共逻辑到 `framework/composables/`

**抽取内容**：
- `useTreeExpand.ts` — 树展开/折叠状态管理
- `useTreeCheck.ts` — 复选框三态逻辑

**理由**：
- 人员选择和组织选择都需要树操作逻辑
- 避免重复代码
- 遵循 DRY 原则

## 风险 / 权衡

### 风险 1：大量用户时性能问题

**风险**：组织下用户过多时，加载和渲染可能变慢

**缓解措施**：
- 支持懒加载，按需加载组织下用户
- 搜索时使用分页 API
- 右侧已选列表支持虚拟滚动（可选优化）

### 风险 2：头像加载失败

**风险**：用户头像 URL 可能失效或加载缓慢

**缓解措施**：
- `PeopleAvatar` 组件处理图片加载失败，显示默认图标
- 头像支持 `id` 和 `username` 两种获取方式

### 风险 3：类型定义不一致

**风险**：前端类型与后端 Schema 可能不一致

**缓解措施**：
- 严格对齐本项目 `TreeNode` 类型体系
- 后端 Schema 继承 `TreeNodeVoMixin` / `TreeNodeTreeVo`
- 前端类型导入自 `@/framework/types/tree`

## 迁移计划

### Phase 1：后端 API（前置依赖）

1. 创建 `src/iam/schemas/org_user.py`
2. 扩展 `src/iam/services/organization_service.py`
3. 扩展 `src/iam/services/user_service.py`
4. 创建 `src/iam/controllers/console/org_user_controller.py`

### Phase 2：前端核心

1. 创建 `types.ts`
2. 创建 `service.ts`
3. 创建 `composables/useOrgPeopleTree.ts`
4. 创建 `composables/context.ts`

### Phase 3：前端组件

1. 创建基础组件（`PeopleAvatar`、`OrgTreeNode`、`UserTreeNode`）
2. 创建视图组件（`PeopleSelectView`、`PeopleSelectDialog`）
3. 创建入口组件（`PeopleSelect`、`PeopleDisplay`）

### Phase 4：组织选择器

1. 创建 `OrganizationSelectView.vue`
2. 创建 `OrganizationSelectDialog.vue`
3. 创建 `OrganizationSelect.vue`

### Phase 5：测试与文档

1. 后端单元测试
2. 前端单元测试
3. E2E 测试
4. 更新 `CLAUDE.md`
