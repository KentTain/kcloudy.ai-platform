---
name: feedback-frontend-web-structure
description: 前端目录 CLAUDE.md 分层规范
metadata:
  type: feedback
---

前端目录采用三层 CLAUDE.md 结构：`web/` 写技术栈总览、`{框架}/` 写技术栈及功能模块、`src/` 写开发指南、`tests/` 写测试规范。

**Why:** 分层文档让 Claude Code 在不同目录工作时能获取恰当粒度的上下文，保持后端与前端文档结构的一致性。

**How to apply:**

1. **web/CLAUDE.md**：技术栈状态表、统一组件规范、各技术栈文档链接
2. **web/vue/CLAUDE.md**：核心技术表、功能模块清单（api/components/pages/stores等）、开发命令、子目录链接
3. **web/vue/src/CLAUDE.md**：目录结构、各层开发规范（API/组件/页面/Store）、类型定义规范
4. **web/vue/tests/CLAUDE.md**：测试目录结构、组件测试/Store测试规范、测试命令
