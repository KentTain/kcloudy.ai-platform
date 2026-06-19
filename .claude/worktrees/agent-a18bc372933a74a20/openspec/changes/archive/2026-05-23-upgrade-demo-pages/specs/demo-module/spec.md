## MODIFIED Requirements

### Requirement: Demo 模块样式迁移

Demo 模块组件 SHALL 使用 shadcn 组件替代 CommonXxx 封装组件。

#### Scenario: Button 组件迁移

- **WHEN** Demo 模块使用 Button 组件
- **THEN** 系统 SHALL 使用 shadcn Button 替代 CommonButton

#### Scenario: Card 组件迁移

- **WHEN** Demo 模块使用 Card 组件
- **THEN** 系统 SHALL 使用 shadcn Card 替代 CommonCard

#### Scenario: Loading 组件迁移

- **WHEN** Demo 模块需要加载态展示
- **THEN** 系统 SHALL 使用 Skeleton 组件替代 CommonLoading

#### Scenario: 表格组件迁移

- **WHEN** Demo 模块需要列表展示
- **THEN** 系统 SHALL 使用 shadcn Table 组件替代 CommonCard 内的手写列表