---
name: feedback-backend-server-structure
description: 后端目录 CLAUDE.md 分层规范
type: feedback
---

后端目录采用层次化文档结构，严格控制文档层级。

**Why:** 分层文档让 Claude Code 在不同目录工作时能获取恰当粒度的上下文，避免在子目录工作时加载过多无关信息。

**How to apply:**

**CLAUDE.md 层级限制：**
- `server/CLAUDE.md`：技术栈总览层 - 技术栈状态、架构概览、各技术栈链接
- `server/{技术栈}/CLAUDE.md`：技术栈层 - 技术栈概述、功能模块清单、开发命令
- `server/{技术栈}/src/CLAUDE.md`：开发目录层 - 各模块开发指南
- `server/{技术栈}/src/{模块}/CLAUDE.md`：模块层 - 模块详细开发指南
- `server/{技术栈}/tests/CLAUDE.md`：测试目录层 - 测试概述和标记
- `server/{技术栈}/tests/{模块}/CLAUDE.md`：模块测试层 - 模块测试规范

**README.md 层级限制：**
- `server/{技术栈}/tests/README.md`：测试目录说明
- 不深入到模块级子目录

**禁止：**
- README.md 不允许出现在模块级目录
- CLAUDE.md 不允许出现在子模块级目录（如 fixtures/、unit/）

**原则：**
- 父层级只写本层级内容，引用子目录 CLAUDE.md
- 具体模块目录结构以实际代码为准，本规范仅定义层级规则
