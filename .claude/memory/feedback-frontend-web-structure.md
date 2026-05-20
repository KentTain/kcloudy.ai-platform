---
name: feedback-frontend-web-structure
description: 前端目录 CLAUDE.md 分层规范
type: feedback
---

前端目录采用层次化文档结构，严格控制文档层级。

**Why:** 分层文档让 Claude Code 在不同目录工作时能获取恰当粒度的上下文，保持后端与前端文档结构的一致性。

**How to apply:**

**CLAUDE.md 层级限制：**
- `web/CLAUDE.md`：根目录层 - 技术栈状态表、项目结构概述、子目录链接
- `web/{技术栈}/CLAUDE.md`：技术栈层 - 技术栈概述、功能模块清单、开发命令、子目录链接
- `web/{技术栈}/src/CLAUDE.md`：开发目录层 - 目录结构、模块链接、通用开发规范
- `web/{技术栈}/src/{模块}/CLAUDE.md`：模块层 - 模块详细开发指南
- `web/{技术栈}/tests/CLAUDE.md`：测试目录层 - 测试概述、测试模块链接
- `web/{技术栈}/tests/{模块}/CLAUDE.md`：模块测试层 - 模块测试规范

**README.md 层级限制：**
- `web/README.md`：根目录层 - 技术栈对比、统一架构、快速开始
- 不深入到技术栈级（`web/vue/README.md` 不应存在）

**禁止：**
- README.md 不允许出现在技术栈级目录
- CLAUDE.md 不允许出现在子模块级目录（如 components/、stores/）

**原则：**
- 父层级只写本层级内容，引用子目录 CLAUDE.md
- 具体模块目录结构以实际代码为准，本规范仅定义层级规则
