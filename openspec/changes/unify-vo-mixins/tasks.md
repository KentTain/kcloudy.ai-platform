## 1. 新增 PropertyVoMixin 和 PropertyAttributeVoMixin

- [x] 1.1 在 `framework/common/schemas.py` 中添加 `PropertyVoMixin` 类
- [x] 1.2 在 `framework/common/schemas.py` 中添加 `PropertyAttributeVoMixin` 类
- [x] 1.3 更新 `framework/common/schemas.py` 的 `__all__` 导出列表

## 2. 重构 TreeNodeVo

- [x] 2.1 修改 `framework/schemas/tree.py` 中的 `TreeNodeVo`，改为继承 `VoMixin, TreeNodeVoMixin`
- [x] 2.2 确保 `TreeNodeVo` 包含 `id` 字段
- [x] 2.3 验证 `TreeNodeTreeVo` 继承链正确

## 3. 更新导出

- [x] 3.1 更新 `framework/schemas/__init__.py`，导出新增的 Mixin

## 4. 重构现有 Property 相关 VO

- [ ] 4.1 重构 `iam/schemas/admin/system_setting.py` 中的 `SystemSettingResponse`，使用 `PropertyVoMixin`
- [ ] 4.2 重构 `iam/schemas/admin/system_setting.py` 中的 `SystemSettingAttributeResponse`，使用 `PropertyAttributeVoMixin`
- [ ] 4.3 重构 `iam/schemas/console/system_setting.py` 中的 `ConsoleSystemSettingResponse`，使用 `PropertyVoMixin`
- [ ] 4.4 重构 `iam/schemas/console/system_setting.py` 中的 `ConsoleSystemSettingAttributeResponse`，使用 `PropertyAttributeVoMixin`

## 5. 编写单元测试

- [ ] 5.1 创建 `tests/framework/unit/schemas/test_vo_mixins.py`
- [ ] 5.2 测试 `PropertyVoMixin` 字段定义正确
- [ ] 5.3 测试 `PropertyAttributeVoMixin` 字段定义正确
- [ ] 5.4 测试 `TreeNodeVo` 继承链和序列化行为
- [ ] 5.5 测试 ORM 模型到 VO 的转换
- [ ] 5.6 测试重构后的 SystemSettingResponse 序列化行为

## 6. 验证与清理

- [ ] 6.1 运行所有相关单元测试
- [ ] 6.2 验证现有 API 响应格式不变
- [ ] 6.3 运行 Ruff 格式化和检查
