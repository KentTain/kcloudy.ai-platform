## 新增需求

### 需求:平台管理员可以扫描服务器目录注册插件定义

系统必须支持平台管理员通过扫描服务器目录批量注册插件定义。扫描过程必须解析插件包的 manifest 文件，提取元数据，计算校验和，并上传到 MinIO。

#### 场景:成功扫描并注册插件定义
- **当** 平台管理员请求 `POST /tenant/admin/v1/plugin-definitions/scan` 且 `directory` 参数指向包含有效插件包的目录
- **那么** 系统扫描目录中的所有 `.zip` 文件，解析 manifest，上传到 MinIO，注册到 `plugin_definitions` 表，返回扫描结果统计

#### 场景:扫描目录时遇到无效插件包
- **当** 平台管理员扫描目录且其中包含格式无效的插件包
- **那么** 系统跳过无效包，记录失败原因，返回包含失败详情的扫描结果

#### 场景:扫描时插件定义已存在
- **当** 扫描到的插件包的 `plugin_unique_identifier` 已存在于 `plugin_definitions` 表
- **那么** 系统跳过该插件，标记为 `skipped`，返回结果中说明"插件定义已存在"

### 需求:平台管理员可以上传插件包注册插件定义

系统必须支持平台管理员通过上传插件包文件注册插件定义。上传过程必须验证包格式，解析 manifest，上传到 MinIO。

#### 场景:成功上传并注册插件定义
- **当** 平台管理员请求 `POST /tenant/admin/v1/plugin-definitions/upload` 且上传有效的插件包文件
- **那么** 系统解析 manifest，上传到 MinIO，注册到 `plugin_definitions` 表，返回插件定义详情

#### 场景:上传的插件定义已存在
- **当** 平台管理员上传插件包且 `plugin_unique_identifier` 已存在
- **那么** 如果 `overwrite=false`，系统返回错误"插件定义已存在"；如果 `overwrite=true`，系统覆盖原有定义

### 需求:平台管理员可以查询插件定义列表

系统必须支持平台管理员分页查询插件定义列表，支持关键词搜索、类型筛选、推荐状态筛选、启用状态筛选。

#### 场景:成功查询插件定义列表
- **当** 平台管理员请求 `GET /tenant/admin/v1/plugin-definitions` 且提供分页参数
- **那么** 系统返回插件定义列表，包含每个定义的基本信息和统计信息（引用数）

#### 场景:按条件筛选插件定义列表
- **当** 平台管理员请求插件定义列表且提供 `keyword`、`type`、`is_recommended`、`is_enabled` 筛选参数
- **那么** 系统返回符合所有筛选条件的插件定义列表

### 需求:平台管理员可以查看插件定义详情

系统必须支持平台管理员查看单个插件定义的完整详情，包括完整的 manifest 内容。

#### 场景:成功查看插件定义详情
- **当** 平台管理员请求 `GET /tenant/admin/v1/plugin-definitions/{plugin_id}`
- **那么** 系统返回插件定义详情，包含 `declaration` 完整内容、引用数、创建时间、更新时间

#### 场景:插件定义不存在
- **当** 平台管理员查询不存在的 `plugin_id`
- **那么** 系统返回 404 错误

### 需求:平台管理员可以标记插件定义为推荐或禁用

系统必须支持平台管理员更新插件定义的 `is_recommended` 和 `is_enabled` 字段。

#### 场景:成功标记插件定义为推荐
- **当** 平台管理员请求 `PATCH /tenant/admin/v1/plugin-definitions/{plugin_id}` 且 `is_recommended=true`
- **那么** 系统更新插件定义的 `is_recommended` 字段，返回更新后的状态

#### 场景:成功禁用插件定义
- **当** 平台管理员请求 `PATCH /tenant/admin/v1/plugin-definitions/{plugin_id}` 且 `is_enabled=false`
- **那么** 系统更新插件定义的 `is_enabled` 字段，该插件定义将不会出现在租户的可用插件列表中

### 需求:平台管理员可以删除插件定义

系统必须支持平台管理员删除插件定义，但必须先检查是否有租户在使用（`refers > 0`）。

#### 场景:成功删除插件定义
- **当** 平台管理员请求 `DELETE /tenant/admin/v1/plugin-definitions/{plugin_id}` 且该定义的 `refers=0`
- **那么** 系统删除插件定义记录，同时删除 MinIO 上的插件包文件

#### 场景:删除插件定义时仍有租户在使用
- **当** 平台管理员请求删除插件定义且该定义的 `refers > 0`
- **那么** 系统返回错误"无法删除，有 N 个租户正在使用此插件"

### 需求:插件定义必须包含推荐和启用状态字段

系统必须确保 `tenant.plugin_definitions` 表包含 `is_recommended` 和 `is_enabled` 字段，默认值分别为 `false` 和 `true`。

#### 场景:新建插件定义时设置默认值
- **当** 系统创建新的插件定义记录
- **那么** `is_recommended` 默认为 `false`，`is_enabled` 默认为 `true`

### 需求:插件定义注册必须统一上传到 MinIO

系统必须将所有插件包上传到 MinIO 存储，存储路径为 `plugins/{plugin_id}/{version}.zip`。

#### 场景:插件包成功上传到 MinIO
- **当** 系统解析插件包并准备存储
- **那么** 系统上传插件包到 MinIO 的 `plugins` bucket，object key 为 `{plugin_id}/{version}.zip`

#### 场景:MinIO 上传失败
- **当** 系统上传插件包到 MinIO 失败
- **那么** 系统回滚注册操作，返回错误"插件包存储失败"

### 需求:插件定义管理必须有权限控制

系统必须对插件定义管理 API 进行权限校验，要求 `tenant:plugin:read` 或 `tenant:plugin:write` 权限。

#### 场景:无权限访问插件定义管理 API
- **当** 用户请求插件定义管理 API 且没有 `tenant:plugin:read` 或 `tenant:plugin:write` 权限
- **那么** 系统返回 403 错误"权限不足"
