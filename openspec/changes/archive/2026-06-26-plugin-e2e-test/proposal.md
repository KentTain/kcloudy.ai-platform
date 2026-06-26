## 为什么

当前插件管理系统的测试全部基于 Mock，缺少对真实插件包的全流程验证。这导致：
1. 无法验证插件解析、安装、配置、运行的实际工作流程
2. 无法发现真实环境下的问题（如依赖安装失败、进程启动失败、通信协议错误）
3. 现有 tongyi、gpustack 等插件包未被测试覆盖，存在回归风险

现在需要建立 E2E 测试体系，使用真实插件包验证完整生命周期。

## 变更内容

### 新增功能

1. **插件 E2E 测试框架**：建立可重复执行的端到端测试基础设施
   - 测试夹具管理（测试租户、测试插件包）
   - 测试环境隔离（独立数据库、Redis 命名空间）
   - 测试数据清理机制

2. **插件全流程测试用例**：
   - 解析导入测试：验证真实插件包的 manifest 解析
   - 安装流程测试：验证虚拟环境创建、依赖安装、OSS 上传
   - 配置验证测试：验证凭证配置和有效性校验
   - 运行时测试：验证进程启动、停止、通信协议
   - 模型调用测试：验证 tongyi/gpustack 的实际 API 调用

3. **测试辅助工具**：
   - 插件测试工具类（PluginTestHelper）
   - 测试环境配置管理
   - 测试日志和断言增强

## 功能 (Capabilities)

### 新增功能

- `plugin-e2e-test-framework`: E2E 测试框架基础设施，包括测试夹具、环境隔离、清理机制
- `plugin-lifecycle-test`: 插件生命周期全流程测试用例（解析→安装→配置→运行→调用）

### 修改功能

无（本变更为新增测试能力，不修改现有功能需求）

## 影响

### 受影响的代码

| 目录 | 影响 |
|------|------|
| `server/python/tests/ai/e2e/` | 新增 E2E 测试目录和测试文件 |
| `server/python/tests/ai/fixtures/` | 新增测试夹具和辅助工具 |
| `server/python/tests/conftest.py` | 可能需要添加 E2E 测试配置 |

### 受影响的 API

无直接 API 变更，测试将调用现有 API 端点：
- `POST /ai/console/v1/plugins/installations` - 安装插件
- `POST /ai/console/v1/plugins/installations/{plugin_id}/start` - 启动插件
- `GET /ai/console/v1/plugins/installations/{plugin_id}/config` - 获取配置
- `POST /ai/console/v1/plugins/credentials` - 配置凭证

### 依赖和系统

| 依赖 | 说明 |
|------|------|
| PostgreSQL | 需要测试数据库，使用独立 Schema |
| Redis | 需要测试 Redis，使用独立 DB |
| MinIO | 需要测试对象存储，使用独立 Bucket |
| tongyi API Key | 用于验证通义千问插件的真实调用 |
| gpustack API Key | 用于验证 GPUStack 插件的真实调用 |

### 兼容性考虑

- E2E 测试通过 `pytest.mark.e2e` 标记，默认不执行
- 测试需要环境变量配置 API Key，无配置时跳过
- 测试不污染现有数据，使用独立租户和命名空间
