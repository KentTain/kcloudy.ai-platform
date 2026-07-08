# Git 仓库 Skill 适配器设计

**日期**：2026-07-08
**状态**：设计中
**范围**：AgentSkillsAdapter 和 ModelScopeSkillAdapter 改造

## 背景

### 问题

1. **AgentSkillsAdapter 实现错误**：假设存在 `agentskills.io` HTTP API，但该站点是 Skill 规范站点，不提供 HTTP 服务
2. **ModelScopeSkillAdapter 语义错位**：`download_plugin` 返回 JSON 声明清单，与 `upload_skill_package` 的 ZIP 包语义不匹配

### 目标

- 新增 `GitSkillsAdapter`：从 git 仓库扫描 SKILL.md 并提供下载能力
- 改造 `ModelScopeSkillAdapter`：保留 HTTP API，`download_plugin` 改为 git sparse-checkout 拉取子目录并打 ZIP
- 改造 `LocalSkillAdapter`：复用共享逻辑，移除重复代码

## 架构设计

### 整体架构

```
server/python/src/tenant/services/
├── marketplace/
│   ├── adapters/
│   │   ├── git_skills_adapter.py      # 新增
│   │   ├── modelscope_skill_adapter.py # 改造
│   │   ├── local_skill_adapter.py      # 改造
│   │   └── agentskills_adapter.py      # 删除
│   ├── git_sync_service.py            # 新增
│   ├── skill_scanner.py               # 新增
│   └── gateway.py                     # 改造：注册 GitSkillsAdapter，移除 agentskills
└── ...

tests/tenant/unit/marketplace/
├── test_git_skills_adapter.py         # 新增
└── test_agentskills_adapter.py        # 删除
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `GitSyncService` | git clone/fetch/sparse-checkout + 缓存管理 |
| `SkillScanner` | 扫描目录中的 SKILL.md + 解析 YAML frontmatter |
| `GitSkillsAdapter` | 实现 MarketplaceAdapter 协议，调用 GitSyncService + SkillScanner |
| `ModelScopeSkillAdapter` | 保留 HTTP API，download_plugin 调用 GitSyncService |
| `LocalSkillAdapter` | 复用 SkillScanner，移除重复逻辑 |

### 依赖方向

```
GitSkillsAdapter ──→ GitSyncService
                  ──→ SkillScanner

ModelScopeSkillAdapter ──→ GitSyncService（仅 download_plugin）

LocalSkillAdapter ──→ SkillScanner
```

## GitSyncService 设计

```python
class GitSyncService:
    """Git 仓库同步服务"""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path("./cache/skills")
        self._git_backend: GitPython | SubprocessGit  # 混合方案

    async def sync_repo(
        self,
        repo_url: str,
        ref: str = "main",
        subdir: str | None = None,
    ) -> tuple[Path, str]:
        """
        同步仓库到本地缓存

        Args:
            repo_url: git 仓库地址
            ref: 分支/tag/commit，默认 main
            subdir: 仅检出子目录（sparse-checkout）

        Returns:
            (本地路径, commit_sha)
        """

    async def sparse_checkout(
        self,
        repo_path: Path,
        subdir: str,
        ref: str,
    ) -> Path:
        """仅检出指定子目录"""

    def parse_source_url(self, source_url: str) -> tuple[str, str, str]:
        """
        解析 GitHub 目录页 URL

        Examples:
            "https://github.com/owner/repo/tree/main/subdir"
            → ("https://github.com/owner/repo.git", "main", "subdir")
        """

    def get_cache_path(self, repo_url: str, ref: str) -> Path:
        """获取缓存路径：{cache_dir}/{repo_hash}/{ref}/"""

    async def cleanup_expired(self, ttl_days: int = 30) -> int:
        """清理过期缓存，返回清理数量"""

    async def check_repo_accessible(self, repo_url: str, ref: str) -> bool:
        """检查仓库可访问性（git ls-remote）"""

    async def get_remote_commit_sha(self, repo_url: str, ref: str) -> str:
        """获取远程最新 commit sha"""
```

### 缓存目录结构

```
./cache/skills/
├── github_com_anthropics_skills/          # {host}_{owner}_{repo}
│   ├── main/                               # ref
│   │   └── ...                             # 完整仓库
│   └── v1.0.0/
│       └── ...
└── github_com_anthropics_claude-plugins-official/
    └── main/
        └── plugins/skill-creator/skills/skill-creator/  # sparse-checkout
```

### 混合实现策略

优先使用 GitPython，失败时 fallback 到 subprocess 调用系统 git。

```python
async def _get_git_backend(self):
    try:
        import git
        return GitPythonBackend(git)
    except ImportError:
        return SubprocessGitBackend()
```

## SkillScanner 设计

```python
@dataclass
class SkillMeta:
    """Skill 元数据"""
    name: str                    # 必需：skill 名称
    description: str             # 必需：描述
    version: str = "1.0.0"       # 版本
    author: str = "unknown"      # 作者
    tags: list[str] = field(default_factory=list)
    skill_dir: Path = None       # 扫描时填充：skill 目录路径

class SkillScanner:
    """Skill 扫描工具"""

    def scan_skills(self, base_dir: Path) -> list[SkillMeta]:
        """
        递归扫描目录中的所有 SKILL.md

        Args:
            base_dir: 扫描根目录

        Returns:
            SkillMeta 列表
        """

    def parse_skill_file(self, skill_file: Path) -> SkillMeta:
        """
        解析单个 SKILL.md 文件

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

    def zip_skill(self, skill: SkillMeta) -> tuple[bytes, str]:
        """
        将 skill 目录打包为 ZIP

        Returns:
            (zip_bytes, sha256_checksum)
        """
```

### 验证规则

- `name` 必需，只允许字母、数字、连字符
- `description` 必需，最多 500 字符（agentskills.io 规范建议）
- frontmatter 总计最多 1024 字符

## GitSkillsAdapter 设计

```python
class GitSkillsAdapter(MarketplaceAdapter):
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
        self.git_sync = git_sync or GitSyncService()
        self.scanner = scanner or SkillScanner()

    @property
    def market_type(self) -> str:
        return "git-skills"

    async def test_connection(self, config: dict) -> MarketplaceTestResult:
        """测试 git 仓库可访问性（git ls-remote）"""

    async def list_plugins(
        self,
        config: dict,
        keyword: str | None = None,
        plugin_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """扫描仓库中的所有 skills"""

    async def get_plugin(self, config: dict, plugin_id: str) -> RemotePluginInfo | None:
        """获取单个 skill 详情"""

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载 skill 目录打包为 ZIP"""

    async def check_updates(
        self,
        config: dict,
        plugins: Sequence[dict],
    ) -> Sequence[PluginUpdateInfo]:
        """检查更新：比对本地 commit_sha 与远程最新 commit"""
```

### 配置示例

```yaml
# 市场配置（通过 API/UI 创建）
type: git-skills
url: https://github.com/anthropics/skills.git  # 可选，有默认值
ref: main                                       # 可选，默认 main
```

### 关键设计点

1. `version` 字段复用 `ref`（分支/tag/commit），`check_updates` 比对 commit_sha
2. `plugin_id` 格式：`{author}/{name}`，与 LocalSkillAdapter 保持一致
3. 注入 `GitSyncService` 和 `SkillScanner`，便于单元测试 mock

## ModelScopeSkillAdapter 改造设计

```python
class ModelScopeSkillAdapter(MarketplaceAdapter):
    """ModelScope Skill 市场适配器

    改造点：
    - list_plugins / get_plugin / check_updates：保留 HTTP API 调用
    - download_plugin：改为 git sparse-checkout 拉取 source_url 对应目录并打 ZIP
    """

    def __init__(
        self,
        git_sync: GitSyncService | None = None,
        scanner: SkillScanner | None = None,
    ):
        self.git_sync = git_sync or GitSyncService()
        self.scanner = scanner or SkillScanner()

    async def download_plugin(
        self,
        config: dict,
        plugin_id: str,
        version: str | None = None,
    ) -> tuple[bytes, str]:
        """
        改造：git sparse-checkout 拉取 source_url 对应目录

        流程：
        1. 调用 get_plugin 获取 skill 元数据
        2. 从 skill_metadata.source_url 解析 (repo_url, ref, subdir)
        3. 调用 GitSyncService.sparse_checkout 拉取子目录
        4. 调用 SkillScanner.zip_skill 打包
        """
```

### source_url 解析示例

```
输入: https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator/skills/skill-creator

parse_source_url 输出:
  repo_url = "https://github.com/anthropics/claude-plugins-official.git"
  ref = "main"
  subdir = "plugins/skill-creator/skills/skill-creator"
```

### 兜底策略

- `source_url` 为空时，返回 JSON 声明清单（保持向后兼容）
- 支持非 GitHub 的 git 仓库（直接传 git URL）

## LocalSkillAdapter 改造设计

```python
class LocalSkillAdapter(MarketplaceAdapter):
    """本地文件 Skill 扫描适配器

    改造点：
    - 复用 SkillScanner，移除重复的 _parse_skill_file / _scan_skills 逻辑
    - download_plugin 调用 SkillScanner.zip_skill
    """

    def __init__(self, scanner: SkillScanner | None = None):
        self.scanner = scanner or SkillScanner()

    # 移除：_parse_skill_file, _scan_skills（由 SkillScanner 提供）
    # 保留：_parse_url, _make_plugin_id, _to_remote_plugin_info
```

### 改造收益

- 移除约 80 行重复代码
- 统一 skill 解析逻辑，便于维护
- 与 GitSkillsAdapter 行为一致

## gateway.py 改造

```python
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
```

### 删除旧代码

| 文件 | 操作 |
|------|------|
| `adapters/agentskills_adapter.py` | 删除 |
| `tests/tenant/unit/marketplace/test_agentskills_adapter.py` | 删除 |
| `gateway.py` 中的 `"agentskills"` 注册 | 移除 |

**说明**：
- `AgentSkillsAdapter` 基于 `agentskills.io` HTTP API 的错误假设实现
- 使用 `GitSkillsAdapter` 完全替代，市场类型从 `agentskills` 改为 `git-skills`

## 配置设计

### application.yml 新增配置

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

### 配置说明

| 配置项 | 用途 | 使用者 |
|--------|------|--------|
| `skills.git.default_repo` | GitSkillsAdapter 默认仓库地址 | `GitSkillsAdapter` |
| `skills.git.default_ref` | 默认分支/tag | `GitSkillsAdapter` |
| `skills.git.cache_dir` | git 仓库缓存目录 | `GitSyncService` |
| `skills.git.cache_ttl_days` | 缓存过期天数 | `GitSyncService` |
| `skills.git.cleanup_on_startup` | 启动时清理过期缓存 | `GitSyncService` |

## 依赖变更

### 新增依赖（可选）

```toml
# pyproject.toml
[project.optional-dependencies]
git = ["GitPython>=3.1.0"]
```

- GitPython 为可选依赖，未安装时自动 fallback 到 subprocess
- 不影响核心功能，仅影响 git 操作的可靠性

## 测试策略

### 单元测试

- `GitSyncService`：mock git 操作，测试缓存路径生成、source_url 解析
- `SkillScanner`：测试 SKILL.md 解析、ZIP 打包
- `GitSkillsAdapter`：mock GitSyncService 和 SkillScanner，测试协议实现
- `ModelScopeSkillAdapter`：mock HTTP API 和 git 操作，测试 download_plugin 改造

### 集成测试

- 端到端测试：创建 git-skills 市场 → 列表 → 详情 → 下载 → 验证 ZIP 内容
- 缓存测试：验证缓存命中、过期清理

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| git 仓库访问失败 | list_plugins/download_plugin 失败 | test_connection 提前验证；错误信息友好提示 |
| source_url 解析失败 | ModelScopeSkillAdapter download_plugin 失败 | 兜底返回 JSON 声明清单；记录日志 |
| 缓存目录过大 | 磁盘空间不足 | TTL 自动清理；手动 API 清理 |
| GitPython 兼容性问题 | git 操作失败 | fallback 到 subprocess；记录日志 |

## 实现优先级

1. **Phase 1**：GitSyncService + SkillScanner（基础设施）
2. **Phase 2**：GitSkillsAdapter（新增适配器）
3. **Phase 3**：ModelScopeSkillAdapter 改造
4. **Phase 4**：LocalSkillAdapter 改造
5. **Phase 5**：删除 AgentSkillsAdapter 及测试文件
6. **Phase 6**：配置 + 测试
