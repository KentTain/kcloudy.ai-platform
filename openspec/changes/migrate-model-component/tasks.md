# Model 组件迁移任务清单

## 1. 基础设施搭建

- [x] 1.1 创建 `ai/components/model/` 目录结构
- [x] 1.2 迁移 `entities/` 模型配置实体（ModelType, ModelConfig 等）
- [x] 1.3 迁移 `errors/` 异常定义（ModelInvocationError, ModelCredentialError 等）
- [x] 1.4 迁移 `schema/` Schema 定义（ModelSchema, ProviderSchema 等）
- [x] 1.5 创建 `__init__.py` 文件，配置模块导出

## 2. Provider 管理实现

- [x] 2.1 迁移 `internal/provider_configuration.py` - Provider 配置实体
- [x] 2.2 迁移 `internal/provider_manager.py` - Provider 管理器
- [x] 2.3 迁移 `internal/model_provider_factory.py` - Provider 工厂
- [x] 2.4 适配 `framework/cache/` 实现凭证缓存
- [x] 2.5 实现 Provider ID 解析逻辑（`<plugin_id>/<provider_type>` 格式）

## 3. 模型实例实现

- [x] 3.1 迁移 `model_providers/__base__/ai_model.py` - AI 模型基类
- [x] 3.2 迁移 `model_providers/__base__/large_language_model.py` - LLM 基类
- [x] 3.3 迁移 `internal/model_instance_factory.py` - 模型实例工厂
- [x] 3.4 对接 `ai/components/plugin/client/model_client.py`
- [x] 3.5 实现错误转换逻辑（PluginError → ModelInvocationError）

## 4. LLM 服务实现

- [x] 4.1 迁移 `services/llm_service.py` - LLMService 核心
- [x] 4.2 实现 `invoke` 非流式调用方法
- [x] 4.3 实现 `stream` 流式调用方法
- [x] 4.4 迁移 `services/management_service.py` - 模型清单管理
- [x] 4.5 实现单例模式和租户隔离

## 5. 数据库模型

- [x] 5.1 创建 `ai/models/model_provider.py` - 模型提供商 ORM
- [x] 5.2 创建 `ai/models/model_config.py` - 模型配置 ORM
- [x] 5.3 创建 Alembic 迁移脚本
- [x] 5.4 执行数据库迁移验证

## 6. 回调与工具

- [x] 6.1 迁移 `callbacks/` 回调机制（可选，按需迁移）
- [ ] 6.2 迁移 `utils/` 工具函数（按需迁移）

## 7. 测试与验证

- [x] 7.1 编写 `LLMService` 单元测试
- [x] 7.2 编写 `ModelProviderFactory` 单元测试
- [x] 7.3 编写 `ModelInstanceFactory` 单元测试
- [x] 7.4 编写凭证缓存集成测试
- [x] 7.5 编写流式调用端到端测试
- [x] 7.6 运行完整测试套件验证

## 8. 文档与收尾

- [x] 8.1 更新 `ai/components/model/CLAUDE.md` 模块文档
- [x] 8.2 编写迁移日志，记录与 Alon 的差异
- [x] 8.3 代码审查和清理
