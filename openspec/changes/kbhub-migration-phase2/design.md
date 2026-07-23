## 上下文

document 模块当前仅有空骨架（controllers/models/schemas/services 目录均为空 __init__.py）。kbhub 迁移方案 Phase 2 需完整迁移文档库、标签管理、人设管理功能。Phase 1 已提供 framework 权限引擎、审计写入辅助、iam 站内信等基础设施。document 模块是 Phase 3（ai）的前置依赖——ai 模块知识库文档来源于 document 文件，需通过 inner 接口回查源文件权限。

kbhub 源代码量大（library.py 2.6 万行、permission.py 7.8 万行、enums.py 3.2 万行），含大量 Alon 平台特有逻辑，需精简迁移。

## 目标 / 非目标

**目标：**
- document 模块完整实现文档库（个人/团队）、文件夹树、文件管理、成员管理、资源权限体系
- 实现标签管理、人设管理
- 实现文档库权限判定引擎（精简版，复用 framework 权限引擎 + Policy 求值器）
- 提供 inner 接口供 ai 模块回查源文件权限和成员身份
- 实现文档切片与索引任务触发（复用 ai Embedding 能力）
- 审计通过 framework 审计写入辅助记录
- 前端使用本项目组件重新实现，缺件迁移适配

**非目标：**
- 不实现知识库功能（Phase 3 范围）
- 不实现入库审核流程（Phase 3 范围）
- 不实现企业 Policy 模型（Phase 1 已在 iam 实现，document 调用求值器）
- 不迁移 kbhub 的 Alon 平台特有逻辑（BaseExtension、alon.events 等）
- 不实现权限申请审批（Phase 1 已在 iam 实现，document 提供 apply 回调 inner 接口）

## 决策

### 决策 1：权限判定引擎精简实现，复用 framework

**选择**：document `permission_service.py` 实现文档库权限判定流程（owner/admin 全可编辑 → 全员权限+权限组+直授权取最高 → 继承链 → Policy 叠加），调用 framework 权限引擎编排第 2 层资源权限和第 3 层 Policy。

**理由**：kbhub permission.py 7.8 万行含 Alon 平台特有逻辑，只需核心判定流程。

**替代方案**：完整迁移 permission.py → 冗余、维护困难，否决。

### 决策 2：Folder 使用 TreeNodeMixin，parent_id 不加外键

**选择**：Folder 继承 framework `TreeNodeMixin`，树字段由 Mixin 自动维护，parent_id 不加 ForeignKey 约束（遵循项目规范）。

**理由**：项目 CLAUDE.md 明确规定 TreeNodeMixin 的 parent_id 禁止外键，顶级节点 parent_id 为虚拟值 "root"。

### 决策 3：资源权限继承链沿 文档库根→目录→文件 计算

**选择**：ResourceAcl 按 resource_type（library_root/folder/document）+ resource_id 存储，继承链沿树形结构向上查找，可关闭继承（acl_inherit_enabled）。

**理由**：kbhub 设计成熟，迁移方案 §3.1 已确认。

### 决策 4：inner 接口设计

**选择**：提供两个核心 inner 接口：
- `GET /document/inner/v1/documents/{id}/permission?user_id=` 校验用户对源文件资源权限（返回 none/readonly/editable）
- `GET /document/inner/v1/libraries/{id}/members?user_id=` 校验文档库成员身份

**理由**：ai 模块知识库问答需回查源文件权限，不放大权限。inner 接口无认证，仅供模块间调用。

### 决策 5：人设放 document 模块

**选择**：Persona 表 `document.personas`，被人设管理页面和标签管理引用。

**理由**：人设被标签管理引用，标签属 document，归属一致（迁移方案 §2.2 已确认）。

### 决策 6：文档切片索引复用 ai Embedding，document 只触发任务

**选择**：document 只负责触发切片索引任务、记录任务状态，实际 Embedding/GraphRAG 调用 ai 模块能力（通过 inner 接口或事件）。

**理由**：避免 document 重复实现 AI 能力，复用 ai 现有 Embedding/Rerank 服务。

## 风险 / 权衡

- **[权限判定复杂度]** 继承链 + 权限组 + Policy 叠加判定逻辑复杂 → 充分单元测试覆盖各判定路径；权限排障面板输出命中原因
- **[文件存储]** 文件上传/预览/下载需对接 MinIO → 复用 framework storage 组件
- **[切片索引跨模块]** document 触发任务需调用 ai 能力 → 通过事件或 inner 接口，document 不直接依赖 ai（依赖方向 ai→document）
- **[前端组件迁移]** kbhub 文档库布局/文件详情/目录树等组件需适配本项目 UI → 使用本项目 Shadcn/Radix/Tailwind 组件重写，仅迁移业务逻辑
- **[代码量]** 16 表 + 10 服务 + 9 控制器 → 按依赖顺序分批实现，先模型后服务后控制器

## 迁移计划

1. module.py 声明（菜单 + 权限）
2. 基础模型（Library/LibraryMember/Folder/Document/DocumentVersion）
3. 权限模型（LibraryRole/LibraryRoleMember/ResourceAcl）
4. 标签与人设模型（Tag/TagGroup/Persona）
5. 元数据模型（ResourceMetadata/LibraryMetadataField）
6. 权限判定引擎
7. 业务服务（按依赖顺序）
8. 控制器（admin/console/inner）
9. 文档切片索引任务
10. 数据库迁移 + 种子
11. 审计接入
12. 前端 API/类型/stores
13. 前端页面（文档库列表/详情、标签、人设）
14. 前端专用组件迁移适配
15. 前端路由 + 权限码
16. 单元测试 + E2E

**回滚**：全部为增量（新 schema + 新模块），回滚删除 document schema 和模块代码即可。

## 待解决问题

- 向量字段维度确认（kbhub 默认 vector(1024)，需与 ai 模块 Embedding 模型维度一致）→ 在实现切片索引时与 ai 模块对齐
- 文件预览支持的格式范围（PDF/Office/图片/音视频）→ 初版支持 PDF/图片/文本，Office 和音视频作为后续增强
