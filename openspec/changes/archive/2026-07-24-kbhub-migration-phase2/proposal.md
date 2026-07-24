## 为什么

kbhub 迁移方案 Phase 2：完整迁移文档库、标签管理、人设管理功能到 document 模块。document 模块当前仅有骨架（空 controllers/models/schemas/services），需要实现完整的文档库能力，包括文件管理、成员管理、资源权限体系、标签、人设、文档切片索引、回收站和审计。ai 模块（Phase 3）依赖 document 的 inner 接口回查源文件权限，因此 document 须先行。

## 变更内容

- document 模块新建 module.py（菜单 + 功能权限 PermissionDef 声明）
- document 模块完整后端：16 个数据库模型、服务层、控制器（admin/console/inner）、迁移、任务、监听器
- document 模块文档库权限判定引擎（精简版，复用 framework 权限引擎）
- document 模块 inner 接口（供 ai 模块回查源文件权限和成员身份）
- document 模块前端：API 层、类型、stores、页面（文档库列表/详情、标签管理、人设管理）、专用组件
- 审计接入：业务操作通过 framework 审计写入辅助记录到 iam.audit_logs
- document schema 数据库迁移 + 种子数据

## 功能 (Capabilities)

### 新增功能

- `document-library`: 文档库管理（个人/团队文档库 CRUD、成员管理、权限配置、回收站、元数据）
- `document-folder`: 文件夹树管理（TreeNodeMixin 树形结构、目录树交互）
- `document-file`: 文件管理（上传、预览、下载、版本管理、切片索引任务触发）
- `document-resource-permission`: 文档库资源权限体系（权限组、资源 ACL、继承链、权限判定引擎）
- `document-tag`: 标签管理（标签 CRUD、标签分组、人设引用）
- `document-persona`: 人设管理（AI 提示词 CRUD、标签引用校验）
- `document-audit`: 文档库审计日志（通过 framework 审计写入辅助）
- `document-inner-api`: document 内部接口（供 ai 模块回查源文件权限和成员身份）

### 修改功能

（无现有功能规范级行为变更，document 模块从空骨架开始）

## 影响

- **后端**：document 模块从空骨架变为完整模块，新增约 16 个模型、10+ 个服务、9+ 个控制器、1 个 module.py
- **数据库**：document schema 新增 16 张表（libraries、library_members、folders、documents、document_versions、resource_acls、library_roles、library_role_members、resource_metadata、library_metadata_fields、resource_favorites、resource_recent_accesses、tags、tag_groups、personas、config_items）
- **API**：新增 `/document/admin/v1/*`、`/document/console/v1/*`、`/document/inner/v1/*` 系列端点
- **前端**：document 模块新增 3+ 页面、7+ 专用组件、路由、stores、API 层
- **依赖**：document 依赖 framework（权限引擎、审计写入）和 iam（通过 inner 接口获取用户/组织信息）
- **兼容性**：无破坏性变更，所有新增为增量
