## 为什么

当前项目中 VO 层存在设计不一致：
1. `TreeNodeVoMixin` 已存在于 `framework/common/schemas.py`，但实际使用的是独立的 `TreeNodeVo`（直接继承 Pydantic BaseModel），导致代码重复和继承链不一致
2. ORM 层有 `PropertyMixin` 和 `PropertyAttributeMixin`，但 VO 层缺少对应的 Mixin，导致属性类实体（如 `SystemSetting`）无法复用通用字段

统一 VO Mixin 体系可以：
- 消除重复代码
- 保持 ORM 层与 VO 层的对应关系
- 方便后续扩展其他通用 VO Mixin

## 变更内容

1. **重构 TreeNodeVo**：改为继承 `VoMixin` + `TreeNodeVoMixin`，统一继承链
2. **新增 PropertyVoMixin**：对应 ORM 层 `PropertyMixin`，提供属性容器的通用字段
3. **新增 PropertyAttributeVoMixin**：对应 ORM 层 `PropertyAttributeMixin`，提供属性值的通用字段
4. **更新导出**：在 `framework/schemas/__init__.py` 中导出新增的 Mixin
5. **重构现有 Property 相关 VO**：
   - `SystemSettingResponse` → 使用 `PropertyVoMixin`
   - `SystemSettingAttributeResponse` → 使用 `PropertyAttributeVoMixin`
   - `ConsoleSystemSettingResponse` → 使用 `PropertyVoMixin`
   - `ConsoleSystemSettingAttributeResponse` → 使用 `PropertyAttributeVoMixin`

## 功能 (Capabilities)

### 新增功能
- `vo-mixins`: 统一 VO Mixin 体系，提供 PropertyVoMixin 和 PropertyAttributeVoMixin

### 修改功能
- 无（此变更为基础设施优化，不影响现有功能的行为）

## 影响

### 代码影响
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `framework/common/schemas.py` | 修改 | 新增 PropertyVoMixin、PropertyAttributeVoMixin |
| `framework/schemas/tree.py` | 修改 | TreeNodeVo 改为组合 VoMixin + TreeNodeVoMixin |
| `framework/schemas/__init__.py` | 修改 | 导出新增的 Mixin |
| `iam/schemas/admin/system_setting.py` | 修改 | SystemSettingResponse、SystemSettingAttributeResponse 改用 Mixin |
| `iam/schemas/console/system_setting.py` | 修改 | ConsoleSystemSettingResponse、ConsoleSystemSettingAttributeResponse 改用 Mixin |

### API 影响
- 无破坏性变更，API 响应格式保持不变

### 依赖影响
- 现有使用 `TreeNodeVo` 的代码（如 `DepartmentVo`）可能需要适配继承链变更

### 兼容性考虑
- TreeNodeVo 字段签名不变，现有代码无需修改即可兼容
