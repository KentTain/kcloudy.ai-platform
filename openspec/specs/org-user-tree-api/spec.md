# org-user-tree-api 规范

## 目的
待定 - 由归档变更 migrate-people-select 创建。归档后请更新目的。
## 需求
### 需求:组织人员树 API 返回树形结构

组织人员树 API 必须返回包含组织和人员的树形结构。

#### 场景:获取根级组织人员树

- **当** 请求 `GET /iam/console/v1/org-users/tree`
- **那么** 系统返回根级组织列表，每个组织包含直属人员
- **当** 响应中每个组织节点
- **那么** 包含 `has_org_num`（直属子组织数量）和 `has_user_num`（直属人员数量）

#### 场景:懒加载子组织

- **当** 请求 `GET /iam/console/v1/org-users/tree?org_id={org_id}`
- **那么** 系统返回指定组织下的子组织和直属人员

#### 场景:搜索组织人员

- **当** 请求 `GET /iam/console/v1/org-users/tree?keyword={keyword}`
- **那么** 系统返回匹配的组织和人员
- **当** 搜索结果包含人员
- **那么** 人员显示在所属组织下

### 需求:组织下人员 API 支持递归查询

组织下人员 API 必须支持递归查询子组织人员。

#### 场景:查询组织直属人员

- **当** 请求 `GET /iam/console/v1/org-users/{org_id}/users?recursive=false`
- **那么** 系统返回该组织的直属人员列表

#### 场景:递归查询组织及子组织人员

- **当** 请求 `GET /iam/console/v1/org-users/{org_id}/users?recursive=true`
- **那么** 系统返回该组织及其所有子组织下的人员列表

### 需求:人员搜索 API 支持分页

人员搜索 API 必须支持分页查询。

#### 场景:搜索人员

- **当** 请求 `GET /iam/console/v1/users/search?keyword={keyword}&page=1&page_size=20`
- **那么** 系统返回匹配的人员列表
- **当** 响应包含分页信息
- **那么** 包含 `total`、`page`、`page_size`

#### 场景:搜索结果包含组织路径

- **当** 人员搜索返回结果
- **那么** 每个人员包含 `org_tree_names`（组织路径名称）

### 需求:批量获取用户 API 支持数组输入

批量获取用户 API 必须支持数组输入。

#### 场景:批量获取用户详情

- **当** 请求 `POST /iam/console/v1/users/batch` body: `["id1", "id2"]`
- **那么** 系统返回用户详情列表
- **当** 某个用户 ID 不存在
- **那么** 该位置返回 `null`

### 需求:用户头像 API 支持多种获取方式

用户头像 API 必须支持通过 ID 或用户名获取。

#### 场景:通过用户 ID 获取头像

- **当** 请求 `GET /iam/console/v1/users/{user_id}/avatar`
- **那么** 系统重定向到头像 URL 或返回图片

#### 场景:通过用户名获取头像

- **当** 请求 `GET /iam/console/v1/users/avatar?username={username}`
- **那么** 系统重定向到头像 URL 或返回图片

### 需求:组织搜索 API 支持分页

组织搜索 API 必须支持分页查询。

#### 场景:搜索组织

- **当** 请求 `GET /iam/console/v1/organizations/search?keyword={keyword}&page=1&page_size=20`
- **那么** 系统返回匹配的组织列表
- **当** 响应包含分页信息
- **那么** 包含 `total`、`page`、`page_size`

### 需求:批量获取组织 API 支持数组输入

批量获取组织 API 必须支持数组输入。

#### 场景:批量获取组织详情

- **当** 请求 `POST /iam/console/v1/organizations/batch` body: `["id1", "id2"]`
- **那么** 系统返回组织详情列表

### 需求:响应格式遵循项目统一规范

所有 API 响应必须遵循项目统一的 `ApiResponse` 格式。

#### 场景:成功响应

- **当** API 调用成功
- **那么** 响应格式为 `{ "code": 200, "msg": "success", "data": {...} }`

#### 场景:分页响应

- **当** API 返回分页数据
- **那么** 响应格式为 `{ "code": 200, "msg": "success", "data": [...], "total": 100, "page": 1, "page_size": 20 }`

### 需求:组织树节点类型遵循项目树模型

组织树节点必须遵循项目 `TreeNodeTreeVo` 类型。

#### 场景:组织树节点字段

- **当** 返回组织树节点
- **那么** 包含 `id`、`parent_id`、`name`、`tree_level`、`tree_leaf`、`tree_names`、`parent_ids`
- **当** 是嵌套树结构
- **那么** 包含 `children` 数组

