# CLAUDE.md

本文件为 Claude Code 在项目中工作时提供指导。

## 项目定位

AI Platform 是一个多技术栈的 AI 助手平台演示项目，提供多种后端和前端技术选型。项目采用模块化结构，每种技术栈作为独立子项目存在，便于技术选型对比和团队学习。

## 架构规则

| 规则 | 说明 |
|------|------|
| 代码查找 | 优先使用 CodeGraph，避免 grep 扫描 |
| Git 提交 | 中文 commit message，遵循约定式提交 |
| Markdown | 中文文档，代码示例可保留英文 |

## 子项目导航

| 目录 | 说明 | 详细文档 |
|------|------|----------|
| server/ | 后端服务（Python/Rust/Java/.NET） | [server/CLAUDE.md](server/CLAUDE.md) |
| web/ | 前端 PC 项目（Vue/React） | [web/CLAUDE.md](web/CLAUDE.md) |
| app/ | 前端 Mobile 项目（Flutter/React Native） | [app/CLAUDE.md](app/CLAUDE.md) |
| docker/ | Docker 部署配置 | [docker/CLAUDE.md](docker/CLAUDE.md) |

## 环境要求

| 类别 | 依赖 |
|------|------|
| 后端 | Python 3.12+ / Rust 1.95+ / PostgreSQL 14+ / Redis 6+ |
| 前端 | Node.js 22+ / pnpm 10+ |

<!-- superpowers-zh:begin (do not edit between these markers) -->
# Superpowers-ZH 技能框架

本项目已安装 superpowers-zh 技能框架（20 个技能）。

## 核心规则

1. **收到任务时检查匹配的 skill** —— 哪怕只有 1% 可能性
2. **设计先于编码** —— 功能需求先用 brainstorming
3. **测试先于实现** —— 写代码前先写测试（TDD）
4. **验证先于完成** —— 声称完成前必须运行验证命令

## 如何使用

使用 Skill 工具加载技能。技能位于 .claude/skills/ 目录。

**常用技能：** brainstorming、test-driven-development、systematic-debugging、verification-before-completion
<!-- superpowers-zh:end -->
