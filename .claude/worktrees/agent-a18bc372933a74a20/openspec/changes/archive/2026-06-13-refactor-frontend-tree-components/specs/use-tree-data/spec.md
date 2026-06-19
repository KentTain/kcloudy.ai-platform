## 新增需求

### 需求:数据转换能力

useTreeData 必须提供数据转换能力，将业务数据转换为 TreeSelectNode 格式。

#### 场景:默认字段映射
- **当** 开发者使用 useTreeData({ source: departments })
- **那么** 自动将 source 数据转换为 TreeSelectNode，使用 id/name/children 默认映射

#### 场景:自定义字段映射
- **当** 开发者使用 useTreeData({ source: menus, fieldMapping: { name: 'label' } })
- **那么** 使用自定义映射转换数据

#### 场景:响应式数据源
- **当** source 为 Ref 或响应式数组
- **那么** treeData 随 source 变化自动更新

### 需求:选中状态管理

useTreeData 必须提供选中状态管理能力，支持单选和多选模式。

#### 场景:单选模式
- **当** mode = 'single' 且选中节点
- **那么** selectedIds 包含单个 ID，之前选中的 ID 被移除

#### 场景:多选模式
- **当** mode = 'multiple' 且选中多个节点
- **那么** selectedIds 包含所有选中 ID

#### 场景:modelValue 双向绑定
- **当** 外部 modelValue 变化
- **那么** selectedIds 同步更新

#### 场景:获取选中节点
- **当** 开发者访问 selectedNodes
- **那么** 返回完整的选中节点对象数组

### 需求:搜索过滤能力

useTreeData 必须提供搜索过滤能力，支持关键词过滤树节点。

#### 场景:关键词过滤
- **当** searchable = true 且 searchQuery = "研发"
- **那么** filteredData 仅包含名称匹配的节点及其祖先节点

#### 场景:清空搜索
- **当** searchQuery 清空
- **那么** filteredData 返回完整树数据

#### 场景:搜索无结果
- **当** searchQuery 无匹配结果
- **那么** filteredData 为空数组

### 需求:节点查找能力

useTreeData 必须提供节点查找能力，支持按 ID 查找和获取祖先。

#### 场景:按 ID 查找节点
- **当** 开发者调用 findNode('dept-001')
- **那么** 返回 ID 为 'dept-001' 的节点对象

#### 场景:查找不存在的节点
- **当** 开发者调用 findNode('not-exist')
- **那么** 返回 undefined

#### 场景:获取祖先节点
- **当** 开发者调用 getAncestors('child-id')
- **那么** 返回从根节点到父节点的祖先节点数组

### 需求:选择操作方法

useTreeData 必须提供选择操作方法，支持编程式选择控制。

#### 场景:切换选中
- **当** 开发者调用 toggleSelect('node-id')
- **那么** 节点选中状态切换

#### 场景:清空选择
- **当** 开发者调用 clearSelection()
- **那么** selectedIds 清空

## 修改需求

(无)

## 移除需求

(无)
