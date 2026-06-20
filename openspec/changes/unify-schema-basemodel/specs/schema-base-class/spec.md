# Schema 基类规范

## 新增需求

### 需求: 所有 Schema 必须使用 framework 提供的基类

所有业务模块（iam、tenant、ai、demo）的 Pydantic Schema 类必须继承 `framework.schemas.BaseModel` 或其子类，禁止直接继承 `pydantic.BaseModel`。

#### 场景: 创建响应 Schema

- **当** 开发者创建响应 Schema 类（如 `UserResponse`）
- **那么** 该类必须继承 `framework.schemas.BaseModel`
- **且** 无需手动配置 `model_config = ConfigDict(from_attributes=True)`

#### 场景: 创建请求 Schema

- **当** 开发者创建请求 Schema 类（如 `UserCreate`）
- **那么** 该类必须继承 `framework.schemas.BaseModel`

#### 场景: 创建查询参数 Schema

- **当** 开发者创建查询参数 Schema
- **那么** 必须使用以下基类之一：
  - `framework.schemas.BaseQuery`（非分页查询）
  - `framework.schemas.BasePaginatedQuery`（分页查询）

#### 场景: 创建树形响应 Schema

- **当** 开发者创建树形结构响应 Schema
- **那么** 必须使用 `framework.schemas.TreeNodeVo` 或 `framework.schemas.TreeNodeTreeVo`

### 需求: 禁止冗余配置

禁止在 Schema 类中手动配置 `framework.schemas.BaseModel` 已包含的默认配置。

#### 场景: 检测冗余的 from_attributes 配置

- **当** Schema 类继承 `framework.schemas.BaseModel`
- **且** 该类包含 `model_config = ConfigDict(from_attributes=True)`
- **那么** 必须删除该冗余配置

#### 场景: 保留额外的 ConfigDict 配置

- **当** Schema 类需要额外的配置（如 `extra="forbid"`）
- **那么** 可以保留 `model_config`，但必须只包含额外的配置项
- **且** 不得重复配置 `from_attributes=True`

### 需求: 豁免场景明确

以下场景豁免使用 `framework.schemas.BaseModel`：

1. `ai_plugin/sdk/*` 目录下的所有文件
2. 第三方库集成接口（需在代码注释中说明原因）

#### 场景: ai_plugin SDK 开发

- **当** 开发者在 `ai_plugin/sdk/` 目录下创建 Schema
- **那么** 可以使用 `pydantic.BaseModel`
- **且** 无需遵循本规范

### 需求: 导入语句规范

Schema 文件的导入语句必须从 `framework.schemas` 导入基类。

#### 场景: 正确的导入方式

- **当** 开发者在 Schema 文件中导入基类
- **那么** 必须使用以下方式之一：
  - `from framework.schemas import BaseModel`
  - `from framework.schemas import BaseModel, BaseQuery, BasePaginatedQuery`
  - `from framework.schemas.base import BaseModel`

#### 场景: 禁止的导入方式

- **当** 开发者在业务模块 Schema 文件中编写 `from pydantic import BaseModel`
- **那么** 必须修改为 `from framework.schemas import BaseModel`

### 需求: 基类选择指南

开发者必须根据场景选择正确的基类。

#### 场景: 普通 Schema 选择

- **当** 创建普通的请求或响应 Schema
- **那么** 必须使用 `framework.schemas.BaseModel`

#### 场景: 查询参数选择

- **当** 创建非分页查询参数
- **那么** 必须继承 `framework.schemas.BaseQuery`

#### 场景: 分页查询参数选择

- **当** 创建分页查询参数
- **那么** 必须继承 `framework.schemas.BasePaginatedQuery`

#### 场景: 树形响应选择

- **当** 创建树形结构响应（如部门树、菜单树）
- **那么** 必须继承 `framework.schemas.TreeNodeVo` 或 `framework.schemas.TreeNodeTreeVo`

### 需求: CI 检查强制执行

项目必须包含 CI 检查脚本，自动检测违规代码。

#### 场景: 新代码提交时检查

- **当** 开发者提交包含 Schema 文件的代码
- **那么** CI 必须检查该文件是否使用正确的基类
- **且** 如果发现违规，必须阻止提交并显示错误信息

#### 场景: 检查豁免目录

- **当** 检查脚本扫描 `ai_plugin/sdk/` 目录
- **那么** 必须跳过该目录，不进行检查

## 修改需求

无。此变更不修改现有需求，仅新增规范。

## 移除需求

无。此变更不移除任何需求。
