## 1. 基础设施准备

- [x] 1.1 创建 `framework/configs/encryption.py`，迁移 EncryptionSettings 配置模型
- [x] 1.2 在 `framework/common/exceptions.py` 中添加 BadRequestError 异常类
- [x] 1.3 更新 `server/python/pyproject.toml`，添加依赖：pycryptodome、datashaper、tiktoken、aiolimiter、json-repair
- [x] 1.4 在 `docker/docker-compose.backend.yml` 中添加 sandbox 服务定义

## 2. encryption 组件迁移

- [x] 2.1 迁移 encryption 组件代码（10 个文件）至 `server/python/src/ai/components/encryption/`
- [x] 2.2 重写导入路径：`alon.configs.infrastructure.encryption` → `framework.configs.encryption`
- [x] 2.3 重写导入路径：`alon.configs.settings` → 适配本项目配置注入方式
- [ ] 2.4 创建 `tests/ai/unit/components/encryption/` 测试目录
- [ ] 2.5 编写 `test_aes_encryption.py`：测试 AES 加密/解密功能
- [ ] 2.6 编写 `test_rsa_encryption.py`：测试 RSA 加密/解密功能
- [ ] 2.7 编写 `test_encryption_manager.py`：测试加密管理器初始化和实例获取

## 3. datasource 组件迁移

- [ ] 3.1 迁移 datasource 组件代码（15 个文件）至 `server/python/src/ai/components/datasource/`
- [ ] 3.2 重写导入路径：`alon.common.exceptions.BadRequestError` → `framework.common.exceptions.BadRequestError`
- [ ] 3.3 创建 `tests/ai/unit/components/datasource/` 测试目录
- [ ] 3.4 编写 `test_base_connector.py`：测试连接器基类接口
- [ ] 3.5 编写 `test_rdbms_connectors.py`：测试 MySQL/PostgreSQL 连接器（使用 mock）

## 4. code_executor 组件迁移

- [ ] 4.1 迁移 code_executor 组件代码（13 个文件）至 `server/python/src/ai/components/code_executor/`
- [ ] 4.2 重写导入路径：`alon.configs.settings` → 适配本项目配置注入方式
- [ ] 4.3 创建 `tests/ai/unit/components/code_executor/` 测试目录
- [ ] 4.4 编写 `test_code_executor.py`：测试代码执行器（Python3/JavaScript/Jinja2）
- [ ] 4.5 编写 `test_template_transformers.py`：测试模板转换器

## 5. graphrag 组件迁移

- [ ] 5.1 迁移 graphrag 组件代码（~457 个文件）至 `server/python/src/ai/components/graphrag/`
- [ ] 5.2 验证 graphrag 组件内部导入路径正确性
- [ ] 5.3 创建 `tests/ai/unit/components/graphrag/` 测试目录
- [ ] 5.4 编写 `test_client.py`：测试 GraphRAGClient 基础方法
- [ ] 5.5 编写 `test_llm_base.py`：测试 LLM 基类和限流功能
- [ ] 5.6 编写 `test_vector_stores.py`：测试向量存储接口

## 6. 集成验证

- [ ] 6.1 运行 `pdm install` 安装新依赖
- [ ] 6.2 运行 `docker compose up -d sandbox` 启动沙箱服务
- [ ] 6.3 运行全部单元测试：`pdm run pytest tests/ai/unit/components/`
- [ ] 6.4 验证 encryption 配置加载正确
- [ ] 6.5 验证 code_executor 与 sandbox 服务连通性
- [x] 6.6 更新 `server/python/src/ai/components/__init__.py` 导出新组件

## 7. 文档更新

- [ ] 7.1 更新 `server/python/src/ai/CLAUDE.md`，添加新组件说明
- [ ] 7.2 更新 `docker/CLAUDE.md`，添加 sandbox 服务说明
