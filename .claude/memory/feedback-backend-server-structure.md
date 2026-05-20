---
name: feedback-backend-server-structure
description: 后端目录 CLAUDE.md 分层规范
metadata:
  type: feedback
---

后端目录采用三层 CLAUDE.md 结构：`server/` 写技术栈总览、`{技术栈}/` 写技术栈及功能模块、`src/` 写开发指南、`tests/` 写测试规范。

**Why:** 分层文档让 Claude Code 在不同目录工作时能获取恰当粒度的上下文，避免在子目录工作时加载过多无关信息。

**How to apply:**

1. **server/CLAUDE.md**：技术栈状态表、MVC架构概览、统一基础设施、各技术栈文档链接
2. **server/python/CLAUDE.md**：核心技术表、功能模块清单（demo/framework）、开发命令、子目录链接
3. **server/python/src/CLAUDE.md**：目录结构、各层开发规范（Controller/Service/Model/Schema）、示例目录
4. **server/python/tests/CLAUDE.md**：测试目录结构、测试类型说明、fixtures数据规范、测试标记、常用命令
