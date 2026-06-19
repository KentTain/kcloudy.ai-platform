## 1. 代码清理

- [x] 1.1 删除 IAM 模块的重复中间件文件 `iam/middlewares/admin_auth_middleware.py`
- [x] 1.2 使用 CodeGraph 验证无其他代码导入已删除的模块

## 2. 修复导入

- [x] 2.1 修复 `iam/controllers/admin/system_setting_controller.py` 的导入路径
- [x] 2.2 修复 `tests/framework/integration/tenant/test_tenant_admin_api.py` 的导入路径

## 3. 修正逻辑错误

- [x] 3.1 移除 `system_setting_controller.py` 中错误的 `tenant_id` 逻辑
- [x] 3.2 更新相关注释和文档字符串，明确系统设置为平台级配置

## 4. 验证

- [x] 4.1 运行 `uv run pytest tests/framework/integration/tenant/` 验证测试通过
- [x] 4.2 运行 `uv run check-dev` 确保 lint 和类型检查通过
- [x] 4.3 使用 CodeGraph 确认中间件注册正确（只有 tenant 版本被注册）
