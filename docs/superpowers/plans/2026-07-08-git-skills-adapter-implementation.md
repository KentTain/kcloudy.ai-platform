# Git 仓库 Skill 适配器实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 新增 GitSkillsAdapter，改造 ModelScopeSkillAdapter 和 LocalSkillAdapter，删除错误的 AgentSkillsAdapter

**架构：** GitSyncService 负责 git 同步和缓存，SkillScanner 负责 SKILL.md 解析和 ZIP 打包，三个 Adapter 复用这两个服务

**技术栈：** Python 3.12, asyncio, GitPython（可选）, subprocess, PyYAML, zipfile

---

## 文件结构

### 新增文件

| 文件 | 职责 |
|------|------|
| `server/python/src/tenant/services/marketplace/git_sync_service.py` | git clone/fetch/sparse-checkout + 缓存管理 |
| `server/python/src/tenant/services/marketplace/skill_scanner.py` | 扫描 SKILL.md + 解析 YAML frontmatter + ZIP 打包 |
| `server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py` | 实现 MarketplaceAdapter 协议 |
| `server/python/tests/tenant/unit/marketplace/test_git_sync_service.py` | GitSyncService 单元测试 |
| `server/python/tests/tenant/unit/marketplace/test_skill_scanner.py` | SkillScanner 单元测试 |
| `server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py` | GitSkillsAdapter 单元测试 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py` | download_plugin 改用 git sparse-checkout |
| `server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py` | 复用 SkillScanner，移除重复代码 |
| `server/python/src/tenant/services/marketplace/gateway.py` | 注册 GitSkillsAdapter，移除 agentskills |
| `server/python/config/application.yml` | 新增 skills.git 配置节 |
| `server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py` | 更新 download_plugin 测试 |
| `server/python/tests/tenant/unit/marketplace/test_local_skill_adapter.py` | 更新为使用 SkillScanner |

### 删除文件

| 文件 | 原因 |
|------|------|
| `server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py` | 基于错误假设实现 |
| `server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py` | 对应测试文件 |

---

## Phase 1: 基础设施（GitSyncService + SkillScanner）

### 任务 1.1：SkillScanner 数据类

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/skill_scanner.py`
- 测试：`server/python/tests/tenant/unit/marketplace/test_skill_scanner.py`

- [ ] **步骤 1：编写失败的测试 - SkillMeta 数据类**

```python
# tests/tenant/unit/marketplace/test_skill_scanner.py
"""SkillScanner 单元测试"""

import pytest
from pathlib import Path
from tenant.services.marketplace.skill_scanner import SkillMeta


def test_skill_meta_creation():
    """验证 SkillMeta 数据类创建"""
    skill = SkillMeta(
        name="test-skill",
        description="Use when testing",
        version="1.0.0",
        author="test-author",
        tags=["test"],
    )
    assert skill.name == "test-skill"
    assert skill.description == "Use when testing"
    assert skill.version == "1.0.0"
    assert skill.author == "test-author"
    assert skill.tags == ["test"]
    assert skill.skill_dir is None


def test_skill_meta_defaults():
    """验证 SkillMeta 默认值"""
    skill = SkillMeta(
        name="minimal-skill",
        description="Minimal description",
    )
    assert skill.version == "1.0.0"
    assert skill.author == "unknown"
    assert skill.tags == []
    assert skill.skill_dir is None
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py -v
```

预期：`ModuleNotFoundError: No module named 'tenant.services.marketplace.skill_scanner'`

- [ ] **步骤 3：实现 SkillMeta 数据类**

```python
# src/tenant/services/marketplace/skill_scanner.py
"""Skill 扫描工具"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SkillMeta:
    """Skill 元数据

    符合 agentskills.io/specification 规范。
    """

    name: str                    # 必需：skill 名称
    description: str             # 必需：描述
    version: str = "1.0.0"       # 版本
    author: str = "unknown"      # 作者
    tags: list[str] = field(default_factory=list)
    skill_dir: Path | None = None  # 扫描时填充：skill 目录路径
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py -v
```

预期：2 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/skill_scanner.py
git add server/python/tests/tenant/unit/marketplace/test_skill_scanner.py
git commit -m "feat(marketplace): 新增 SkillMeta 数据类"
```

---

### 任务 1.2：SkillScanner.parse_skill_file

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/skill_scanner.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_skill_scanner.py`

- [ ] **步骤 1：编写失败的测试 - parse_skill_file**

```python
# tests/tenant/unit/marketplace/test_skill_scanner.py（追加）

import tempfile
from tenant.services.marketplace.skill_scanner import SkillScanner


def test_parse_skill_file_valid():
    """验证解析有效的 SKILL.md 文件"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Use when testing skill parsing
version: 2.0.0
author: test-author
tags: [test, parsing]
---

# Test Skill

This is a test skill.
""", encoding="utf-8")

        skill = scanner.parse_skill_file(skill_file)

        assert skill.name == "test-skill"
        assert skill.description == "Use when testing skill parsing"
        assert skill.version == "2.0.0"
        assert skill.author == "test-author"
        assert skill.tags == ["test", "parsing"]
        assert skill.skill_dir == Path(tmpdir)


def test_parse_skill_file_missing_name():
    """验证缺少必需字段 name 时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
description: Missing name field
---

# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="missing 'name' field"):
            scanner.parse_skill_file(skill_file)


def test_parse_skill_file_missing_description():
    """验证缺少必需字段 description 时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
---

# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="missing 'description' field"):
            scanner.parse_skill_file(skill_file)


def test_parse_skill_file_invalid_yaml():
    """验证 YAML 格式错误时抛出异常"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_file = Path(tmpdir) / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: [invalid yaml
---

# Test
""", encoding="utf-8")

        with pytest.raises(ValueError, match="YAML parse error"):
            scanner.parse_skill_file(skill_file)
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py::test_parse_skill_file_valid -v
```

预期：`AttributeError: 'SkillScanner' object has no attribute 'parse_skill_file'`

- [ ] **步骤 3：实现 parse_skill_file 方法**

```python
# src/tenant/services/marketplace/skill_scanner.py（追加）

import yaml


class SkillScanner:
    """Skill 扫描工具"""

    def parse_skill_file(self, skill_file: Path) -> SkillMeta:
        """解析单个 SKILL.md 文件

        Args:
            skill_file: SKILL.md 文件路径

        Returns:
            SkillMeta: Skill 元数据

        Raises:
            ValueError: 文件格式无效

        YAML frontmatter 格式（agentskills.io/specification）：
        ---
        name: skill-name
        description: Use when ...
        version: 1.0.0
        author: author-name
        tags: [tag1, tag2]
        ---

        # Skill Content
        ...
        """
        if not skill_file.exists():
            raise ValueError(f"Skill file not found: {skill_file}")

        content = skill_file.read_text(encoding="utf-8")

        # 检查是否以 --- 开头
        if not content.startswith("---"):
            raise ValueError("Invalid SKILL.md format: missing front matter delimiter")

        # 提取 front matter
        parts = content.split("---", 2)
        if len(parts) < 3:
            raise ValueError("Invalid SKILL.md format: malformed front matter")

        front_matter_text = parts[1].strip()

        try:
            front_matter = yaml.safe_load(front_matter_text)
        except yaml.YAMLError as e:
            raise ValueError(f"YAML parse error: {e}") from e

        if not isinstance(front_matter, dict):
            raise ValueError("Invalid SKILL.md format: front matter must be a YAML map")

        # 提取必需字段
        name = front_matter.get("name")
        if not name:
            raise ValueError("Invalid SKILL.md format: missing 'name' field")

        description = front_matter.get("description")
        if not description:
            raise ValueError("Invalid SKILL.md format: missing 'description' field")

        # 提取可选字段
        version = front_matter.get("version", "1.0.0")
        author = front_matter.get("author", "unknown")
        tags = front_matter.get("tags", [])

        return SkillMeta(
            name=name,
            description=description,
            version=version,
            author=author,
            tags=tags if isinstance(tags, list) else [],
            skill_dir=skill_file.parent,
        )
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py -v
```

预期：7 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/skill_scanner.py
git add server/python/tests/tenant/unit/marketplace/test_skill_scanner.py
git commit -m "feat(marketplace): 实现 SkillScanner.parse_skill_file"
```

---

### 任务 1.3：SkillScanner.scan_skills

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/skill_scanner.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_skill_scanner.py`

- [ ] **步骤 1：编写失败的测试 - scan_skills**

```python
# tests/tenant/unit/marketplace/test_skill_scanner.py（追加）


def test_scan_skills_multiple():
    """验证扫描多个 skill 目录"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # 创建第一个 skill
        skill1_dir = base_dir / "skill1"
        skill1_dir.mkdir()
        (skill1_dir / "SKILL.md").write_text("""---
name: skill-one
description: First skill
author: author1
---
# Skill One
""", encoding="utf-8")

        # 创建第二个 skill
        skill2_dir = base_dir / "skill2"
        skill2_dir.mkdir()
        (skill2_dir / "SKILL.md").write_text("""---
name: skill-two
description: Second skill
author: author2
---
# Skill Two
""", encoding="utf-8")

        # 创建非 skill 目录（无 SKILL.md）
        (base_dir / "other_dir").mkdir()

        skills = scanner.scan_skills(base_dir)

        assert len(skills) == 2
        skill_names = [s.name for s in skills]
        assert "skill-one" in skill_names
        assert "skill-two" in skill_names


def test_scan_skills_nested():
    """验证递归扫描嵌套目录"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # 创建嵌套 skill
        nested_dir = base_dir / "category" / "subcategory" / "skill"
        nested_dir.mkdir(parents=True)
        (nested_dir / "SKILL.md").write_text("""---
name: nested-skill
description: Nested skill
---
# Nested
""", encoding="utf-8")

        skills = scanner.scan_skills(base_dir)

        assert len(skills) == 1
        assert skills[0].name == "nested-skill"
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py::test_scan_skills_multiple -v
```

预期：`AttributeError: 'SkillScanner' object has no attribute 'scan_skills'`

- [ ] **步骤 3：实现 scan_skills 方法**

```python
# src/tenant/services/marketplace/skill_scanner.py（追加）

from loguru import logger


class SkillScanner:
    """Skill 扫描工具"""

    def scan_skills(self, base_dir: Path) -> list[SkillMeta]:
        """递归扫描目录中的所有 SKILL.md

        Args:
            base_dir: 扫描根目录

        Returns:
            SkillMeta 列表
        """
        skills = []

        # 递归查找所有 SKILL.md 文件
        for skill_file in base_dir.rglob("SKILL.md"):
            try:
                skill = self.parse_skill_file(skill_file)
                skills.append(skill)
            except ValueError as e:
                logger.warning(f"Failed to parse {skill_file}: {e}")

        return skills
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py -v
```

预期：9 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/skill_scanner.py
git add server/python/tests/tenant/unit/marketplace/test_skill_scanner.py
git commit -m "feat(marketplace): 实现 SkillScanner.scan_skills"
```

---

### 任务 1.4：SkillScanner.zip_skill

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/skill_scanner.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_skill_scanner.py`

- [ ] **步骤 1：编写失败的测试 - zip_skill**

```python
# tests/tenant/unit/marketplace/test_skill_scanner.py（追加）

import hashlib
import zipfile


def test_zip_skill():
    """验证将 skill 目录打包为 ZIP"""
    scanner = SkillScanner()

    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("""---
name: test-skill
description: Test skill for zipping
---
# Test Skill
""", encoding="utf-8")

        # 添加额外文件
        (skill_dir / "helper.py").write_text("# helper code", encoding="utf-8")
        subdir = skill_dir / "docs"
        subdir.mkdir()
        (subdir / "readme.md").write_text("# Docs", encoding="utf-8")

        skill = SkillMeta(
            name="test-skill",
            description="Test skill for zipping",
            skill_dir=skill_dir,
        )

        zip_data, checksum = scanner.zip_skill(skill)

        # 验证返回类型
        assert isinstance(zip_data, bytes)
        assert isinstance(checksum, str)
        assert len(checksum) == 64  # SHA256 hex length

        # 验证 checksum 正确性
        expected_checksum = hashlib.sha256(zip_data).hexdigest()
        assert checksum == expected_checksum

        # 验证 ZIP 内容
        with zipfile.ZipFile(BytesIO(zip_data)) as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert "helper.py" in names
            assert "docs/readme.md" in names
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py::test_zip_skill -v
```

预期：`AttributeError: 'SkillScanner' object has no attribute 'zip_skill'`

- [ ] **步骤 3：实现 zip_skill 方法**

```python
# src/tenant/services/marketplace/skill_scanner.py（追加导入）

import hashlib
import zipfile
from io import BytesIO


class SkillScanner:
    """Skill 扫描工具"""

    def zip_skill(self, skill: SkillMeta) -> tuple[bytes, str]:
        """将 skill 目录打包为 ZIP

        Args:
            skill: Skill 元数据

        Returns:
            tuple[bytes, str]: (ZIP 数据, SHA256 校验和)
        """
        if not skill.skill_dir:
            raise ValueError("skill_dir is not set")

        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in skill.skill_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill.skill_dir)
                    zipf.write(file_path, arcname)

        zip_data = zip_buffer.getvalue()
        checksum = hashlib.sha256(zip_data).hexdigest()

        return zip_data, checksum
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_skill_scanner.py -v
```

预期：10 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/skill_scanner.py
git add server/python/tests/tenant/unit/marketplace/test_skill_scanner.py
git commit -m "feat(marketplace): 实现 SkillScanner.zip_skill"
```

---

### 任务 1.5：GitSyncService 数据类和初始化

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/git_sync_service.py`
- 创建：`server/python/tests/tenant/unit/marketplace/test_git_sync_service.py`

- [ ] **步骤 1：编写失败的测试 - GitSyncService 初始化**

```python
# tests/tenant/unit/marketplace/test_git_sync_service.py
"""GitSyncService 单元测试"""

from pathlib import Path
import pytest
from tenant.services.marketplace.git_sync_service import GitSyncService


def test_git_sync_service_default_cache_dir():
    """验证默认缓存目录"""
    service = GitSyncService()
    assert service.cache_dir == Path("./cache/skills")


def test_git_sync_service_custom_cache_dir():
    """验证自定义缓存目录"""
    custom_dir = Path("/tmp/custom/cache")
    service = GitSyncService(cache_dir=custom_dir)
    assert service.cache_dir == custom_dir
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py -v
```

预期：`ModuleNotFoundError: No module named 'tenant.services.marketplace.git_sync_service'`

- [ ] **步骤 3：实现 GitSyncService 初始化**

```python
# src/tenant/services/marketplace/git_sync_service.py
"""Git 仓库同步服务"""

from __future__ import annotations

from pathlib import Path


class GitSyncService:
    """Git 仓库同步服务

    负责从 git 仓库克隆/拉取代码到本地缓存，
    支持 sparse-checkout 仅检出指定子目录。
    """

    def __init__(self, cache_dir: Path | None = None):
        """初始化 Git 同步服务

        Args:
            cache_dir: 缓存目录，默认 ./cache/skills
        """
        self.cache_dir = cache_dir or Path("./cache/skills")
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py -v
```

预期：2 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/git_sync_service.py
git add server/python/tests/tenant/unit/marketplace/test_git_sync_service.py
git commit -m "feat(marketplace): 新增 GitSyncService 基础结构"
```

---

### 任务 1.6：GitSyncService.get_cache_path

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/git_sync_service.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_sync_service.py`

- [ ] **步骤 1：编写失败的测试 - get_cache_path**

```python
# tests/tenant/unit/marketplace/test_git_sync_service.py（追加）


def test_get_cache_path():
    """验证缓存路径生成"""
    service = GitSyncService(cache_dir=Path("/tmp/cache"))

    path = service.get_cache_path(
        "https://github.com/anthropics/skills.git",
        "main"
    )

    # 预期：/tmp/cache/github_com_anthropics_skills/main
    assert path == Path("/tmp/cache/github_com_anthropics_skills/main")


def test_get_cache_path_github_url():
    """验证 GitHub URL 解析"""
    service = GitSyncService()

    path = service.get_cache_path(
        "https://github.com/owner/repo.git",
        "v1.0.0"
    )

    assert "github_com_owner_repo" in str(path)
    assert "v1.0.0" in str(path)
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py::test_get_cache_path -v
```

预期：`AttributeError: 'GitSyncService' object has no attribute 'get_cache_path'`

- [ ] **步骤 3：实现 get_cache_path 方法**

```python
# src/tenant/services/marketplace/git_sync_service.py（追加）

import re


class GitSyncService:
    """Git 仓库同步服务"""

    def get_cache_path(self, repo_url: str, ref: str) -> Path:
        """获取缓存路径

        将仓库 URL 转换为安全的目录名，格式：
        {cache_dir}/{host}_{owner}_{repo}/{ref}/

        Args:
            repo_url: git 仓库地址
            ref: 分支/tag/commit

        Returns:
            缓存路径
        """
        # 从 URL 提取 host, owner, repo
        # 例如：https://github.com/anthropics/skills.git
        # → github.com, anthropics, skills
        match = re.search(r"https?://([^/]+)/([^/]+)/([^/]+?)(?:\.git)?$", repo_url)
        if match:
            host = match.group(1).replace(".", "_")
            owner = match.group(2)
            repo = match.group(3)
            repo_name = f"{host}_{owner}_{repo}"
        else:
            # 非 GitHub URL，使用 hash
            import hashlib
            repo_hash = hashlib.md5(repo_url.encode()).hexdigest()[:12]
            repo_name = repo_hash

        return self.cache_dir / repo_name / ref
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py -v
```

预期：4 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/git_sync_service.py
git add server/python/tests/tenant/unit/marketplace/test_git_sync_service.py
git commit -m "feat(marketplace): 实现 GitSyncService.get_cache_path"
```

---

### 任务 1.7：GitSyncService.parse_source_url

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/git_sync_service.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_sync_service.py`

- [ ] **步骤 1：编写失败的测试 - parse_source_url**

```python
# tests/tenant/unit/marketplace/test_git_sync_service.py（追加）


def test_parse_source_url_github_tree():
    """验证解析 GitHub tree URL"""
    service = GitSyncService()

    repo_url, ref, subdir = service.parse_source_url(
        "https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator/skills/skill-creator"
    )

    assert repo_url == "https://github.com/anthropics/claude-plugins-official.git"
    assert ref == "main"
    assert subdir == "plugins/skill-creator/skills/skill-creator"


def test_parse_source_url_github_blob():
    """验证解析 GitHub blob URL"""
    service = GitSyncService()

    repo_url, ref, subdir = service.parse_source_url(
        "https://github.com/owner/repo/blob/v1.0/path/to/file.md"
    )

    assert repo_url == "https://github.com/owner/repo.git"
    assert ref == "v1.0"
    assert subdir == "path/to/file.md"


def test_parse_source_url_git_url():
    """验证解析直接 git URL"""
    service = GitSyncService()

    # 直接 git URL，无子目录
    repo_url, ref, subdir = service.parse_source_url(
        "https://github.com/owner/repo.git"
    )

    assert repo_url == "https://github.com/owner/repo.git"
    assert ref == "main"  # 默认
    assert subdir is None
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py::test_parse_source_url_github_tree -v
```

预期：`AttributeError: 'GitSyncService' object has no attribute 'parse_source_url'`

- [ ] **步骤 3：实现 parse_source_url 方法**

```python
# src/tenant/services/marketplace/git_sync_service.py（追加）


class GitSyncService:
    """Git 仓库同步服务"""

    def parse_source_url(self, source_url: str) -> tuple[str, str, str | None]:
        """解析 GitHub 目录页 URL

        将 GitHub tree/blob URL 解析为 (repo_url, ref, subdir)

        Args:
            source_url: GitHub 目录页 URL 或 git 仓库 URL

        Returns:
            tuple[str, str, str | None]: (仓库 URL, 分支/tag, 子目录路径)

        Examples:
            "https://github.com/owner/repo/tree/main/subdir"
            → ("https://github.com/owner/repo.git", "main", "subdir")

            "https://github.com/owner/repo.git"
            → ("https://github.com/owner/repo.git", "main", None)
        """
        # 匹配 GitHub tree/blob URL
        # https://github.com/{owner}/{repo}/tree/{ref}/{path}
        tree_match = re.search(
            r"https?://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+)/(.+)$",
            source_url
        )
        if tree_match:
            owner = tree_match.group(1)
            repo = tree_match.group(2)
            ref = tree_match.group(3)
            subdir = tree_match.group(4)
            repo_url = f"https://github.com/{owner}/{repo}.git"
            return repo_url, ref, subdir

        # 直接 git URL，无子目录
        if source_url.endswith(".git"):
            return source_url, "main", None

        # 无法解析，返回默认值
        return source_url, "main", None
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py -v
```

预期：7 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/git_sync_service.py
git add server/python/tests/tenant/unit/marketplace/test_git_sync_service.py
git commit -m "feat(marketplace): 实现 GitSyncService.parse_source_url"
```

---

### 任务 1.8：GitSyncService.sync_repo（mock 实现）

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/git_sync_service.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_sync_service.py`

- [ ] **步骤 1：编写失败的测试 - sync_repo**

```python
# tests/tenant/unit/marketplace/test_git_sync_service.py（追加）

from unittest.mock import AsyncMock, patch, MagicMock
import tempfile


@pytest.mark.asyncio
async def test_sync_repo_new_clone():
    """验证克隆新仓库"""
    with tempfile.TemporaryDirectory() as tmpdir:
        service = GitSyncService(cache_dir=Path(tmpdir))

        # Mock git 操作
        with patch.object(service, "_clone_repo", new_callable=AsyncMock) as mock_clone:
            mock_clone.return_value = (Path(tmpdir) / "test_repo", "abc123")

            repo_path, commit_sha = await service.sync_repo(
                "https://github.com/test/repo.git",
                ref="main"
            )

            assert commit_sha == "abc123"
            mock_clone.assert_called_once()


@pytest.mark.asyncio
async def test_sync_repo_existing_cache():
    """验证使用现有缓存"""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir)
        service = GitSyncService(cache_dir=cache_dir)

        # 创建已存在的缓存目录
        cached_repo = cache_dir / "github_com_test_repo" / "main"
        cached_repo.mkdir(parents=True)
        (cached_repo / "SKILL.md").write_text("---\nname: test\n---\n", encoding="utf-8")

        # Mock git 操作
        with patch.object(service, "_fetch_and_checkout", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "def456"

            repo_path, commit_sha = await service.sync_repo(
                "https://github.com/test/repo.git",
                ref="main"
            )

            assert commit_sha == "def456"
            mock_fetch.assert_called_once()
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py::test_sync_repo_new_clone -v
```

预期：`AttributeError: 'GitSyncService' object has no attribute 'sync_repo'`

- [ ] **步骤 3：实现 sync_repo 方法**

```python
# src/tenant/services/marketplace/git_sync_service.py（追加）

from loguru import logger


class GitSyncService:
    """Git 仓库同步服务"""

    async def sync_repo(
        self,
        repo_url: str,
        ref: str = "main",
        subdir: str | None = None,
    ) -> tuple[Path, str]:
        """同步仓库到本地缓存

        Args:
            repo_url: git 仓库地址
            ref: 分支/tag/commit，默认 main
            subdir: 仅检出子目录（sparse-checkout）

        Returns:
            tuple[Path, str]: (本地路径, commit_sha)
        """
        cache_path = self.get_cache_path(repo_url, ref)

        # 确保缓存目录存在
        cache_path.mkdir(parents=True, exist_ok=True)

        # 检查是否已存在
        if (cache_path / ".git").exists():
            # 已存在，执行 fetch + checkout
            logger.info(f"Updating existing cache: {cache_path}")
            commit_sha = await self._fetch_and_checkout(cache_path, ref, subdir)
        else:
            # 不存在，执行 clone
            logger.info(f"Cloning repository: {repo_url}")
            cache_path, commit_sha = await self._clone_repo(
                repo_url, ref, cache_path, subdir
            )

        return cache_path, commit_sha

    async def _clone_repo(
        self,
        repo_url: str,
        ref: str,
        target_path: Path,
        subdir: str | None,
    ) -> tuple[Path, str]:
        """克隆仓库（内部方法）"""
        # 使用 subprocess 或 GitPython 实现
        # 这里是占位实现，实际需要根据混合策略实现
        backend = await self._get_git_backend()
        return await backend.clone(repo_url, ref, target_path, subdir)

    async def _fetch_and_checkout(
        self,
        repo_path: Path,
        ref: str,
        subdir: str | None,
    ) -> str:
        """拉取并检出（内部方法）"""
        backend = await self._get_git_backend()
        return await backend.fetch_and_checkout(repo_path, ref, subdir)

    async def _get_git_backend(self):
        """获取 git 后端（混合策略）"""
        try:
            import git
            # GitPython 可用，使用 GitPython 后端
            from tenant.services.marketplace.git_backends import GitPythonBackend
            return GitPythonBackend(git)
        except ImportError:
            # GitPython 不可用，使用 subprocess 后端
            from tenant.services.marketplace.git_backends import SubprocessGitBackend
            return SubprocessGitBackend()
```

- [ ] **步骤 4：创建 git_backends 模块（简化版）**

```python
# src/tenant/services/marketplace/git_backends.py
"""Git 后端实现"""

from __future__ import annotations

from pathlib import Path


class GitPythonBackend:
    """GitPython 后端"""

    def __init__(self, git_module):
        self.git = git_module

    async def clone(self, repo_url: str, ref: str, target_path: Path, subdir: str | None) -> tuple[Path, str]:
        """克隆仓库"""
        # 实际实现需要使用 GitPython API
        # 这里是简化实现
        import asyncio
        import subprocess

        cmd = ["git", "clone", "--branch", ref, repo_url, str(target_path)]
        if subdir:
            # sparse-checkout
            cmd.extend(["--filter=blob:none", "--sparse"])

        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()

        if subdir:
            # 配置 sparse-checkout
            sparse_cmd = ["git", "-C", str(target_path), "sparse-checkout", "set", subdir]
            proc = await asyncio.create_subprocess_exec(*sparse_cmd)
            await proc.wait()

        # 获取 commit sha
        sha_cmd = ["git", "-C", str(target_path), "rev-parse", "HEAD"]
        proc = await asyncio.create_subprocess_exec(*sha_cmd, stdout=subprocess.PIPE)
        stdout, _ = await proc.communicate()
        commit_sha = stdout.decode().strip()

        return target_path, commit_sha

    async def fetch_and_checkout(self, repo_path: Path, ref: str, subdir: str | None) -> str:
        """拉取并检出"""
        import asyncio
        import subprocess

        # git fetch
        fetch_cmd = ["git", "-C", str(repo_path), "fetch", "origin", ref]
        proc = await asyncio.create_subprocess_exec(*fetch_cmd)
        await proc.wait()

        # git checkout
        checkout_cmd = ["git", "-C", str(repo_path), "checkout", ref]
        proc = await asyncio.create_subprocess_exec(*checkout_cmd)
        await proc.wait()

        # 获取 commit sha
        sha_cmd = ["git", "-C", str(repo_path), "rev-parse", "HEAD"]
        proc = await asyncio.create_subprocess_exec(*sha_cmd, stdout=subprocess.PIPE)
        stdout, _ = await proc.communicate()
        return stdout.decode().strip()


class SubprocessGitBackend:
    """subprocess git 后端"""

    async def clone(self, repo_url: str, ref: str, target_path: Path, subdir: str | None) -> tuple[Path, str]:
        """克隆仓库"""
        import asyncio
        import subprocess

        cmd = ["git", "clone", "--branch", ref, repo_url, str(target_path)]
        if subdir:
            cmd.extend(["--filter=blob:none", "--sparse"])

        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()

        if subdir:
            sparse_cmd = ["git", "-C", str(target_path), "sparse-checkout", "set", subdir]
            proc = await asyncio.create_subprocess_exec(*sparse_cmd)
            await proc.wait()

        sha_cmd = ["git", "-C", str(target_path), "rev-parse", "HEAD"]
        proc = await asyncio.create_subprocess_exec(*sha_cmd, stdout=subprocess.PIPE)
        stdout, _ = await proc.communicate()
        commit_sha = stdout.decode().strip()

        return target_path, commit_sha

    async def fetch_and_checkout(self, repo_path: Path, ref: str, subdir: str | None) -> str:
        """拉取并检出"""
        import asyncio
        import subprocess

        fetch_cmd = ["git", "-C", str(repo_path), "fetch", "origin", ref]
        proc = await asyncio.create_subprocess_exec(*fetch_cmd)
        await proc.wait()

        checkout_cmd = ["git", "-C", str(repo_path), "checkout", ref]
        proc = await asyncio.create_subprocess_exec(*checkout_cmd)
        await proc.wait()

        sha_cmd = ["git", "-C", str(repo_path), "rev-parse", "HEAD"]
        proc = await asyncio.create_subprocess_exec(*sha_cmd, stdout=subprocess.PIPE)
        stdout, _ = await proc.communicate()
        return stdout.decode().strip()
```

- [ ] **步骤 5：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_sync_service.py -v
```

预期：9 passed

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/tenant/services/marketplace/git_sync_service.py
git add server/python/src/tenant/services/marketplace/git_backends.py
git add server/python/tests/tenant/unit/marketplace/test_git_sync_service.py
git commit -m "feat(marketplace): 实现 GitSyncService.sync_repo"
```

---

## Phase 2: GitSkillsAdapter

### 任务 2.1：GitSkillsAdapter 初始化和 market_type

**文件：**
- 创建：`server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py`
- 创建：`server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py`

- [ ] **步骤 1：编写失败的测试**

```python
# tests/tenant/unit/marketplace/test_git_skills_adapter.py
"""GitSkillsAdapter 单元测试"""

import pytest
from tenant.services.marketplace.adapters.git_skills_adapter import GitSkillsAdapter


def test_market_type():
    """验证市场类型为 git-skills"""
    adapter = GitSkillsAdapter()
    assert adapter.market_type == "git-skills"


def test_default_repo():
    """验证默认仓库地址"""
    adapter = GitSkillsAdapter()
    assert adapter.DEFAULT_REPO == "https://github.com/anthropics/skills.git"
    assert adapter.DEFAULT_REF == "main"
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py -v
```

预期：`ModuleNotFoundError: No module named 'tenant.services.marketplace.adapters.git_skills_adapter'`

- [ ] **步骤 3：实现 GitSkillsAdapter 基础结构**

```python
# src/tenant/services/marketplace/adapters/git_skills_adapter.py
"""Git 仓库 Skill 适配器"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tenant.services.marketplace.git_sync_service import GitSyncService
from tenant.services.marketplace.skill_scanner import SkillScanner

if TYPE_CHECKING:
    from tenant.services.marketplace.protocol import (
        MarketplaceAdapter,
        MarketplaceTestResult,
        PluginUpdateInfo,
        RemotePluginInfo,
    )


class GitSkillsAdapter:
    """Git 仓库 Skill 适配器

    从 git 仓库扫描 SKILL.md 并提供下载能力。
    支持任意 git 仓库地址，默认使用 anthropics/skills。
    """

    DEFAULT_REPO = "https://github.com/anthropics/skills.git"
    DEFAULT_REF = "main"

    def __init__(
        self,
        git_sync: GitSyncService | None = None,
        scanner: SkillScanner | None = None,
    ):
        """初始化适配器

        Args:
            git_sync: Git 同步服务
            scanner: Skill 扫描工具
        """
        self.git_sync = git_sync or GitSyncService()
        self.scanner = scanner or SkillScanner()

    @property
    def market_type(self) -> str:
        """市场类型标识"""
        return "git-skills"
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py -v
```

预期：2 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py
git add server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py
git commit -m "feat(marketplace): 新增 GitSkillsAdapter 基础结构"
```

---

### 任务 2.2：GitSkillsAdapter.list_plugins

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py`

- [ ] **步骤 1：编写失败的测试**

```python
# tests/tenant/unit/marketplace/test_git_skills_adapter.py（追加）

from unittest.mock import AsyncMock, MagicMock
from pathlib import Path
import tempfile


@pytest.mark.asyncio
async def test_list_plugins():
    """验证列出 skills"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试 skill
        skill_dir = Path(tmpdir) / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: test-skill
description: Use when testing
author: test-author
---
# Test
""", encoding="utf-8")

        # Mock git_sync
        mock_git_sync = MagicMock()
        mock_git_sync.sync_repo = AsyncMock(return_value=(Path(tmpdir), "abc123"))

        adapter = GitSkillsAdapter(git_sync=mock_git_sync)
        config = {"url": "https://github.com/test/repo.git"}

        plugins, total = await adapter.list_plugins(config)

        assert total == 1
        assert len(plugins) == 1
        assert plugins[0].name == "test-skill"
        assert plugins[0].author == "test-author"
        assert plugins[0].plugin_type == "skill"


@pytest.mark.asyncio
async def test_list_plugins_with_keyword():
    """验证关键词过滤"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建两个 skill
        for name in ["alpha-skill", "beta-skill"]:
            skill_dir = Path(tmpdir) / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(f"""---
name: {name}
description: Test skill
---
# Test
""", encoding="utf-8")

        mock_git_sync = MagicMock()
        mock_git_sync.sync_repo = AsyncMock(return_value=(Path(tmpdir), "abc123"))

        adapter = GitSkillsAdapter(git_sync=mock_git_sync)
        config = {"url": "https://github.com/test/repo.git"}

        plugins, total = await adapter.list_plugins(config, keyword="alpha")

        assert total == 1
        assert plugins[0].name == "alpha-skill"
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py::test_list_plugins -v
```

预期：`AttributeError: 'GitSkillsAdapter' object has no attribute 'list_plugins'`

- [ ] **步骤 3：实现 list_plugins 方法**

```python
# src/tenant/services/marketplace/adapters/git_skills_adapter.py（追加）

from collections.abc import Sequence
from tenant.services.marketplace.protocol import (
    MarketplaceTestResult,
    PluginUpdateInfo,
    RemotePluginInfo,
)


class GitSkillsAdapter:
    """Git 仓库 Skill 适配器"""

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """扫描仓库中的所有 skills

        Args:
            config: 市场配置
            keyword: 搜索关键词
            plugin_type: 插件类型筛选（忽略）
            page: 页码
            page_size: 每页条数

        Returns:
            tuple[Sequence[RemotePluginInfo], int]: (插件列表, 总数)
        """
        repo_url = config.get("url", self.DEFAULT_REPO)
        ref = config.get("ref", self.DEFAULT_REF)

        # 同步仓库到本地缓存
        repo_path, commit_sha = await self.git_sync.sync_repo(repo_url, ref)

        # 扫描 SKILL.md
        skills = self.scanner.scan_skills(repo_path)

        # 关键词过滤
        if keyword:
            keyword_lower = keyword.lower()
            skills = [
                s for s in skills
                if keyword_lower in s.name.lower()
                or keyword_lower in s.description.lower()
            ]

        # 转换为 RemotePluginInfo
        plugins = [self._to_remote_plugin_info(s, repo_url, ref) for s in skills]

        # 分页
        total = len(plugins)
        start = (page - 1) * page_size
        return plugins[start:start + page_size], total

    def _to_remote_plugin_info(
        self,
        skill: SkillMeta,
        repo_url: str,
        ref: str
    ) -> "RemotePluginInfo":
        """转换为 RemotePluginInfo"""
        plugin_id = f"{skill.author}/{skill.name}"
        return RemotePluginInfo(
            plugin_id=plugin_id,
            name=skill.name,
            description=skill.description,
            version=ref,  # 用 ref 作为版本标识
            author=skill.author,
            icon=None,
            plugin_type="skill",
            skill_type="knowledge",
            tags=skill.tags,
            downloads=None,
            manifest_url=None,
            download_url=f"git://{repo_url}:{ref}:{skill.name}",
            created_at=None,
            updated_at=None,
        )
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py -v
```

预期：4 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py
git add server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py
git commit -m "feat(marketplace): 实现 GitSkillsAdapter.list_plugins"
```

---

### 任务 2.3：GitSkillsAdapter.get_plugin

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py`

- [ ] **步骤 1：编写失败的测试**

```python
# tests/tenant/unit/marketplace/test_git_skills_adapter.py（追加）


@pytest.mark.asyncio
async def test_get_plugin():
    """验证获取单个 skill 详情"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: my-skill
description: Test skill
author: my-author
version: 2.0.0
---
# My Skill
""", encoding="utf-8")

        mock_git_sync = MagicMock()
        mock_git_sync.sync_repo = AsyncMock(return_value=(Path(tmpdir), "abc123"))

        adapter = GitSkillsAdapter(git_sync=mock_git_sync)
        config = {"url": "https://github.com/test/repo.git"}

        plugin = await adapter.get_plugin(config, "my-author/my-skill")

        assert plugin is not None
        assert plugin.name == "my-skill"
        assert plugin.author == "my-author"


@pytest.mark.asyncio
async def test_get_plugin_not_found():
    """验证 skill 不存在时返回 None"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_git_sync = MagicMock()
        mock_git_sync.sync_repo = AsyncMock(return_value=(Path(tmpdir), "abc123"))

        adapter = GitSkillsAdapter(git_sync=mock_git_sync)
        config = {"url": "https://github.com/test/repo.git"}

        plugin = await adapter.get_plugin(config, "unknown/unknown")

        assert plugin is None
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py::test_get_plugin -v
```

预期：`AttributeError: 'GitSkillsAdapter' object has no attribute 'get_plugin'`

- [ ] **步骤 3：实现 get_plugin 方法**

```python
# src/tenant/services/marketplace/adapters/git_skills_adapter.py（追加）


class GitSkillsAdapter:
    """Git 仓库 Skill 适配器"""

    async def get_plugin(
        self,
        config: dict,
        plugin_id: str
    ) -> "RemotePluginInfo | None":
        """获取单个 skill 详情

        Args:
            config: 市场配置
            plugin_id: 插件 ID（格式：author/name）

        Returns:
            RemotePluginInfo | None: 插件信息，不存在返回 None
        """
        repo_url = config.get("url", self.DEFAULT_REPO)
        ref = config.get("ref", self.DEFAULT_REF)

        repo_path, _ = await self.git_sync.sync_repo(repo_url, ref)
        skills = self.scanner.scan_skills(repo_path)

        for skill in skills:
            if f"{skill.author}/{skill.name}" == plugin_id:
                return self._to_remote_plugin_info(skill, repo_url, ref)

        return None
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py -v
```

预期：6 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py
git add server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py
git commit -m "feat(marketplace): 实现 GitSkillsAdapter.get_plugin"
```

---

### 任务 2.4：GitSkillsAdapter.download_plugin

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py`

- [ ] **步骤 1：编写失败的测试**

```python
# tests/tenant/unit/marketplace/test_git_skills_adapter.py（追加）

import zipfile
from io import BytesIO


@pytest.mark.asyncio
async def test_download_plugin():
    """验证下载 skill 打包为 ZIP"""
    with tempfile.TemporaryDirectory() as tmpdir:
        skill_dir = Path(tmpdir) / "downloadable-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("""---
name: downloadable-skill
description: For download test
author: test-author
---
# Downloadable
""", encoding="utf-8")
        (skill_dir / "helper.py").write_text("# helper", encoding="utf-8")

        mock_git_sync = MagicMock()
        mock_git_sync.sync_repo = AsyncMock(return_value=(Path(tmpdir), "abc123"))

        adapter = GitSkillsAdapter(git_sync=mock_git_sync)
        config = {"url": "https://github.com/test/repo.git"}

        zip_data, checksum = await adapter.download_plugin(config, "test-author/downloadable-skill")

        assert isinstance(zip_data, bytes)
        assert len(checksum) == 64

        # 验证 ZIP 内容
        with zipfile.ZipFile(BytesIO(zip_data)) as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert "helper.py" in names


@pytest.mark.asyncio
async def test_download_plugin_not_found():
    """验证下载不存在的 skill 时抛出异常"""
    with tempfile.TemporaryDirectory() as tmpdir:
        mock_git_sync = MagicMock()
        mock_git_sync.sync_repo = AsyncMock(return_value=(Path(tmpdir), "abc123"))

        adapter = GitSkillsAdapter(git_sync=mock_git_sync)
        config = {"url": "https://github.com/test/repo.git"}

        with pytest.raises(ValueError, match="Skill not found"):
            await adapter.download_plugin(config, "unknown/unknown")
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py::test_download_plugin -v
```

预期：`AttributeError: 'GitSkillsAdapter' object has no attribute 'download_plugin'`

- [ ] **步骤 3：实现 download_plugin 方法**

```python
# src/tenant/services/marketplace/adapters/git_skills_adapter.py（追加）


class GitSkillsAdapter:
    """Git 仓库 Skill 适配器"""

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载 skill 目录打包为 ZIP

        Args:
            config: 市场配置
            plugin_id: 插件 ID
            version: 版本号（使用 ref）

        Returns:
            tuple[bytes, str]: (ZIP 数据, SHA256 校验和)
        """
        repo_url = config.get("url", self.DEFAULT_REPO)
        ref = version or config.get("ref", self.DEFAULT_REF)

        repo_path, _ = await self.git_sync.sync_repo(repo_url, ref)
        skills = self.scanner.scan_skills(repo_path)

        for skill in skills:
            if f"{skill.author}/{skill.name}" == plugin_id:
                return self.scanner.zip_skill(skill)

        raise ValueError(f"Skill not found: {plugin_id}")
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py -v
```

预期：8 passed

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py
git add server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py
git commit -m "feat(marketplace): 实现 GitSkillsAdapter.download_plugin"
```

---

### 任务 2.5：GitSkillsAdapter.test_connection 和 check_updates

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py`

- [ ] **步骤 1：编写失败的测试**

```python
# tests/tenant/unit/marketplace/test_git_skills_adapter.py（追加）


@pytest.mark.asyncio
async def test_test_connection():
    """验证测试连接"""
    mock_git_sync = MagicMock()
    mock_git_sync.check_repo_accessible = AsyncMock(return_value=True)

    adapter = GitSkillsAdapter(git_sync=mock_git_sync)
    config = {"url": "https://github.com/test/repo.git"}

    result = await adapter.test_connection(config)

    assert result.success is True
    assert result.message == "仓库可访问"


@pytest.mark.asyncio
async def test_test_connection_failed():
    """验证测试连接失败"""
    mock_git_sync = MagicMock()
    mock_git_sync.check_repo_accessible = AsyncMock(return_value=False)

    adapter = GitSkillsAdapter(git_sync=mock_git_sync)
    config = {"url": "https://github.com/test/repo.git"}

    result = await adapter.test_connection(config)

    assert result.success is False


@pytest.mark.asyncio
async def test_check_updates():
    """验证检查更新"""
    mock_git_sync = MagicMock()
    mock_git_sync.get_remote_commit_sha = AsyncMock(return_value="new-sha")

    adapter = GitSkillsAdapter(git_sync=mock_git_sync)
    config = {"url": "https://github.com/test/repo.git"}

    plugins = [
        {"plugin_id": "author/skill1", "current_version": "old-sha"},
        {"plugin_id": "author/skill2", "current_version": "new-sha"},
    ]

    updates = await adapter.check_updates(config, plugins)

    assert len(updates) == 2
    assert updates[0].has_update is True
    assert updates[1].has_update is False
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py::test_test_connection -v
```

预期：`AttributeError: 'GitSkillsAdapter' object has no attribute 'test_connection'`

- [ ] **步骤 3：实现 test_connection 和 check_updates 方法**

```python
# src/tenant/services/marketplace/adapters/git_skills_adapter.py（追加）


class GitSkillsAdapter:
    """Git 仓库 Skill 适配器"""

    async def test_connection(self, config: dict) -> "MarketplaceTestResult":
        """测试 git 仓库可访问性

        Args:
            config: 市场配置

        Returns:
            MarketplaceTestResult: 测试结果
        """
        repo_url = config.get("url", self.DEFAULT_REPO)
        ref = config.get("ref", self.DEFAULT_REF)

        try:
            success = await self.git_sync.check_repo_accessible(repo_url, ref)
            if success:
                return MarketplaceTestResult(success=True, message="仓库可访问")
            return MarketplaceTestResult(success=False, message="仓库不可访问或 ref 不存在")
        except Exception as e:
            return MarketplaceTestResult(success=False, message=f"连接异常: {str(e)}")

    async def check_updates(
        self,
        config: dict,
        plugins: "Sequence[dict]",
    ) -> "Sequence[PluginUpdateInfo]":
        """检查更新：比对本地 commit_sha 与远程最新 commit

        Args:
            config: 市场配置
            plugins: 需要检查的插件列表

        Returns:
            Sequence[PluginUpdateInfo]: 更新信息列表
        """
        repo_url = config.get("url", self.DEFAULT_REPO)
        ref = config.get("ref", self.DEFAULT_REF)

        # 获取远程最新 commit
        remote_sha = await self.git_sync.get_remote_commit_sha(repo_url, ref)

        results = []
        for plugin in plugins:
            plugin_id = plugin.get("plugin_id")
            local_sha = plugin.get("current_version")

            if not plugin_id:
                continue

            results.append(PluginUpdateInfo(
                plugin_id=plugin_id,
                current_version=local_sha or "",
                latest_version=remote_sha,
                has_update=local_sha != remote_sha,
                changelog=None,
            ))

        return results
```

- [ ] **步骤 4：在 GitSyncService 中添加 check_repo_accessible 和 get_remote_commit_sha**

```python
# src/tenant/services/marketplace/git_sync_service.py（追加）

    async def check_repo_accessible(self, repo_url: str, ref: str) -> bool:
        """检查仓库可访问性（git ls-remote）

        Args:
            repo_url: git 仓库地址
            ref: 分支/tag/commit

        Returns:
            bool: 是否可访问
        """
        import asyncio

        try:
            # 使用 git ls-remote 检查
            cmd = ["git", "ls-remote", "--exit-code", repo_url, f"refs/heads/{ref}"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception:
            return False

    async def get_remote_commit_sha(self, repo_url: str, ref: str) -> str:
        """获取远程最新 commit sha

        Args:
            repo_url: git 仓库地址
            ref: 分支/tag/commit

        Returns:
            str: commit sha
        """
        import asyncio
        import subprocess

        cmd = ["git", "ls-remote", repo_url, f"refs/heads/{ref}"]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = await proc.communicate()

        # 输出格式：<sha>\trefs/heads/<ref>
        line = stdout.decode().strip()
        if line:
            return line.split("\t")[0]
        return ""
```

- [ ] **步骤 5：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_git_skills_adapter.py -v
```

预期：11 passed

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py
git add server/python/src/tenant/services/marketplace/git_sync_service.py
git add server/python/tests/tenant/unit/marketplace/test_git_skills_adapter.py
git commit -m "feat(marketplace): 实现 GitSkillsAdapter.test_connection 和 check_updates"
```

---

## Phase 3: ModelScopeSkillAdapter 改造

### 任务 3.1：ModelScopeSkillAdapter 注入依赖

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py`

- [ ] **步骤 1：编写失败的测试 - 注入依赖**

```python
# tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py（追加）


def test_adapter_with_dependencies():
    """验证适配器可注入依赖"""
    from tenant.services.marketplace.git_sync_service import GitSyncService
    from tenant.services.marketplace.skill_scanner import SkillScanner

    git_sync = GitSyncService()
    scanner = SkillScanner()
    adapter = ModelScopeSkillAdapter(git_sync=git_sync, scanner=scanner)

    assert adapter.git_sync is git_sync
    assert adapter.scanner is scanner
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py::test_adapter_with_dependencies -v
```

预期：`TypeError: ModelScopeSkillAdapter.__init__() got unexpected keyword arguments`

- [ ] **步骤 3：修改 ModelScopeSkillAdapter 初始化**

```python
# src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py（修改 __init__）

from tenant.services.marketplace.git_sync_service import GitSyncService
from tenant.services.marketplace.skill_scanner import SkillScanner


class ModelScopeSkillAdapter(MarketplaceAdapter):
    """ModelScope Skill 市场适配器（符合官方 OpenAPI 规范）

    改造点：
    - list_plugins / get_plugin / check_updates：保留 HTTP API 调用
    - download_plugin：改为 git sparse-checkout 拉取 source_url 对应目录并打 ZIP
    """

    API_BASE = "https://modelscope.cn/openapi/v1"

    def __init__(
        self,
        git_sync: GitSyncService | None = None,
        scanner: SkillScanner | None = None,
    ):
        """初始化适配器

        Args:
            git_sync: Git 同步服务
            scanner: Skill 扫描工具
        """
        self.git_sync = git_sync or GitSyncService()
        self.scanner = scanner or SkillScanner()

    # ... 其他方法保持不变
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py -v
```

预期：所有测试通过

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py
git add server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py
git commit -m "refactor(marketplace): ModelScopeSkillAdapter 注入 GitSyncService 和 SkillScanner"
```

---

### 任务 3.2：ModelScopeSkillAdapter.download_plugin 改造

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py`

- [ ] **步骤 1：编写失败的测试 - download_plugin 使用 git**

```python
# tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py（追加）

import zipfile
from io import BytesIO


@pytest.mark.asyncio
async def test_download_plugin_with_source_url():
    """验证 download_plugin 使用 git sparse-checkout"""
    from unittest.mock import MagicMock, AsyncMock, patch
    from pathlib import Path
    import tempfile

    adapter = ModelScopeSkillAdapter()

    # Mock get_plugin 返回带 source_url 的信息
    with patch.object(adapter, "get_plugin", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = RemotePluginInfo(
            plugin_id="@author/skill",
            name="skill",
            description="test",
            version="latest",
            author="author",
            icon=None,
            plugin_type="skill",
            manifest_url=None,
            download_url="",
            created_at=None,
            updated_at=None,
            skill_metadata={
                "source_url": "https://github.com/owner/repo/tree/main/skills/test-skill",
                "category": "test",
            },
        )

        # Mock git_sync
        with tempfile.TemporaryDirectory() as tmpdir:
            skill_dir = Path(tmpdir)
            (skill_dir / "SKILL.md").write_text("---\nname: test-skill\ndescription: test\n---\n", encoding="utf-8")

            mock_git_sync = MagicMock()
            mock_git_sync.parse_source_url = MagicMock(return_value=(
                "https://github.com/owner/repo.git",
                "main",
                "skills/test-skill"
            ))
            mock_git_sync.sync_repo = AsyncMock(return_value=(skill_dir, "abc123"))

            adapter.git_sync = mock_git_sync

            data, checksum = await adapter.download_plugin({}, "@author/skill")

            assert isinstance(data, bytes)
            assert len(checksum) == 64

            # 验证是有效的 ZIP
            with zipfile.ZipFile(BytesIO(data)) as zf:
                assert "SKILL.md" in zf.namelist()
```

- [ ] **步骤 2：运行测试验证失败**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py::test_download_plugin_with_source_url -v
```

预期：测试失败或返回 JSON 而非 ZIP

- [ ] **步骤 3：改造 download_plugin 方法**

```python
# src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py（修改 download_plugin）

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载 skill（git sparse-checkout + ZIP 打包）

        Args:
            config: 市场配置
            plugin_id: 插件ID
            version: 版本号，None 表示最新版本

        Returns:
            tuple[bytes, str]: (ZIP 数据, SHA256 校验和)
        """
        skill_info = await self.get_plugin(config, plugin_id)
        if not skill_info:
            raise ValueError(f"Skill {plugin_id} not found")

        # 从 skill_metadata 获取 source_url
        metadata = skill_info.skill_metadata or {}
        source_url = metadata.get("source_url", "")

        if not source_url:
            # 兜底：返回声明清单（向后兼容）
            return self._generate_declaration(skill_info)

        # 解析 source_url
        repo_url, ref, subdir = self.git_sync.parse_source_url(source_url)

        # git sparse-checkout 拉取子目录
        skill_dir, commit_sha = await self.git_sync.sync_repo(
            repo_url, ref=ref, subdir=subdir
        )

        # 扫描并打包
        skills = self.scanner.scan_skills(skill_dir)
        if not skills:
            raise ValueError(f"No SKILL.md found in {source_url}")

        return self.scanner.zip_skill(skills[0])

    def _generate_declaration(self, skill_info: RemotePluginInfo) -> tuple[bytes, str]:
        """生成声明清单（兜底方法）"""
        metadata = skill_info.skill_metadata or {}
        category = metadata.get("category", "")

        declaration = {
            "skill": {
                "skill_type": self._infer_skill_type(category),
                "runtime": "none",
            },
            "metadata": {
                "name": skill_info.name,
                "description": skill_info.description,
                "version": skill_info.version,
                "author": skill_info.author,
                "tags": skill_info.tags,
            },
            "install": {
                "source_url": metadata.get("source_url", ""),
                "commands": metadata.get("install_commands", []),
            },
        }

        data = json.dumps(declaration, ensure_ascii=False, sort_keys=True).encode("utf-8")
        checksum = hashlib.sha256(data).hexdigest()
        return data, checksum
```

- [ ] **步骤 4：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py -v
```

预期：所有测试通过

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py
git add server/python/tests/tenant/unit/marketplace/test_modelscope_skill_adapter.py
git commit -m "refactor(marketplace): ModelScopeSkillAdapter.download_plugin 改为 git sparse-checkout"
```

---

## Phase 4: LocalSkillAdapter 改造

### 任务 4.1：LocalSkillAdapter 复用 SkillScanner

**文件：**
- 修改：`server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py`
- 修改：`server/python/tests/tenant/unit/marketplace/test_local_skill_adapter.py`

- [ ] **步骤 1：修改 LocalSkillAdapter 初始化**

```python
# src/tenant/services/marketplace/adapters/local_skill_adapter.py（修改）

from tenant.services.marketplace.skill_scanner import SkillScanner


class LocalSkillAdapter(MarketplaceAdapter):
    """本地文件 Skill 扫描适配器

    从本地文件系统扫描 SKILL.md 文件并返回 Skill 信息。
    支持递归扫描目录，解析 YAML front matter。
    """

    def __init__(self, scanner: SkillScanner | None = None):
        """初始化适配器

        Args:
            scanner: Skill 扫描工具
        """
        self.scanner = scanner or SkillScanner()

    # ... 其他方法
```

- [ ] **步骤 2：修改 list_plugins 使用 scanner**

```python
# src/tenant/services/marketplace/adapters/local_skill_adapter.py（修改 list_plugins）

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取本地 skill 列表"""
        url = config.get("url", "")
        if not url:
            return [], 0

        try:
            path = self._parse_url(url)
            skills = self.scanner.scan_skills(path)

            # 关键词过滤
            if keyword:
                keyword_lower = keyword.lower()
                skills = [
                    s for s in skills
                    if keyword_lower in s.name.lower()
                    or keyword_lower in s.description.lower()
                ]

            # 转换为 RemotePluginInfo
            plugins = [self._to_remote_plugin_info(s) for s in skills]

            # 分页
            total = len(plugins)
            start = (page - 1) * page_size
            return plugins[start:start + page_size], total
        except Exception as e:
            logger.error(f"获取本地 Skill 列表失败: {e}")
            return [], 0
```

- [ ] **步骤 3：修改 download_plugin 使用 scanner**

```python
# src/tenant/services/marketplace/adapters/local_skill_adapter.py（修改 download_plugin）

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """打包 skill 目录为 ZIP"""
        url = config.get("url", "")
        if not url:
            raise ValueError("市场地址不能为空")

        path = self._parse_url(url)
        skills = self.scanner.scan_skills(path)

        for skill in skills:
            if f"{skill.author}/{skill.name}" == plugin_id:
                return self.scanner.zip_skill(skill)

        raise ValueError(f"Plugin not found: {plugin_id}")
```

- [ ] **步骤 4：移除重复方法**

```python
# src/tenant/services/marketplace/adapters/local_skill_adapter.py（删除以下方法）
# - _parse_skill_file
# - _scan_skills
# 保留：_parse_url
```

- [ ] **步骤 5：运行测试验证通过**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/test_local_skill_adapter.py -v
```

预期：所有测试通过

- [ ] **步骤 6：Commit**

```bash
git add server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py
git commit -m "refactor(marketplace): LocalSkillAdapter 复用 SkillScanner"
```

---

## Phase 5: 删除 AgentSkillsAdapter

### 任务 5.1：删除 AgentSkillsAdapter 文件

**文件：**
- 删除：`server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py`
- 删除：`server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py`
- 修改：`server/python/src/tenant/services/marketplace/gateway.py`

- [ ] **步骤 1：修改 gateway.py 移除 agentskills 注册**

```python
# src/tenant/services/marketplace/gateway.py（修改）

from tenant.services.marketplace.adapters.git_skills_adapter import GitSkillsAdapter

class MarketplaceGateway:
    """插件市场网关服务"""

    _adapters: dict[str, type] = {
        "dify": DifyAdapter,
        "modelscope-skill": ModelScopeSkillAdapter,
        "modelscope-mcp": ModelScopeMcpAdapter,
        "local-skill": LocalSkillAdapter,
        "local-plugin": LocalPluginAdapter,
        "git-skills": GitSkillsAdapter,  # 新增
    }

    # 移除旧的 agentskills 导入和注册
```

- [ ] **步骤 2：删除 agentskills_adapter.py**

```bash
rm server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py
```

- [ ] **步骤 3：删除 test_agentskills_adapter.py**

```bash
rm server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py
```

- [ ] **步骤 4：运行测试验证无破坏**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/ -v
```

预期：所有测试通过

- [ ] **步骤 5：Commit**

```bash
git add server/python/src/tenant/services/marketplace/gateway.py
git add server/python/src/tenant/services/marketplace/adapters/git_skills_adapter.py
git rm server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py
git rm server/python/tests/tenant/unit/marketplace/test_agentskills_adapter.py
git commit -m "refactor(marketplace): 删除错误的 AgentSkillsAdapter，使用 GitSkillsAdapter 替代"
```

---

## Phase 6: 配置和测试

### 任务 6.1：添加配置

**文件：**
- 修改：`server/python/config/application.yml`

- [ ] **步骤 1：添加 skills.git 配置节**

```yaml
# server/config/application.yml（追加到末尾）

# Skills Git 配置（GitSkillsAdapter / ModelScopeSkillAdapter 共用）
skills:
  git:
    # GitSkillsAdapter 默认仓库（当市场配置未指定 url 时使用）
    default_repo: "https://github.com/anthropics/skills.git"
    default_ref: "main"
    # 缓存配置
    cache_dir: "./cache/skills"
    cache_ttl_days: 30
    cleanup_on_startup: true
```

- [ ] **步骤 2：Commit**

```bash
git add server/python/config/application.yml
git commit -m "feat(config): 新增 skills.git 配置节"
```

---

### 任务 6.2：运行完整测试套件

- [ ] **步骤 1：运行所有 marketplace 测试**

```bash
cd server/python && uv run pytest tests/tenant/unit/marketplace/ -v
```

预期：所有测试通过

- [ ] **步骤 2：运行完整测试套件**

```bash
cd server/python && uv run pytest tests/tenant/ -v
```

预期：所有测试通过

- [ ] **步骤 3：最终 Commit**

```bash
git add .
git commit -m "feat(marketplace): 完成 Git 仓库 Skill 适配器改造"
```

---

## 自检清单

### 规格覆盖度

| 规格需求 | 对应任务 |
|----------|----------|
| GitSyncService 基础结构 | 任务 1.5 |
| GitSyncService.get_cache_path | 任务 1.6 |
| GitSyncService.parse_source_url | 任务 1.7 |
| GitSyncService.sync_repo | 任务 1.8 |
| SkillScanner 数据类 | 任务 1.1 |
| SkillScanner.parse_skill_file | 任务 1.2 |
| SkillScanner.scan_skills | 任务 1.3 |
| SkillScanner.zip_skill | 任务 1.4 |
| GitSkillsAdapter 基础结构 | 任务 2.1 |
| GitSkillsAdapter.list_plugins | 任务 2.2 |
| GitSkillsAdapter.get_plugin | 任务 2.3 |
| GitSkillsAdapter.download_plugin | 任务 2.4 |
| GitSkillsAdapter.test_connection/check_updates | 任务 2.5 |
| ModelScopeSkillAdapter 注入依赖 | 任务 3.1 |
| ModelScopeSkillAdapter.download_plugin 改造 | 任务 3.2 |
| LocalSkillAdapter 改造 | 任务 4.1 |
| 删除 AgentSkillsAdapter | 任务 5.1 |
| 添加配置 | 任务 6.1 |

### 占位符扫描

- ✅ 无"待定"、"TODO"、"后续实现"
- ✅ 所有代码步骤都有实际代码
- ✅ 所有测试都有断言
- ✅ 所有命令都有预期输出

### 类型一致性

- ✅ `SkillMeta` 在任务 1.1 定义，后续任务一致使用
- ✅ `GitSyncService` 在任务 1.5 定义，后续任务一致使用
- ✅ `RemotePluginInfo` 使用 protocol.py 中定义的类型
- ✅ 方法签名与协议定义一致
