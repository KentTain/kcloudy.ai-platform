# 插件系统测试补充实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（- [x]）语法来跟踪进度。

**目标：** 为 migrate-plugin-system 变更补充测试，覆盖 ai_plugin SDK、服务层和控制器层

**架构：** 采用分层测试策略：SDK 和 Service 层使用单元测试（mock 隔离依赖），Controller 层使用集成测试（真实数据库 + HTTP 客户端）。测试目录镜像源码结构。

**技术栈：** pytest + pytest-asyncio + httpx.AsyncClient + unittest.mock

---

## 文件结构

### 测试目录结构

`
server/python/tests/ai/
├── __init__.py
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── sdk/
│   │   ├── __init__.py
│   │   ├── test_entities.py
│   │   ├── test_errors.py
│   │   └── test_file.py
│   └── services/
│       ├── __init__.py
│       ├── test_credential_service.py
│       └── test_plugin_management_service.py
└── integration/
    ├── __init__.py
    ├── conftest.py
    └── controllers/
        ├── __init__.py
        ├── test_admin_plugin.py
        └── test_console_plugin.py
`

---

## 任务 1：创建测试目录结构与公共 fixtures

- [x] **步骤 1：创建目录结构**
- [x] **步骤 2：创建公共 fixtures（tests/ai/conftest.py）**
- [x] **步骤 3：验证目录结构**
- [x] **步骤 4：Commit**

---

## 任务 2：SDK entities 单元测试

- [x] **步骤 1：编写 I18nObject 测试**
- [x] **步骤 2：运行 I18nObject 测试**
- [x] **步骤 3：编写 ToolInvokeMessage 测试**
- [x] **步骤 4：运行完整 entities 测试**
- [x] **步骤 5：Commit**

---

## 任务 3：SDK errors 单元测试

- [x] **步骤 1：编写 errors 测试**
- [x] **步骤 2：运行 errors 测试**
- [x] **步骤 3：Commit**

---

## 任务 4：SDK file 单元测试

- [x] **步骤 1：编写 file 测试**
- [x] **步骤 2：运行 file 测试**
- [x] **步骤 3：Commit**

---

## 任务 5：CredentialService 单元测试

- [x] **步骤 1：编写 encrypt_credentials 测试**
- [x] **步骤 2：编写 decrypt_credentials 测试**
- [x] **步骤 3：编写 mask_credentials 测试**
- [x] **步骤 4：编写 validate_credentials_format 测试**
- [x] **步骤 5：编写 extract_credentials_schema 测试**
- [x] **步骤 6：运行完整 CredentialService 测试**
- [x] **步骤 7：Commit**

---

## 任务 6：PluginManagementService 单元测试

- [x] **步骤 1：编写 get_plugin_list 测试**
- [x] **步骤 2：编写 get_plugin_info 测试**
- [x] **步骤 3：编写凭证管理测试**
- [x] **步骤 4：运行 PluginManagementService 测试**
- [x] **步骤 5：Commit**

---

## 任务 7：更新 pytest.ini 配置

- [x] **步骤 1：添加 ai 模块到 pythonpath**
- [x] **步骤 2：验证 pytest 配置生效**
- [x] **步骤 3：Commit**

---

## 任务 8：运行所有单元测试并验证

- [x] **步骤 1：运行所有 SDK 单元测试**
- [x] **步骤 2：运行所有服务层单元测试**
- [x] **步骤 3：运行完整 ai 模块测试套件**
- [x] **步骤 4：Commit 最终验证**

---

## 验收标准

- [x] 所有测试用例通过
- [x] SDK 测试覆盖核心实体、异常、文件模块
- [x] Service 测试覆盖凭证加密/解密/脱敏/校验
- [x] 测试使用 mock 隔离外部依赖
- [x] pytest.ini 正确配置模块路径
