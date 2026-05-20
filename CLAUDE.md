# CLAUDE.md

本文件为 Claude Code 在项目中工作时提供指导。

## 项目概述

InitProject 是一个多技术栈的 AI 助手平台演示项目，提供多种后端和前端技术选型。项目采用模块化结构，每个技术栈作为独立子项目存在。

**核心目标：** 提供可对比、可学习的多技术栈实现参考。

## 项目结构

```text
init_project/
├── server/                    # 后端服务
├── web/                       # 前端 PC 项目
├── app/                       # 前端 Mobile 项目
├── docker/                    # Docker 部署配置
└── docs/                      # 项目文档
```

## 子项目文档

| 子项目 | 说明 | 详细文档 |
|--------|------|----------|
| server/ | 后端服务（Python/Rust/Java/.NET） | [server/CLAUDE.md](server/CLAUDE.md) |
| web/ | 前端 PC 项目（Vue/React） | [web/CLAUDE.md](web/CLAUDE.md) |
| app/ | 前端 Mobile 项目（Flutter/React Native） | [app/CLAUDE.md](app/CLAUDE.md) |

## 环境要求

| 类别 | 依赖 |
|------|------|
| 后端 | Python 3.12+ / Rust 1.95+ / PostgreSQL 14+ / Redis 6+ |
| 前端 | Node.js 22+ / pnpm 10+ |

## License

Copyright © 2025 Moles. All Rights Reserved.
