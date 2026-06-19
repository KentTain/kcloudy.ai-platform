# 插件系统测试补充设计

## 概述

为 `migrate-plugin-system` 变更补充测试，覆盖 ai_plugin SDK、服务层和控制器层。

## 测试范围

| 层级 | 测试类型 | 文件位置 |
|------|----------|----------|
| SDK | 单元测试 | `tests/ai/unit/sdk/` |
| Service | 单元测试 | `tests/ai/unit/services/` |
| Controller | 集成测试 | `tests/ai/integration/controllers/` |

## 目录结构

```
tests/ai/
├── __init__.py
├── conftest.py              # AI 模块公共 fixtures
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
    ├── conftest.py          # 集成测试 fixtures（数据库、认证）
    └── controllers/
        ├── __init__.py
        ├── test_admin_plugin.py
        └── test_console_plugin.py
```

## SDK 单元测试

### entities/ 测试重点

- **I18nObject**：多语言回退逻辑（zh_Hans/pt_BR 默认使用 en_US）
- **ToolParameter**：参数类型枚举、校验规则、to_docstring_param 转换
- **ToolInvokeMessage**：消息类型枚举、序列化/反序列化（BlobMessage 的 base64 编解码）

### errors/ 测试重点

- 异常继承关系正确
- description 默认值与自定义值
- 字符串表示（`__str__`）行为

### file/ 测试重点

- 文件类型常量定义
- 文件实体模型字段校验
- 文件处理的边界情况

## 服务层单元测试

### CredentialService 测试重点

| 方法 | 测试场景 |
|------|----------|
| `encrypt_credentials` | 敏感字段加密，非敏感字段保留原值 |
| `decrypt_credentials` | 敏感字段解密，解密失败降级处理 |
| `mask_credentials` | 不同长度的脱敏规则（短/中/长字符串） |
| `validate_credentials_format` | 必填校验、类型校验、选项值校验 |
| `extract_credentials_schema` | 从插件配置提取凭证架构 |

### PluginManagementService 测试重点

| 方法 | 测试场景 |
|------|----------|
| `get_plugin_list` | 分页、状态过滤、类型过滤 |
| `get_plugin_info` | 正常获取、插件不存在异常 |
| `list_credentials` / `get_credential` | 凭证 CRUD |
| `create_credential` | 名称重复校验、格式校验、加密入库 |
| `update_credential` | 脱敏占位回填逻辑 |
| `delete_credential` | 正常删除、凭证不存在 |

## 控制器集成测试

使用 `httpx.AsyncClient` + `TestClient` + 真实 PostgreSQL 数据库。

### Admin 控制器测试

| 接口 | 测试场景 |
|------|----------|
| `GET /admin/v1/plugins` | 空列表、带过滤条件、分页 |
| `POST /admin/v1/plugins/upload` | 有效 zip 包、无效格式 |
| `POST /admin/v1/plugins/{id}/start` | 启动成功、插件不存在 |
| `POST /admin/v1/plugins/{id}/stop` | 停止成功、插件不存在 |
| `DELETE /admin/v1/plugins/{id}` | 卸载成功、插件不存在 |
| `GET /admin/v1/plugins/{id}` | 获取详情、插件不存在 |

### Console 控制器测试

| 接口 | 测试场景 |
|------|----------|
| `GET /console/v1/plugins` | 列表查询 |
| `GET /console/v1/plugins/{id}` | 详情查询 |
| `GET /console/v1/plugins/{id}/credentials` | 凭证列表（分页） |
| `POST /console/v1/plugins/{id}/credentials` | 创建凭证、名称重复 |
| `PUT /console/v1/plugins/{id}/credentials/{cid}` | 更新凭证 |
| `DELETE /console/v1/plugins/{id}/credentials/{cid}` | 删除凭证 |

## Fixtures 设计

### 公共 fixtures（tests/ai/conftest.py）

- `credential_schema`：标准凭证架构
- `sample_plugin_config`：示例插件配置

### 集成测试 fixtures（tests/ai/integration/conftest.py）

- `client`：HTTP 测试客户端
- `auth_headers`：认证请求头
- `db_session`：数据库会话（事务回滚清理）
- `test_plugin`：测试插件记录
- `test_credential`：测试凭证记录

## 实现任务

| 序号 | 任务 | 依赖 |
|------|------|------|
| 1 | 创建 `tests/ai/` 目录结构与 conftest.py | 无 |
| 2 | SDK entities 单元测试 | 1 |
| 3 | SDK errors 单元测试 | 1 |
| 4 | SDK file 单元测试 | 1 |
| 5 | CredentialService 单元测试 | 1 |
| 6 | PluginManagementService 单元测试 | 1 |
| 7 | Admin 控制器集成测试 | 1, 5, 6 |
| 8 | Console 控制器集成测试 | 1, 5, 6 |
| 9 | 更新 pytest.ini 配置 | 无 |

## 验收标准

- [ ] 所有测试用例通过 `uv run pytest tests/ai/ -v`
- [ ] SDK 测试覆盖核心实体、异常、文件模块
- [ ] Service 测试覆盖凭证加密/解密/脱敏/校验、插件管理核心逻辑
- [ ] Controller 测试覆盖管理端和用户端主要接口
- [ ] 集成测试使用真实数据库，测试后数据自动清理
