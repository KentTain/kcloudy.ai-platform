# InitProject - Minimal AI Assistant Platform

This is a multi-tech-stack AI assistant platform demo project, providing various backend and frontend technology options for learning and comparing different implementation approaches.

## Project Structure

```text
init_project/
├── server/                    # Backend Services
│   ├── python/                # Python Backend (FastAPI)
│   ├── java/                  # Java Backend (Spring Boot)
│   └── rust/                  # Rust Backend (Actix-web)
├── web/                       # Frontend PC Projects
│   ├── vue/                   # Vue 3 + TypeScript
│   └── react/                 # React + TypeScript
├── app/                       # Frontend Mobile Projects
├── docker/                    # Docker Deployment
├── docs/                      # Documentation
└── tests/                     # Test Code
```

## Technology Stack

### Backend Services (server/)

| Language | Framework | Directory | Status |
|----------|-----------|-----------|--------|
| Python | FastAPI + SQLAlchemy | [server/python](server/python) | ✅ Available |
| Java | Spring Boot | [server/java](server/java) | 🚧 Planned |
| Rust | Actix-web | [server/rust](server/rust) | 🚧 Planned |

### Frontend PC Projects (web/)

| Framework | Language | Directory | Status |
|-----------|----------|-----------|--------|
| Vue | TypeScript | [web/vue](web/vue) | 🚧 Planned |
| React | TypeScript | [web/react](web/react) | 🚧 Planned |

### Frontend Mobile Projects (app/)

| Framework | Language | Directory | Status |
|-----------|----------|-----------|--------|
| Flutter | Dart | [app/flutter](app/flutter) | 🚧 Planned |
| React Native | TypeScript | [app/react-native](app/react-native) | 🚧 Planned |

## Quick Start

### Python Backend

```bash
cd server/python

# Install dependencies
uv sync

# Configuration
cp config/application-local.yml.example config/application-local.yml

# Start server
uv run runserver
```

Visit: <http://localhost:8000/docs>

See [server/python/README.md](server/python/README.md) for details.

## Requirements

### Backend

- Python 3.12+ / uv
- Java 21+ / Maven (Planned)
- Rust 1.75+ / Cargo (Planned)
- PostgreSQL 14+
- Redis 6+

### Frontend

- Node.js 22+
- pnpm 10+

## Features

### Core Capabilities

- **RESTful API Design**: Unified JSON response format
- **AI Framework Integration**: LangChain 1.3.0, LangGraph 1.2.0
- **Database Support**: PostgreSQL + pgvector (vector search)
- **Cache Support**: Redis high-performance caching
- **Comprehensive Error Handling**: Global exception handling and automatic error tracking

### Data & Storage

- **Database Integration**: SQLAlchemy 2.0 + Alembic migrations
- **Layered Configuration**: YAML-based multi-environment configuration system

## Module Documentation

| Module | Documentation | Description |
|--------|---------------|-------------|
| Python Backend | [server/python/README.md](server/python/README.md) | FastAPI backend features, installation |
| Docker Deployment | [docker/README.md](docker/README.md) | Docker Compose deployment guide |

## License

Copyright © 2025 Moles. All Rights Reserved.
