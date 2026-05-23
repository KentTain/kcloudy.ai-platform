## MODIFIED Requirements

### Requirement: 权限选择

系统 SHALL 支持多选权限功能，PermissionTree SHALL 使用 CheckboxTree 替代 el-tree。

#### Scenario: 勾选权限
- **WHEN** 用户勾选某个权限
- **THEN** 该权限被添加到已选权限列表，CheckboxTree SHALL 通过 v-model 同步已选列表

#### Scenario: 勾选资源节点
- **WHEN** 用户勾选某个资源节点
- **THEN** 该资源下的所有权限被选中，CheckboxTree SHALL 支持半选状态

#### Scenario: 取消勾选
- **WHEN** 用户取消勾选某个权限或资源节点
- **THEN** 对应权限从已选列表移除

### Requirement: 权限搜索

系统 SHALL 支持搜索过滤权限，搜索框 SHALL 使用 shadcn Input 替代 el-input。

#### Scenario: 按名称搜索
- **WHEN** 用户在搜索框输入权限名称关键字
- **THEN** CheckboxTree SHALL 过滤并展示匹配的权限及其父节点

#### Scenario: 无匹配结果
- **WHEN** 搜索关键字无匹配结果
- **THEN** CheckboxTree SHALL 展示空状态提示