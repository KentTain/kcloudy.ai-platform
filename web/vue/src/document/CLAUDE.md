# Document 模块开发指南

本文件为 Claude Code 在 `web/vue/src/document/` 文档库管理模块中工作时提供指导。

## 模块定位

Document 模块提供企业知识库的文档管理功能，包括文件夹树、文件上传/下载、元数据管理、切片索引、回收站和资源权限。与后端 `server/python/src/document/` 模块对齐。

## 目录职责

| 目录 | 职责 |
|------|------|
| api/ | API 函数（文件夹、文件、回收站、资源权限） |
| composables/ | 组合式函数（useFileTree、useFileUpload 等） |
| pages/ | 页面组件（文件管理、回收站） |
| router/ | 模块路由配置 |
| stores/ | Pinia 状态管理（文件夹、文件状态） |
| types/ | TypeScript 类型定义 |

## 页面组件

| 页面 | 路径 | 功能 |
|------|------|------|
| FolderList | /document/folders | 文件夹树形管理 |
| FileList | /document/files | 文件列表管理 |
| FileDetail | /document/files/:id | 文件详情查看 |
| TrashList | /document/trash | 回收站管理 |

## 路由配置

| 路径 | 组件 | 权限 |
|------|------|------|
| /document/folders | FolderList | requiresAuth |
| /document/files | FileList | requiresAuth |
| /document/files/:id | FileDetail | requiresAuth |
| /document/trash | TrashList | requiresAuth |

## API 函数

### 文件夹管理 API

| 函数 | 说明 |
|------|------|
| getFolders | 获取文件夹列表 |
| getFolder | 获取文件夹详情 |
| createFolder | 创建文件夹 |
| updateFolder | 更新文件夹 |
| deleteFolder | 删除文件夹 |

### 文件管理 API

| 函数 | 说明 |
|------|------|
| getFiles | 获取文件列表 |
| getFile | 获取文件详情 |
| uploadFile | 上传文件 |
| downloadFile | 下载文件 |
| deleteFile | 删除文件 |

### 回收站 API

| 函数 | 说明 |
|------|------|
| getTrashItems | 获取回收站列表 |
| restoreItem | 恢复文件/文件夹 |
| permanentDelete | 永久删除 |

## 核心类型

| 类型 | 说明 |
|------|------|
| Folder | 文件夹信息（支持树形结构） |
| File | 文件信息 |
| FileMetadata | 文件元数据 |
| TrashItem | 回收站条目 |
| ResourcePermission | 资源权限信息 |

## 开发规则

- 使用 `<script setup lang="ts">` 语法
- API 函数使用 `@/framework/api/client` 封装
- Store 使用 Pinia 的 `defineStore`
- 页面使用 `AppPage` 组件作为骨架
- 所有路由需要认证（requiresAuth: true）
- 文件夹树组件复用 `@/components` 的 Tree 组件

## 测试

```bash
pnpm test:unit tests/document/unit/ --run
```
