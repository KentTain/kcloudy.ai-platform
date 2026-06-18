## 1. 基础设施准备

- [x] 1.1 创建 `framework/configs/encryption.py`，迁移 EncryptionSettings 配置模型
- [x] 1.2 在 `framework/common/exceptions.py` 中添加 BadRequestError 异常类
- [x] 1.3 更新 `server/python/pyproject.toml`，添加依赖：pycryptodome、datashaper、tiktoken、aiolimiter、json-repair
- [x] 1.4 在 `docker/docker-compose.backend.yml` 中添加 sandbox 服务定义

## 2. encryption 组件迁移

- [x] 2.1 迁移 encryption 组件代码（10 个文件）至 `server/python/src/ai/components/encryption/`
- [x] 2.2 重写导入路径：`alon.configs.infrastructure.encryption` → `framework.configs.encryption`
- [x] 2.3 重写导入路径：`alon.configs.settings` → 适配本项目配置注入方式
- [x] 2.4 创建测试目录（已完成于 `tests/ai/unit/components/encryption/`）
- [x] 2.5 编写 `test_encryption.py`：测试 AES 加密/解密功能（已通过）
- [x] 2.6 测试 RSA 加密/解密功能（已在 test_encryption.py 中覆盖）
- [x] 2.7 测试加密管理器初始化和实例获取（已在 test_encryption.py 中覆盖）

## 3. datasource 组件迁移

- [x] 3.1 迁移 datasource 组件代码（8 个文件）至 `server/python/src/ai/components/datasource/`
- [x] 3.2 重写导入路径：`alon.common.exceptions.BadRequestError` → `framework.common.exceptions.BadRequestError`
- [x] 3.3 创建测试目录（已完成于 `tests/ai/unit/components/datasource/`）
- [x] 3.4 编写 `test_datasource.py`、`test_interfaces.py`：测试连接器基类接口（已通过）
- [x] 3.5 编写 `test_uri.py`、`test_sql_parsing.py`：测试 MySQL 连接器和 SQL 解析（已通过）

## 4. code_executor 组件迁移

- [x] 4.1 迁移 code_executor 组件代码（12 个文件）至 `server/python/src/ai/components/code_executor/`
- [x] 4.2 重写导入路径：`alon.configs.settings` → 适配本项目配置注入方式
- [x] 4.3 创建测试目录（已完成于 `tests/ai/unit/components/code_executor/`）
- [x] 4.4 编写 `test_code_executor.py`：测试代码执行器（Python3/JavaScript/Jinja2）（已通过）
- [x] 4.5 编写 `test_jinja2_transformer.py`、`test_code_node_provider.py`：测试模板转换器（已通过）

## 5. graphrag 组件迁移

- [x] 5.1 迁移 graphrag 组件代码（456 个文件）至 `server/python/src/ai/components/graphrag/`
- [x] 5.2 验证 graphrag 组件内部导入路径正确性（已验证）
- [x] 5.3 创建测试目录（已完成于 `tests/ai/unit/components/graphrag/`）
- [x] 5.4 编写 `test_client.py`：测试 GraphRAGClient 基础方法（已通过）
- [x] 5.5 编写 `test_graphrag.py`、`test_graph_data.py`：测试客户端和 GraphData 模型（已通过）
- [x] 5.6 编写 `test_imports.py`：验证导入正确性（已通过）

## 6. 集成验证

- [x] 6.1 运行 `pdm install` 安装新依赖（依赖已安装）
- [x] 6.2 运行 `docker compose up -d sandbox` 启动沙箱服务（已启动）
- [x] 6.3 运行全部单元测试：`pytest tests/ai/unit/components/`（216 passed, 1 skipped）
- [x] 6.4 验证 encryption 配置加载正确（已验证）
- [x] 6.5 验证 code_executor 与 sandbox 服务连通性（已验证）
- [x] 6.6 更新 `server/python/src/ai/components/__init__.py` 导出新组件

## 7. 文档更新

- [x] 7.1 更新 `server/python/src/ai/CLAUDE.md`，添加新组件说明（已更新测试路径）
- [x] 7.2 更新 `docker/CLAUDE.md`，添加 sandbox 服务说明（已添加服务说明）
