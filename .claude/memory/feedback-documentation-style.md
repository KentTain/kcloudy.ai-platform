---
name: feedback-documentation-style
description: CLAUDE.md 与 README.md 的文档职责划分规范
metadata:
  type: feedback
---

README.md 负责技术选型对比，CLAUDE.md 只需简洁的技术清单。

**Why:** 用户希望 CLAUDE.md 保持简洁，便于快速了解技术栈；详细的技术对比内容放在 README.md 中供需要时查阅。

**How to apply:**

1. **CLAUDE.md 技术选型部分**：每个技术栈一行，用表格列出技术栈名称、核心技术组合、详细文档链接
2. **README.md 技术栈对比部分**：包含完整技术选型对比表、各维度详细对比（如框架对比、ORM对比、测试框架对比等）
3. 子项目目录下的 CLAUDE.md 可包含该技术栈的详细技术清单
