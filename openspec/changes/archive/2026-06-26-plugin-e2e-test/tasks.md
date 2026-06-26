## 1. 测试框架搭建

- [x] 1.1 创建 E2E 测试目录结构 `tests/ai/e2e/` 和 `tests/ai/e2e/helpers/`
- [x] 1.2 创建 `conftest.py`，定义 `@pytest.mark.e2e` 标记和共享夹具
- [x] 1.3 实现测试租户夹具 `test_tenant_id`，自动创建和清理隔离环境
- [x] 1.4 实现数据库会话夹具 `e2e_session`，支持独立事务和自动回滚
- [x] 1.5 实现插件包路径夹具 `plugin_package_path`，支持获取真实插件包路径

## 2. 测试辅助工具

- [x] 2.1 创建 `helpers/plugin_test_helper.py` 测试辅助工具类
- [x] 2.2 实现 `wait_for_plugin_status` 方法，支持轮询等待插件状态
- [x] 2.3 实现 `assert_plugin_installed` 方法，验证插件安装成功
- [x] 2.4 实现 `assert_plugin_running` 方法，验证插件进程运行正常
- [x] 2.5 实现 `cleanup_plugin` 方法，安全清理插件资源

## 3. 解析导入测试

- [x] 3.1 创建 `test_plugin_parse.py` 测试文件
- [x] 3.2 实现测试用例：解析 tongyi 插件包并验证元数据
- [x] 3.3 实现测试用例：解析 gpustack 插件包并验证元数据
- [x] 3.4 实现测试用例：解析无效插件包（缺少 manifest）验证错误处理

## 4. 安装流程测试

- [x] 4.1 创建 `test_plugin_install.py` 测试文件
- [x] 4.2 实现测试用例：安装 tongyi 插件并验证虚拟环境创建
- [x] 4.3 实现测试用例：验证重复安装返回正确错误
- [x] 4.4 实现测试用例：卸载已安装插件并验证资源清理
- [x] 4.5 实现测试用例：验证 OSS 上传正确

## 5. 配置验证测试

- [x] 5.1 创建 `test_plugin_configure.py` 测试文件
- [x] 5.2 实现 API Key 夹具，从环境变量读取（无配置时跳过）
- [x] 5.3 实现测试用例：配置 tongyi 凭证并验证加密存储
- [x] 5.4 实现测试用例：验证凭证脱敏显示正确
- [x] 5.5 实现测试用例：更新凭证并验证保留未修改字段

## 6. 运行时测试

- [x] 6.1 创建 `test_plugin_runtime.py` 测试文件
- [x] 6.2 实现测试用例：启动 tongyi 插件并验证进程状态
- [x] 6.3 实现测试用例：停止运行中的插件并验证进程退出
- [x] 6.4 实现测试用例：验证插件状态查询 API 正确
- [x] 6.5 实现测试用例：验证插件崩溃后状态更新正确

## 7. 模型调用测试

- [x] 7.1 创建 `test_plugin_invoke.py` 测试文件
- [x] 7.2 实现测试用例：调用 tongyi 模型并验证响应
- [x] 7.3 实现测试用例：调用 gpustack 模型并验证响应
- [x] 7.4 实现测试用例：流式调用 tongyi 模型并验证增量响应
- [x] 7.5 实现测试用例：无效 API Key 调用验证错误处理

## 8. 完整生命周期测试

- [x] 8.1 创建 `test_plugin_full_lifecycle.py` 测试文件
- [x] 8.2 实现测试用例：tongyi 插件完整生命周期（安装→配置→启动→调用→停止→卸载）
- [x] 8.3 实现测试用例：gpustack 插件完整生命周期
- [x] 8.4 验证所有测试资源正确清理

## 9. 测试验证和文档

- [x] 9.1 运行所有 E2E 测试验证通过 `pytest -m e2e -v`（13 个用例通过，其余跳过/需环境配置）
- [x] 9.2 更新 `tests/ai/CLAUDE.md` 添加 E2E 测试说明
- [x] 9.3 创建测试运行脚本 `scripts/run_e2e_tests.sh`
