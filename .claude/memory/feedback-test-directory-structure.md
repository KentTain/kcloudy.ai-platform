---
name: feedback-test-directory-structure
description: 测试目录分层规范
type: feedback
---

测试目录按功能模块组织，文档层级严格控制。

**Why:** 清晰的测试目录结构便于定位测试代码，fixtures 集中管理测试数据，unit/integration 分离测试类型。

**How to apply:**

**文档层级限制：**
- CLAUDE.md 只到模块级（`tests/{模块}/`）
- README.md 只到测试目录级（`tests/`）

**标准子目录：**

| 目录 | 说明 |
|------|------|
| fixtures/ | 测试夹具和数据（data/ 存放 JSON/YAML，helpers.py 辅助函数） |
| unit/ | 单元测试（使用 mock 隔离依赖，对应源码目录结构） |
| integration/ | 集成测试（真实服务交互） |
| examples/ | 示例代码测试 |
| studies/ | 代码预研（非正式测试） |

**测试文件命名：** `test_*.py`

**禁止：**
- fixtures/, unit/, integration/, studies/ 等子目录下不允许创建 README.md 或 CLAUDE.md
- 具体模块目录结构以实际代码为准，本规范仅定义层级规则
