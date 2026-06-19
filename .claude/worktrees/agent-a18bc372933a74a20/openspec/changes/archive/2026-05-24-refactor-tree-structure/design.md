## Context

当前项目的树结构实现分散在多个模块中：

- **后端**：`framework/database/mixins/tree.py` 提供简单的 `TreeMixin`（仅 3 个字段），`framework/utils/tree_util.py` 提供构建方法
- **前端**：`components/CommonCheckboxTree.vue` 内嵌 `TreeNode` 接口，与后端字段不对应

参考 Alon 项目的 `TreeNodeMixin` 实现，包含 7 个树字段和完整的 CRUD 方法，支持事件发布、级联更新、软删除等特性。

## Goals / Non-Goals

**Goals:**

1. 后端提供完整的 `TreeNodeMixin`，支持树字段的自动维护和级联更新
2. 后端提供 `TreeNodeVo` 基类，统一树节点响应格式
3. 前端提供统一的树类型定义和工具函数
4. 前端提供可复用的树组件体系（CommonTree、CommonSelectTree、CommonTreeList）
5. 部门模块作为首个使用新树结构的业务模块

**Non-Goals:**

1. 不修改现有 API 的路径和认证方式
2. 不实现拖拽排序功能（可选，暂不实现）
3. 不重构其他可能使用树结构的模块（如权限树）

## Decisions

### D1: TreeNodeMixin 字段设计

**决定**：采用 Alon 的字段命名和设计

| 字段 | 类型 | 说明 |
|------|------|------|
| parent_id | str | 父节点ID，根节点为 `DEFAULT_TREE_ROOT_ID` |
| tree_leaf | bool | 是否为叶子节点 |
| tree_level | int | 树层级（根节点为 0） |
| tree_sort | int | 当前层级排序号 |
| tree_sorts | str | 排序路径（如 `0000000030,0000000015,`） |
| tree_names | str | 名称路径（如 `集团/研发部/前端组`） |
| parent_ids | str | 父ID路径（如 `root-id,parent1-id,parent2-id,`） |

**备选方案**：

- 方案 A（已选）：保持 Alon 命名，便于参考和迁移
- 方案 B：简化命名（sort、sort_path 等），但与参考项目不一致

**理由**：保持与 Alon 一致，减少学习成本，便于后续参考其实现细节。

### D2: TreeNodeMixin 内置 CRUD 方法

**决定**：在 Mixin 中提供完整的 CRUD 方法

```python
class TreeNodeMixin:
    @classmethod
    async def create_node(cls, session, source, ...) -> Self: ...
    @classmethod
    async def update_node(cls, session, id, source, ...) -> Self: ...
    @classmethod
    async def delete_node(cls, session, id, ...) -> int: ...
    @classmethod
    async def list_nodes(cls, session, ...) -> Sequence[Self]: ...
    @classmethod
    def build_tree(cls, nodes, parent_id, ...) -> list[Any]: ...
```

**理由**：

- 避免每个业务模块重复实现树逻辑
- 确保树字段的一致性维护
- 支持事件发布和级联更新

### D3: 事件发布机制

**决定**：在 `TreeNodeMixin` 中集成事件发布

```python
@classmethod
async def _publish_node_event(cls, event_type: EventType, data: Any) -> None:
    publisher = getattr(cls, "_publish_event", None)
    if publisher:
        await publisher(event_type, data)
```

**理由**：

- 与 Alon 一致
- 业务模块可通过定义 `_publish_event` 方法启用事件发布
- 不强制要求事件发布，向后兼容

### D4: 前端组件体系

**决定**：创建三层组件体系

```
CommonTree.vue (基础展示树)
├── 提供展开/折叠、节点渲染、样式定制
└── 通过 slot 支持自定义节点内容

CommonCheckboxTree.vue (勾选树)
├── 继承 CommonTree 的基础能力
├── 增加勾选逻辑（全选/半选/单选）
└── 增加搜索过滤

CommonSelectTree.vue (下拉选择树)
├── 基于 CommonTree
└── 增加下拉弹层，支持单选/多选

CommonTreeList.vue (列表树)
├── 基于 CommonTree
└── 每个节点带操作按钮
```

**备选方案**：

- 方案 A（已选）：继承/组合模式，共享基础能力
- 方案 B：每个组件独立实现，灵活性更高但维护成本大

**理由**：共享基础能力，减少代码重复，保持一致性。

### D5: 数据库迁移策略

**决定**：创建迁移脚本，为现有数据填充新字段

1. 添加新字段（允许 NULL 或默认值）
2. 使用 Python 脚本递归计算并填充字段
3. 添加 NOT NULL 约束和索引

**理由**：

- 确保现有数据完整性
- 避免手动数据修复
- 支持回滚

## Risks / Trade-offs

### R1: 数据迁移耗时

**风险**：如果部门数据量大，迁移可能耗时较长

**缓解措施**：
- 在业务低峰期执行迁移
- 分批处理数据
- 提供进度监控

### R2: 前端组件重构影响

**风险**：重构 `CommonCheckboxTree` 可能影响现有使用方

**缓解措施**：
- 保持组件 Props 接口兼容
- 增加过渡期警告
- 更新文档说明迁移方式

### R3: 树字段冗余

**风险**：`tree_sorts`、`tree_names`、`parent_ids` 存在数据冗余

**缓解措施**：
- 通过 `TreeNodeMixin` 方法统一维护，避免不一致
- 接受冗余换取查询性能和实现简洁性

## Migration Plan

### Phase 1: 后端基础设施

1. 创建 `framework/core/constants.py`（树常量）
2. 重写 `framework/database/mixins/tree.py`（TreeNodeMixin）
3. 创建 `framework/schemas/tree.py`（TreeNodeVo）
4. 简化 `framework/utils/tree_util.py`

### Phase 2: 业务模块集成

1. 更新 `iam/models/department.py`
2. 更新 `iam/schemas/department.py`
3. 简化 `iam/services/department_service.py`
4. 创建数据库迁移脚本

### Phase 3: 前端基础设施

1. 创建 `framework/types/tree.ts`
2. 创建 `framework/utils/tree.ts`
3. 更新 `framework/types/index.ts`

### Phase 4: 前端组件

1. 创建 `CommonTree.vue`
2. 重构 `CommonCheckboxTree.vue`
3. 创建 `CommonSelectTree.vue`
4. 创建 `CommonTreeList.vue`

### Phase 5: 前端业务集成

1. 更新 `iam/types/index.ts`
2. 更新 `iam/components/DepartmentTree.vue`

### Phase 6: 文档更新

1. 更新各层级 CLAUDE.md 文档
