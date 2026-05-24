## REMOVED Requirements

### Requirement: Element Plus 依赖

**Reason**: 项目已全面迁移至 shadcn-vue 组件体系，Element Plus 依赖不再需要。

**Migration**: 无需迁移。所有 Element Plus 组件已在 Change #5（migrate-iam-to-shadcn）中迁移至 shadcn-vue 组件。

#### Scenario: 移除 element-plus 依赖后编译通过

- **WHEN** 从 package.json 移除 element-plus 依赖
- **THEN** 系统 SHALL 能够成功编译无错误

#### Scenario: 移除 element-plus 依赖后测试通过

- **WHEN** 执行单元测试
- **THEN** 系统 SHALL 所有测试通过

#### Scenario: 移除后无残留引用

- **WHEN** 全局搜索 element-plus 相关引用
- **THEN** 系统 SHALL 返回零匹配
