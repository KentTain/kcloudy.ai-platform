## 1. 模块声明与基础模型

- [x] 1.1 新建 `document/module.py`（ModuleDefinition：菜单 + 功能权限 PermissionDef）
- [x] 1.2 新建 `document/models/library.py`（Library/LibraryMember 模型）
- [x] 1.3 新建 `document/models/folder.py`（Folder 模型，TreeNodeMixin，parent_id无外键）
- [x] 1.4 新建 `document/models/document.py`（Document/DocumentVersion 模型）
- [x] 1.5 新建 `document/models/enums.py`（文档库相关枚举，从kbhub enums.py拆分）
- [x] 1.6 验证模型可映射，迁移可执行

## 2. 权限模型

- [x] 2.1 新建 `document/models/permission.py`（LibraryRole/LibraryRoleMember/ResourceAcl 模型）
- [x] 2.2 验证权限模型字段（角色/权限组/资源ACL/继承链字段）
- [x] 2.3 验证模型可映射

## 3. 标签与人设模型

- [x] 3.1 新建 `document/models/tag.py`（Tag/TagGroup 模型）
- [x] 3.2 新建 `document/models/persona.py`（Persona 模型）
- [x] 3.3 验证模型可映射

## 4. 元数据模型

- [x] 4.1 新建 `document/models/metadata.py`（ResourceMetadata/LibraryMetadataField 模型）
- [x] 4.2 验证模型可映射

## 5. 权限判定引擎

- [x] 5.1 新建 `document/services/permission_service.py`（文档库权限判定引擎，复用framework权限引擎）
- [x] 5.2 实现判定流程（owner/admin全可编辑→全员权限+权限组+直授权取最高→继承链→Policy叠加）
- [x] 5.3 实现权限排障输出（命中原因）
- [x] 5.4 单元测试覆盖各判定路径（owner/admin/全员/权限组/继承/截断/Policy）

## 6. 业务服务

- [x] 6.1 新建 `document/services/library_service.py`（文档库 CRUD）
- [x] 6.2 新建 `document/services/folder_service.py`（文件夹树管理）
- [x] 6.3 新建 `document/services/document_service.py`（文件上传/预览/下载/切片触发）
- [x] 6.4 新建 `document/services/member_service.py`（成员管理）
- [x] 6.5 新建 `document/services/permission_config_service.py`（权限配置：权限组+资源权限）
- [x] 6.6 新建 `document/services/tag_service.py`（标签管理）
- [x] 6.7 新建 `document/services/persona_service.py`（人设管理）
- [x] 6.8 新建 `document/services/recycle_service.py`（回收站）
- [x] 6.9 新建 `document/services/metadata_service.py`（元数据管理）
- [x] 6.10 各服务单元测试

## 7. 控制器

- [x] 7.1 新建 `document/controllers/admin/`（管理端：文档库/标签/人设管理）
- [x] 7.2 新建 `document/controllers/console/`（用户端：文档库/文件/成员/权限/回收站）
- [x] 7.3 新建 `document/controllers/inner/`（内部接口：源文件权限回查、成员身份回查、权限申请apply回调）
- [x] 7.4 新建 schemas（请求/响应 DTO，继承 framework.schemas.BaseModel）
- [ ] 7.5 控制器接口测试

## 8. 任务与监听

- [x] 8.1 新建 `document/tasks/document_index_task.py`（文档切片索引任务触发，复用ai能力）
- [x] 8.2 新建 `document/listeners/`（事件监听，如权限变更失效）
- [x] 8.3 任务可调度验证

## 9. 数据库迁移与种子

- [x] 9.1 新建 document 迁移脚本（16张表）
- [x] 9.2 新建 document 种子数据（默认元数据字段、权限组模板）
- [ ] 9.3 执行迁移并验证表结构

## 10. 审计接入

- [x] 10.1 各业务操作接入framework审计写入辅助（library/folder/document/member/permission/tag/persona操作）
- [x] 10.2 验证审计日志正确写入 iam.audit_logs，business_domain=document

## 11. 前端基础

- [x] 11.1 新建 `web/vue/src/document/api/`（API 函数，路径 `/document/console/v1/*`、`/document/admin/v1/*`）
- [x] 11.2 新建 `web/vue/src/document/types/`（类型定义）
- [x] 11.3 新建 `web/vue/src/document/stores/`（Pinia 状态）
- [x] 11.4 新建 `web/vue/src/document/composables/`（组合式函数）
- [x] 11.5 类型校验通过

## 12. 前端页面

- [x] 12.1 新建文档库列表页（`/document/library`）
- [x] 12.2 新建文档库详情页（概览/文件/成员/权限/回收站/审计/任务）
- [x] 12.3 新建标签管理页（`/document/tags`）
- [x] 12.4 新建人设管理页（`/document/personas`，CodeMirror提示词编辑）
- [x] 12.5 页面联调接口通过

## 13. 前端专用组件

- [x] 13.1 迁移适配文档库布局组件（侧栏+内容区）
- [x] 13.2 迁移适配文件详情组件（预览/元数据/版本）
- [x] 13.3 迁移适配目录树组件（文件浏览器）
- [x] 13.4 迁移适配成员管理组件（人员选择器，适配iam接口）
- [x] 13.5 迁移适配权限配置组件（权限组+资源权限树）
- [x] 13.6 迁移适配标签选择器组件
- [x] 13.7 迁移适配人设编辑器组件
- [x] 13.8 迁移适配审计日志展示组件
- [x] 13.9 组件复用本项目 UI 规范（Shadcn/Radix/Tailwind）

## 14. 前端路由与权限

- [x] 14.1 新建 `web/vue/src/document/router/`（路由配置）
- [x] 14.2 接入权限码（菜单按 document:* 权限渲染）
- [ ] 14.3 前端单元测试 + E2E 基础流程
