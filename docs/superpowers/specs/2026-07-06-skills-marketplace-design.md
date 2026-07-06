# Skills 市场功能设计规格

## 1. 概述

### 1.1 背景

当前 Tenant 模块已具备成熟的插件市场架构，支持 Dify、ModelScope 等市场类型，涵盖插件的定义、安装、运行时管理全流程。现有 Plugin 体系属于"重量级运行时"（虚拟环境 + 独立进程 + 沙箱隔离），适合承载复杂的代码逻辑。

后续需要集成 hermes-agent（D:\Project\ai\marketplace\hermes-agent）的对话方式及 Skills 能力。Hermes 的 Skill 体系采用"轻量级知识文档"理念，通过 Markdown + Prompt Engineering 指导 Agent 调用外部 API，兼容 agentskills.io 开放标准。

需要开发一个独立的 Skills 市场，集成国内外不同来源（local 文件、API、Git）的 Skill 资源，将 Skills 存储在 MinIO，通过 LangChain 进行调用。

### 1.2 Hermes Skill 与现有 Plugin 的本质差异

| 维度 | Hermes Skill | 本项目现有 Plugin |
|------|--------------|-------------------|
| **本质** | 知识文档（Prompt Engineering） | 代码运行时（完整程序） |
| **内容** | Markdown 文件（操作指南 + curl 命令） | Python/JS 代码包 + 虚拟环境 |
| **能力** | API 调用指导、工作流模板 | 完整业务逻辑、数据处理、模型推理 |
| **执行环境** | Agent 主进程内 | 独立 Python 进程 |
| **隔离性** | 无隔离 | 沙箱隔离 |
| **技术栈** | Terminal + curl | Python/JS + 任意依赖 |
| **生命周期** | 即时加载/卸载 | 需要启动/停止进程 |

### 1.3 目标

- Skills 作为 Plugin 的子类型（`plugin_type='skill'`），统一管理
- 同时支持知识文档（knowledge）和简单脚本（script）两种技术边界
- 一步到位实现：市场浏览 + 安装 + 调用 + 前端集成 + LangChain 调用
- 复用现有 Plugin 市场架构（适配器、存储、安装流程）
- 集成国内外 Skills 市场：AgentSkills、ModelScope Skill、本地文件扫描

### 1.4 范围

| 包含 | 不包含 |
|------|--------|
| Skill 作为 Plugin 子类型 | 重写现有 Plugin 架构 |
| 知识文档运行时（零隔离） | 完整代码运行时（复用现有） |
| 简单脚本运行时（轻量级沙箱） | Docker 容器隔离 |
| AgentSkills 市场适配器 | HuggingFace 等其他市场 |
| ModelScope Skill 适配器 | 实时同步 |
| 本地文件扫描适配器 | 多版本共存管理 |
| LangChain Prompt 集成 | 自定义输出解析器框架 |
| 前端 Skill 市场浏览页 | 前端 Skill 编辑器 |
| 前端 Skill 调用面板 | Skill 调试器 |
| MinIO 存储集成 | 向量检索 |
| 完整测试覆盖（单元/集成/E2E） | 性能基准测试 |

---

## 2. 整体架构

### 2.1 模块定位与依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                      Tenant Module                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Plugin Definition (全局插件注册表)                 │  │
│  │  ├─ tool/model/agent 插件定义                      │  │
│  │  └─ skill 插件定义 (新增)                          │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Plugin Installation (租户安装记录)                 │  │
│  │  ├─ tool/model/agent 安装记录                      │  │
│  │  └─ skill 安装记录 (新增)                          │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Plugin Marketplace (市场配置 + 适配器)            │  │
│  │  ├─ Dify Adapter                                   │  │
│  │  ├─ ModelScope Adapter                             │  │
│  │  ├─ AgentSkills Adapter (新增)                     │  │
│  │  └─ ModelScope Skill Adapter (新增)                │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Provider 协议
                          ▼
┌─────────────────────────────────────────────────────────┐
│                        AI Module                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  Plugin Runtime (运行时管理)                        │  │
│  │  ├─ LocalPluginRuntime (重度隔离，现有)            │  │
│  │  ├─ KnowledgeSkillRuntime (零隔离，新增)           │  │
│  │  └─ SandboxSkillRuntime (轻量级沙箱，新增)         │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  LangChain Integration (技能调用，新增)            │  │
│  │  ├─ PromptTemplate Loader                          │  │
│  │  ├─ Skill Chain Builder                            │  │
│  │  └─ Skill Context Manager                          │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 2.2 关键设计决策

- **Skill 存储在 Tenant 模块**：复用现有 `plugin_definitions` 和 `plugin_installations` 表
- **Skill 运行时在 AI 模块**：新增轻量级运行时实现
- **市场适配器扩展**：新增 AgentSkills、ModelScope Skill、本地文件扫描适配器
- **LangChain 集成在 AI 模块**：负责知识文档渲染和脚本执行

### 2.3 三层运行时体系

| 运行时 | 适用类型 | 隔离级别 | 典型场景 |
|--------|---------|---------|---------|
| LocalPluginRuntime | tool/model/agent | 重度隔离（虚拟环境 + 进程） | LLM 推理、复杂工具 |
| KnowledgeSkillRuntime | skill/knowledge | 零隔离 | API 调用指导、工作流模板 |
| SandboxSkillRuntime | skill/script | 轻量级沙箱 | 数据处理脚本、简单工具 |

---

## 3. 数据模型设计

### 3.1 Plugin Definition 扩展

扩展现有 `tenant.plugin_definitions` 表，无需新建表：

```python
# server/python/src/tenant/models/plugin_definition.py

class TenantPluginDefinition(BaseModel, ActiveRecordMixin):
    """插件定义模型 - 扩展支持 Skill"""

    # 现有字段保持不变
    plugin_id: Mapped[str]
    plugin_type: Mapped[str]  # tool, model, agent, skill (新增)

    # 新增 Skill 特有字段（plugin_type='skill' 时必填）
    skill_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="Skill 类型：knowledge(知识文档) | script(简单脚本)",
    )
    runtime_type: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="运行时类型：none | sandbox | local",
    )
```

### 3.2 Skill 配置结构

存储在 `declaration` JSON 字段中：

```yaml
# declaration 字段内容（plugin_type='skill'）
skill:
  skill_type: knowledge  # knowledge | script
  runtime: none          # none | sandbox

  # 知识文档配置
  knowledge:
    documents:
      - SKILL.md
    examples:
      - examples/create_record.md
    langchain:
      prompt_template: "{user_request}"
      input_variables:
        - user_request

  # 脚本配置（skill_type=script 时）
  script:
    entrypoint: main.py
    dependencies:
      - requests>=2.28.0
    allowed_imports:
      - requests
      - json
    timeout: 30
    memory_limit_mb: 128
```

### 3.3 Plugin Marketplace 扩展

扩展现有 `tenant.plugin_marketplaces` 表的 `type` 字段：

| 市场类型 | 说明 | 认证方式 |
|---------|------|---------|
| dify | Dify 插件市场（现有） | api_key |
| modelscope | ModelScope 插件市场（现有） | api_key |
| agentskills | AgentSkills 市场（新增） | none |
| modelscope-skill | ModelScope Skill 市场（新增） | api_key |
| local-skill | 本地文件扫描（新增） | none |

### 3.4 数据库迁移

```python
# server/python/src/tenant/migrations/versions/xxx_add_skill_support.py

def upgrade() -> None:
    # 扩展 plugin_definitions 表
    op.add_column(
        "plugin_definitions",
        sa.Column("skill_type", sa.String(16), nullable=True,
                  comment="Skill 类型：knowledge|script"),
    )
    op.add_column(
        "plugin_definitions",
        sa.Column("runtime_type", sa.String(16), nullable=True,
                  comment="运行时类型：none|sandbox|local"),
    )

    # 添加索引（仅对 skill 类型查询优化）
    op.execute("""
        CREATE INDEX idx_plugin_definitions_skill_type
        ON tenant.plugin_definitions (plugin_type, skill_type)
        WHERE plugin_type = 'skill';
    """)

def downgrade() -> None:
    op.drop_index("idx_plugin_definitions_skill_type", table_name="plugin_definitions")
    op.drop_column("plugin_definitions", "runtime_type")
    op.drop_column("plugin_definitions", "skill_type")
```

---

## 4. 市场适配器设计

### 4.1 适配器协议扩展

扩展 `RemotePluginInfo` 以支持 Skill 特有字段：

```python
# server/python/src/tenant/services/marketplace/protocol.py

@dataclass
class RemotePluginInfo:
    """远程插件信息 - 扩展支持 Skill"""

    # 现有字段
    plugin_id: str
    name: str
    description: str | None
    version: str
    author: str
    plugin_type: str  # tool, model, agent, skill (新增)

    # 新增 Skill 特有字段
    skill_type: str | None = None  # knowledge | script
    skill_metadata: dict | None = None

    # 现有字段保持不变
    tags: list[str] = field(default_factory=list)
    icon: str | None = None
    downloads: int | None = None
    manifest_url: str | None = None
    download_url: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### 4.2 AgentSkills 适配器

兼容 https://agentskills.io 开放标准：

```python
# server/python/src/tenant/services/marketplace/adapters/agentskills_adapter.py

class AgentSkillsAdapter(MarketplaceAdapter):
    """AgentSkills 市场适配器"""

    @property
    def market_type(self) -> str:
        return "agentskills"

    async def list_plugins(
        self, config: dict, keyword: str | None = None,
        plugin_type: str | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取 Skill 列表

        AgentSkills API 格式：
        GET /api/v1/skills?keyword=xxx&page=1&size=20
        """
        url = f"{config['url']}/api/v1/skills"
        params = {"keyword": keyword, "page": page, "size": page_size}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()

            skills = [
                RemotePluginInfo(
                    plugin_id=skill["identifier"],
                    name=skill["name"],
                    description=skill["description"],
                    version=skill["version"],
                    author=skill["author"],
                    plugin_type="skill",
                    skill_type="knowledge",  # AgentSkills 默认为知识文档
                    tags=skill.get("tags", []),
                    download_url=skill["download_url"],
                )
                for skill in data["skills"]
            ]
            return skills, data["total"]

    async def download_plugin(
        self, config: dict, plugin_id: str, version: str | None = None,
    ) -> tuple[bytes, str]:
        """下载 Skill 包，返回 (数据, SHA256 校验和)"""
        url = f"{config['url']}/api/v1/skills/{plugin_id}/download"
        if version:
            url += f"?version={version}"

        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            checksum = hashlib.sha256(response.content).hexdigest()
            return response.content, checksum
```

### 4.3 ModelScope Skill 适配器

兼容 https://modelscope.cn/skills API：

```python
# server/python/src/tenant/services/marketplace/adapters/modelscope_skill_adapter.py

class ModelScopeSkillAdapter(MarketplaceAdapter):
    """ModelScope Skills 市场适配器"""

    @property
    def market_type(self) -> str:
        return "modelscope-skill"

    async def list_plugins(
        self, config: dict, keyword: str | None = None,
        plugin_type: str | None = None, page: int = 1, page_size: int = 20,
    ) -> tuple[Sequence[RemotePluginInfo], int]:
        """获取 ModelScope Skill 列表"""
        url = f"{config['url']}/api/v1/skills"
        params = {"Keyword": keyword, "PageNumber": page, "PageSize": page_size}

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()

            skills = [
                RemotePluginInfo(
                    plugin_id=skill["Id"],
                    name=skill["Name"],
                    description=skill["Description"],
                    version=skill["Version"],
                    author=skill["Owner"],
                    plugin_type="skill",
                    skill_type=self._parse_skill_type(skill),
                    tags=skill.get("Tags", []),
                    downloads=skill.get("Downloads"),
                    icon=skill.get("Logo"),
                    download_url=skill["DownloadUrl"],
                )
                for skill in data["Data"]["Skills"]
            ]
            return skills, data["Data"]["TotalCount"]

    def _parse_skill_type(self, skill_data: dict) -> str:
        """解析 Skill 类型"""
        if skill_data.get("HasScript"):
            return "script"
        return "knowledge"
```

### 4.4 本地文件扫描适配器

支持从本地目录扫描 Skill 文件：

```python
# server/python/src/tenant/services/marketplace/adapters/local_skill_adapter.py

class LocalSkillAdapter(MarketplaceAdapter):
    """本地 Skill 扫描适配器"""

    @property
    def market_type(self) -> str:
        return "local-skill"

    async def scan_skills(
        self, config: dict, scan_path: str,
    ) -> Sequence[RemotePluginInfo]:
        """扫描本地目录中的 Skill

        支持格式：
        1. 单个 SKILL.md 文件
        2. 包含 SKILL.md 的目录
        3. ZIP 压缩包
        """
        skills = []
        scan_dir = Path(scan_path)

        for item in scan_dir.rglob("SKILL.md"):
            skill_info = await self._parse_skill_file(item)
            skills.append(skill_info)

        return skills

    async def _parse_skill_file(self, skill_file: Path) -> RemotePluginInfo:
        """解析 SKILL.md 文件（YAML front matter 格式）"""
        content = skill_file.read_text(encoding="utf-8")

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1])
                return RemotePluginInfo(
                    plugin_id=f"{metadata.get('author', 'local')}/{metadata['name']}",
                    name=metadata["name"],
                    description=metadata.get("description", ""),
                    version=metadata.get("version", "1.0.0"),
                    author=metadata.get("author", "local"),
                    plugin_type="skill",
                    skill_type="knowledge",
                    tags=metadata.get("metadata", {}).get("hermes", {}).get("tags", []),
                    download_url=f"file://{skill_file.parent}",
                )

        raise ValueError(f"无效的 Skill 文件格式: {skill_file}")
```

### 4.5 Gateway 服务扩展

```python
# server/python/src/tenant/services/marketplace/gateway.py

class MarketplaceGateway:
    """市场网关服务"""

    _adapters = {
        "dify": DifyAdapter,
        "modelscope": ModelScopeAdapter,
        "agentskills": AgentSkillsAdapter,           # 新增
        "modelscope-skill": ModelScopeSkillAdapter,  # 新增
        "local-skill": LocalSkillAdapter,            # 新增
    }

    async def sync_skill_from_marketplace(
        self, session: AsyncSession, marketplace_id: str, skill_id: str,
    ) -> TenantPluginDefinition:
        """从市场同步单个 Skill"""
        marketplace = await self.get_marketplace(session, marketplace_id)
        adapter = self._get_adapter(marketplace.type)
        config = self._build_adapter_config(marketplace)

        # 获取 Skill 元数据
        skill_info = await adapter.get_plugin(config, skill_id)

        # 下载 Skill 包
        skill_data, checksum = await adapter.download_plugin(
            config, skill_id, version=skill_info.version
        )

        # 上传到 MinIO
        storage_key = await plugin_storage_service.upload_skill_package(
            skill_id, skill_data, checksum
        )

        # 创建插件定义
        definition = TenantPluginDefinition(
            plugin_id=skill_info.plugin_id,
            plugin_type="skill",
            skill_type=skill_info.skill_type,
            plugin_unique_identifier=f"{skill_info.plugin_id}@{skill_info.version}",
            name=skill_info.name,
            description=skill_info.description,
            version=skill_info.version,
            author=skill_info.author,
            icon=skill_info.icon,
            tags=skill_info.tags,
            storage_key=storage_key,
            declaration={
                "skill": {
                    "skill_type": skill_info.skill_type,
                    "runtime": "none" if skill_info.skill_type == "knowledge" else "sandbox",
                }
            },
        )

        session.add(definition)
        await session.flush()
        return definition
```

---

## 5. 运行时实现设计

### 5.1 运行时工厂扩展

```python
# server/python/src/ai/components/plugin/engine/core/runtime/factory.py

class RuntimeFactory:
    """运行时工厂 - 扩展支持 Skill"""

    def create_runtime(
        self, plugin_info: PluginInfo, workspace_dir: Path | None = None,
    ) -> PluginRuntime:
        """创建运行时实例"""

        # Skill 类型路由
        if plugin_info.type == PluginType.SKILL:
            return self._create_skill_runtime(plugin_info)

        # 现有逻辑：tool/model/agent
        runtime_type = self._get_runtime_type(plugin_info)
        if runtime_type == RuntimeType.LOCAL:
            return LocalPluginRuntime(plugin_info, workspace_dir)
        elif runtime_type == RuntimeType.REMOTE:
            return RemotePluginRuntime(plugin_info)
        elif runtime_type == RuntimeType.CONTAINER:
            return ContainerPluginRuntime(plugin_info)

        raise ValueError(f"不支持的运行时类型: {runtime_type}")

    def _create_skill_runtime(self, plugin_info: PluginInfo) -> PluginRuntime:
        """创建 Skill 运行时"""
        skill_config = plugin_info.declaration.get("skill", {})
        skill_type = skill_config.get("skill_type", "knowledge")

        if skill_type == "knowledge":
            return KnowledgeSkillRuntime(plugin_info)  # 零隔离
        elif skill_type == "script":
            return SandboxSkillRuntime(plugin_info)    # 轻量级沙箱
        else:
            raise ValueError(f"不支持的 Skill 类型: {skill_type}")
```

### 5.2 KnowledgeSkillRuntime 实现

知识文档运行时 - 零隔离，通过 LangChain 加载：

```python
# server/python/src/ai/components/plugin/engine/core/runtime/knowledge_skill_runtime.py

class KnowledgeSkillRuntime(PluginRuntime):
    """知识文档运行时

    特点：
    - 零隔离，无需进程
    - 通过 LangChain PromptTemplate 加载
    - 由 LLM 理解并执行
    """

    def __init__(self, plugin_info: PluginInfo):
        super().__init__(plugin_info)
        self.skill_type = "knowledge"
        self.runtime_type = "none"

        # LangChain 组件
        self.llm: ChatOpenAI | None = None
        self.skill_documents: dict[str, str] = {}
        self.prompt_template: PromptTemplate | None = None
        self.chain: Runnable | None = None
        self._is_loaded = False

    async def prepare(self) -> None:
        """准备阶段：加载 Skill 文档"""
        if self._is_loaded:
            return

        self._update_state(PluginRuntimeState.PREPARING)

        try:
            # 1. 从 MinIO 下载 Skill 包
            skill_data = await self._download_skill_package()

            # 2. 解析文件内容
            self.skill_documents = await self._parse_skill_documents(skill_data)

            # 3. 验证必要文件
            if "SKILL.md" not in self.skill_documents:
                raise SkillPreparationError(
                    self.plugin_info.plugin_id, "缺少 SKILL.md 文件"
                )

            # 4. 构建 LangChain Prompt
            self._build_prompt_chain()

            self._is_loaded = True
            self._update_state(PluginRuntimeState.PREPARED)

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            raise RuntimeError(f"Skill 准备失败: {e}")

    async def start(self) -> None:
        """启动阶段：初始化 LLM"""
        if self.is_running:
            return
        if not self._is_loaded:
            await self.prepare()

        self._update_state(PluginRuntimeState.STARTING)

        try:
            from ai.services.model_config_service import model_config_service
            model_config = await model_config_service.get_default_llm_config()
            self.llm = ChatOpenAI(
                model=model_config.model_name,
                openai_api_key=model_config.api_key,
                openai_api_base=model_config.base_url,
                temperature=0.7,
            )
            self.chain = self.prompt_template | self.llm | StrOutputParser()
            self._update_state(PluginRuntimeState.RUNNING)

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            raise RuntimeError(f"Skill 启动失败: {e}")

    async def invoke_stream(
        self, invoke_request: dict[str, Any], timeout: int = 60,
        session_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """调用 Skill（流式返回）"""
        if not self.is_running or not self.chain:
            raise RuntimeError("Skill 未启动")

        try:
            async for chunk in self.chain.astream(invoke_request):
                yield {"type": "chunk", "content": chunk, "session_id": session_id}
            yield {"type": "complete", "session_id": session_id}
        except Exception as e:
            yield {"type": "error", "error": str(e), "session_id": session_id}

    def _build_prompt_chain(self) -> None:
        """构建 LangChain Prompt Chain"""
        skill_config = self.plugin_info.declaration.get("skill", {})
        knowledge_config = skill_config.get("knowledge", {})

        # 主文档内容
        main_doc = self.skill_documents["SKILL.md"]
        if main_doc.startswith("---"):
            parts = main_doc.split("---", 2)
            if len(parts) >= 3:
                main_doc = parts[2].strip()

        # 加载示例文档
        examples_content = ""
        for example_file in knowledge_config.get("examples", []):
            if example_file in self.skill_documents:
                examples_content += f"\n\n### 示例：{example_file}\n"
                examples_content += self.skill_documents[example_file]

        # 构建 Prompt Template
        template = """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

## 技能说明

{skill_document}

## 使用示例

{examples}

## 用户请求

{user_request}

请根据技能说明和示例，帮助用户完成任务。"""

        self.prompt_template = PromptTemplate(
            template=template,
            input_variables=["user_request"],
            partial_variables={
                "skill_document": main_doc,
                "examples": examples_content,
            },
        )

    async def _parse_skill_documents(self, skill_data: bytes) -> dict[str, str]:
        """解析 Skill 包中的文档"""
        import zipfile, io
        documents = {}

        try:
            with zipfile.ZipFile(io.BytesIO(skill_data)) as zf:
                for file_info in zf.filelist:
                    if file_info.filename.endswith(".md"):
                        documents[file_info.filename] = zf.read(file_info.filename).decode("utf-8")
        except zipfile.BadZipFile:
            documents["SKILL.md"] = skill_data.decode("utf-8")

        return documents
```

### 5.3 SandboxSkillRuntime 实现

简单脚本运行时 - 轻量级沙箱：

```python
# server/python/src/ai/components/plugin/engine/core/runtime/sandbox_skill_runtime.py

class SandboxSkillRuntime(PluginRuntime):
    """轻量级沙箱运行时

    特点：
    - RestrictedPython 沙箱
    - 白名单导入控制
    - 资源限制（内存、CPU、超时）
    - 单进程执行
    """

    def __init__(self, plugin_info: PluginInfo):
        super().__init__(plugin_info)
        self.skill_type = "script"
        self.runtime_type = "sandbox"

        self.timeout: int = 30
        self.memory_limit_mb: int = 128
        self.allowed_imports: set[str] = set()
        self.script_content: str = ""
        self.dependencies: list[str] = []
        self.temp_dir: Path | None = None
        self._is_prepared = False

    async def prepare(self) -> None:
        """准备阶段：下载脚本、安装依赖"""
        if self._is_prepared:
            return
        self._update_state(PluginRuntimeState.PREPARING)

        try:
            skill_config = self.plugin_info.declaration.get("skill", {})
            script_config = skill_config.get("script", {})

            self.timeout = script_config.get("timeout", 30)
            self.memory_limit_mb = script_config.get("memory_limit_mb", 128)
            self.allowed_imports = set(script_config.get("allowed_imports", []))
            self.dependencies = script_config.get("dependencies", [])

            script_data = await self._download_skill_package()
            self.script_content = self._extract_main_script(script_data)

            # 验证脚本安全性
            self._validate_script_security()

            self.temp_dir = Path(tempfile.mkdtemp(prefix=f"skill_{self.plugin_info.name}_"))

            if self.dependencies:
                await self._install_dependencies()

            self._is_prepared = True
            self._update_state(PluginRuntimeState.PREPARED)

        except Exception as e:
            self._update_state(PluginRuntimeState.ERROR)
            raise RuntimeError(f"Skill 准备失败: {e}")

    async def invoke_stream(
        self, invoke_request: dict[str, Any], timeout: int = 60,
        session_id: str | None = None,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """在沙箱中执行脚本"""
        if not self.is_running:
            raise RuntimeError("Skill 未启动")

        try:
            exec_globals = self._build_safe_globals()
            exec_locals = {
                "input_data": invoke_request.get("input", {}),
                "context": invoke_request.get("context", {}),
            }

            result = await self._execute_with_limits(
                self.script_content, exec_globals, exec_locals
            )

            yield {"type": "complete", "result": result, "session_id": session_id}
        except Exception as e:
            yield {"type": "error", "error": str(e), "session_id": session_id}

    def _validate_script_security(self) -> None:
        """验证脚本安全性"""
        try:
            compile_restricted(self.script_content, "<skill>", "exec")
        except SyntaxError as e:
            raise SkillSecurityError(self.plugin_info.plugin_id, [str(e)])

        forbidden_patterns = [
            "import os", "import subprocess", "import sys",
            "__import__", "eval(", "exec(", "compile(",
        ]
        violations = [p for p in forbidden_patterns if p in self.script_content]
        if violations:
            raise SkillSecurityError(self.plugin_info.plugin_id, violations)

    def _build_safe_globals(self) -> dict:
        """构建安全的全局命名空间"""
        safe_modules = {}
        for module_name in self.allowed_imports:
            try:
                safe_modules[module_name] = __import__(module_name)
            except ImportError:
                pass

        return {
            "__builtins__": {
                **safe_builtins,
                "print": print, "len": len, "str": str,
                "int": int, "float": float, "bool": bool,
                "list": list, "dict": dict, "range": range,
            },
            **safe_modules,
        }

    async def _execute_with_limits(
        self, script: str, exec_globals: dict, exec_locals: dict,
    ) -> Any:
        """在子进程中执行脚本（带资源限制）"""
        process = await asyncio.create_subprocess_exec(
            "python3", "-c", script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=self.temp_dir,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=self.timeout
            )

            if process.returncode != 0:
                raise RuntimeError(f"脚本执行失败: {stderr.decode()}")

            try:
                return json.loads(stdout.decode())
            except json.JSONDecodeError:
                return {"output": stdout.decode()}

        except asyncio.TimeoutError:
            process.kill()
            raise SkillTimeoutError(self.plugin_info.plugin_id, self.timeout)
```

### 5.4 运行时状态枚举扩展

```python
# server/python/src/ai/components/plugin/engine/models/enums.py

class PluginType(EnumBase):
    """插件类型枚举"""
    MODEL = "model"
    TOOL = "tool"
    AGENT = "agent"
    OAUTH = "oauth"
    ENDPOINT = "endpoint"
    SKILL = "skill"  # 新增：技能插件

class RuntimeType(EnumBase):
    """运行时类型枚举"""
    LOCAL = "local"
    REMOTE = "remote"
    CONTAINER = "container"
    SANDBOX = "sandbox"  # 新增：轻量级沙箱
    NONE = "none"        # 新增：零隔离（知识文档）
```

---

## 6. LangChain 集成设计

### 6.1 Skill Chain Builder

构建可复用的 Skill Chain：

```python
# server/python/src/ai/components/skill/chain_builder.py

class SkillChainBuilder:
    """Skill Chain 构建器"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    def build_knowledge_skill_chain(
        self, skill_document: str, examples: str = "",
        context: dict[str, Any] | None = None,
    ) -> Runnable:
        """构建知识文档类型的 Chain"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

## 技能说明

{skill_document}

## 使用示例

{examples}

## 额外上下文

{extra_context}

请根据技能说明和示例，帮助用户完成任务。遵循以下原则：
1. 严格按照技能说明中的步骤执行
2. 注意技能中提到的常见错误和解决方案
3. 如果需要用户提供更多信息，主动询问
4. 使用清晰、专业的语言回复"""),
            ("user", "{user_request}"),
        ])

        return prompt | self.llm | StrOutputParser()

    def build_multi_skill_chain(
        self, skills: list[dict[str, str]], user_request: str,
    ) -> Runnable:
        """构建多 Skill 组合 Chain（类似 Hermes stacking skills）"""
        combined_skills = "\n\n---\n\n".join([
            f"## 技能 {i+1}: {skill['name']}\n\n{skill['document']}"
            for i, skill in enumerate(skills)
        ])

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的 AI 助手，现在需要组合使用以下 {skill_count} 个技能来帮助用户。

{combined_skills}

请根据所有技能的说明，协调使用它们来完成用户任务。"""),
            ("user", "{user_request}"),
        ])

        return prompt | self.llm | StrOutputParser()

    def build_skill_with_history_chain(
        self, skill_document: str,
        conversation_history: list[dict[str, str]],
    ) -> Runnable:
        """构建带对话历史的 Skill Chain（支持多轮对话）"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的 AI 助手，现在需要使用以下技能来帮助用户。

{skill_document}"""),
            MessagesPlaceholder(variable_name="history"),
            ("user", "{user_request}"),
        ])

        return prompt | self.llm | StrOutputParser()
```

### 6.2 Skill Context Manager

管理 Skill 上下文和状态：

```python
# server/python/src/ai/components/skill/context_manager.py

@dataclass
class SkillExecutionContext:
    """Skill 执行上下文"""
    skill_id: str
    skill_name: str
    skill_type: str  # knowledge | script

    user_id: str
    tenant_id: str
    conversation_id: str
    message_history: list[dict[str, str]] = field(default_factory=list)

    skill_document: str = ""
    examples: dict[str, str] = field(default_factory=dict)

    loaded_at: datetime = field(default_factory=datetime.now)
    invoke_count: int = 0
    last_invoked_at: datetime | None = None

    chain_cache: dict[str, Any] = field(default_factory=dict)

class SkillContextManager:
    """Skill 上下文管理器"""

    def __init__(self):
        self._contexts: dict[str, SkillExecutionContext] = {}

    async def load_skill(
        self, skill_id: str, user_id: str, tenant_id: str, conversation_id: str,
    ) -> SkillExecutionContext:
        """加载 Skill 并创建上下文"""
        context_key = f"{tenant_id}:{user_id}:{skill_id}"

        if context_key in self._contexts:
            return self._contexts[context_key]

        # 从数据库加载 Skill 定义
        async with get_db_session() as session:
            skill_def = await plugin_definition_service.get_by_plugin_id(session, skill_id)

        if not skill_def or skill_def.plugin_type != "skill":
            raise SkillNotFoundError(f"Skill 不存在: {skill_id}")

        # 从 MinIO 加载文档
        skill_documents = await self._load_skill_documents(skill_def.storage_key)

        context = SkillExecutionContext(
            skill_id=skill_id,
            skill_name=skill_def.name,
            skill_type=skill_def.skill_type,
            user_id=user_id,
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            skill_document=skill_documents.get("SKILL.md", ""),
            examples={k: v for k, v in skill_documents.items() if k != "SKILL.md"},
        )

        self._contexts[context_key] = context
        return context

    async def invoke_skill(
        self, skill_id: str, user_request: str,
        context: dict[str, Any] | None = None,
    ) -> str:
        """调用 Skill"""
        skill_context = self._get_active_context(skill_id)
        if not skill_context:
            raise RuntimeError(f"Skill 未加载: {skill_id}")

        skill_context.invoke_count += 1
        skill_context.last_invoked_at = datetime.now()

        chain = self._get_or_build_chain(skill_context)

        return await chain.ainvoke({
            "user_request": user_request,
            "extra_context": context or {},
            "examples": self._format_examples(skill_context.examples),
            "skill_document": skill_context.skill_document,
        })

    def _get_or_build_chain(self, context: SkillExecutionContext) -> Runnable:
        """获取或构建 Chain（带缓存）"""
        cache_key = f"chain_{context.skill_id}"

        if cache_key not in context.chain_cache:
            llm = model_config_service.get_langchain_llm()
            builder = SkillChainBuilder(llm)
            chain = builder.build_knowledge_skill_chain(
                skill_document=context.skill_document,
                examples=self._format_examples(context.examples),
            )
            context.chain_cache[cache_key] = chain

        return context.chain_cache[cache_key]
```

### 6.3 与对话系统集成

```python
# server/python/src/ai/services/conversation_service.py

class ConversationService:
    """对话服务 - 扩展支持 Skill"""

    async def chat_with_skill(
        self, session: AsyncSession, conversation_id: str,
        user_message: str, skill_ids: list[str],
        user_id: str, tenant_id: str,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """带 Skill 的对话"""
        # 1. 加载 Skills
        skill_contexts = []
        for skill_id in skill_ids:
            context = await skill_context_manager.load_skill(
                skill_id, user_id, tenant_id, conversation_id
            )
            skill_contexts.append(context)

        # 2. 构建组合 Chain
        if len(skill_contexts) == 1:
            chain = self._build_single_skill_chain(skill_contexts[0])
        else:
            chain = self._build_multi_skill_chain(skill_contexts)

        # 3. 保存用户消息
        await self._save_message(session, conversation_id, "user", user_message)

        # 4. 流式调用 LLM
        assistant_message = ""
        async for chunk in chain.astream({"user_request": user_message}):
            assistant_message += chunk
            yield {"type": "chunk", "content": chunk}

        # 5. 保存助手消息
        await self._save_message(session, conversation_id, "assistant", assistant_message)

        yield {"type": "complete", "message": assistant_message}
```

### 6.4 API 控制器扩展

```python
# server/python/src/ai/controllers/console/skill_controller.py

router = APIRouter(prefix="/ai/console/v1/skills", tags=["Skills"])

@router.post("/invoke")
async def invoke_skill(
    request: SkillInvokeRequest,
    session: AsyncSession = Depends(get_db_session),
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """调用 Skill（支持单个或多个 Skill 组合调用）"""
    async def generate():
        async for chunk in conversation_service.chat_with_skill(
            session, request.conversation_id, request.user_message,
            request.skill_ids, user_id, tenant_id,
        ):
            yield f"data: {json.dumps(chunk)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/{skill_id}/preview")
async def preview_skill(
    skill_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """预览 Skill 内容（返回 Skill 文档和示例）"""
    skill_def = await plugin_definition_service.get_by_plugin_id(session, skill_id)

    if not skill_def or skill_def.plugin_type != "skill":
        raise HTTPException(404, "Skill 不存在")

    documents = await skill_storage_service.load_skill_documents(skill_def.storage_key)

    return ORJSONResponse({
        "code": 200,
        "data": {
            "skill_id": skill_id,
            "name": skill_def.name,
            "description": skill_def.description,
            "skill_type": skill_def.skill_type,
            "documents": documents,
        }
    })
```

---

## 7. 前端集成设计

### 7.1 前端架构扩展

```
web/vue/src/
├── tenant/
│   ├── pages/
│   │   ├── admin/
│   │   │   ├── PluginDefinitionListPage.vue     # 复用：插件列表
│   │   │   ├── PluginDefinitionDetailPage.vue   # 复用：插件详情
│   │   │   └── SkillMarketplacePage.vue         # 新增：Skill 市场浏览
│   │   └── console/
│   │       └── SkillInvocationPage.vue          # 新增：Skill 调用界面
│   └── api/
│       └── plugin.ts                             # 复用：扩展 API
├── ai/
│   └── components/
│       ├── SkillCard.vue                        # 新增：Skill 卡片
│       ├── SkillPreview.vue                     # 新增：Skill 预览
│       ├── SkillInvocationPanel.vue             # 新增：Skill 调用面板
│       └── SkillStacker.vue                     # 新增：多 Skill 组合器
└── components/
    └── chat/
        └── ChatWithSkill.vue                    # 新增：带 Skill 的聊天界面
```

### 7.2 Skill 市场浏览页面

复用现有市场架构，新增 Skill 专属视图：

- 搜索框：按关键词搜索 Skill
- 类型筛选：全部 / 知识文档 / 简单脚本
- Skill 卡片网格：展示 Skill 信息（名称、作者、描述、标签、下载量、版本）
- 快速操作：安装、预览

### 7.3 Skill 卡片组件

展示 Skill 信息和快速操作：

- 卡片头部：Skill 名称 + 类型徽章（知识文档/简单脚本）
- 卡片内容：描述、标签、统计信息（下载量、版本）
- 操作按钮：安装（未安装时）/ 已安装（禁用）+ 预览

### 7.4 Skill 调用面板

集成到对话界面，支持快速调用 Skill：

- 已选 Skills 区域：展示已选择的 Skill（最多 5 个）
- Skill 列表：可点击选择/取消选择
- 输入区域：用户请求输入框 + 执行按钮

### 7.5 集成到聊天界面

扩展现有聊天组件，支持 Skill 快捷调用：

- 主聊天区域：消息列表 + 输入框
- Skills 切换按钮：显示已安装 Skill 数量
- Skill 调用面板：侧边栏，支持选择和调用

### 7.6 API 扩展

```typescript
// web/vue/src/tenant/api/plugin.ts

export interface RemoteSkillInfo {
  plugin_id: string
  name: string
  description: string | null
  version: string
  author: string
  plugin_type: 'skill'
  skill_type: 'knowledge' | 'script'
  tags: string[]
  downloads: number | null
  icon: string | null
  download_url: string
}

export interface PluginDefinition {
  id: string
  plugin_id: string
  plugin_type: 'tool' | 'model' | 'agent' | 'skill'  // 新增 skill
  skill_type?: 'knowledge' | 'script'                 // 新增
  name: string
  description: string | null
  version: string
  author: string
  icon: string | null
  tags: string[]
}

// 新增 API
export async function getRemoteSkills(marketplaceId, params): Promise<...>
export async function syncSkillFromMarketplace(marketplaceId, skillId): Promise<...>
export async function getInstalledSkills(): Promise<...>
export async function previewSkill(skillId): Promise<...>
export async function invokeSkillStream(request, onChunk, onComplete): Promise<void>
```

---

## 8. 存储与错误处理设计

### 8.1 MinIO 存储结构

```
plugin-bucket/
├── plugins/                          # 现有：tool/model/agent 插件
│   └── global/
│       └── {plugin_id}/
│           └── {version}/
│               ├── plugin.zip
│               └── checksum.sha256
│
└── skills/                           # 新增：Skill 存储
    ├── global/                       # 全局 Skill（市场同步）
    │   └── {skill_id}/
    │       └── {version}/
    │           ├── skill.zip
    │           └── checksum.sha256
    │
    └── {tenant_id}/                  # 租户级 Skill 缓存（可选）
        └── {skill_id}/
            └── {version}/
                └── skill.zip
```

存储路径规范：`skills/{tenant_id|global}/{skill_id}/{version}/skill.zip`

### 8.2 存储服务扩展

```python
# server/python/src/tenant/services/plugin_storage_service.py

class PluginStorageService:
    """插件存储服务 - 扩展支持 Skill"""

    SKILL_PATH_TEMPLATE = "skills/{scope}/{skill_id}/{version}/skill.zip"

    async def upload_skill_package(
        self, skill_id: str, skill_data: bytes, checksum: str,
        version: str = "latest",
    ) -> str:
        """上传 Skill 包到 MinIO"""
        storage_key = f"skills/global/{skill_id}/{version}/skill.zip"
        await self.storage.upload(
            bucket=self.bucket_name, name=storage_key,
            data=skill_data, content_type="application/zip",
        )

        checksum_key = f"skills/global/{skill_id}/{version}/checksum.sha256"
        await self.storage.upload(
            bucket=self.bucket_name, name=checksum_key,
            data=checksum.encode("utf-8"), content_type="text/plain",
        )
        return storage_key

    async def download_skill_package(self, storage_key: str) -> bytes:
        """从 MinIO 下载 Skill 包"""
        return await self.storage.download(bucket=self.bucket_name, name=storage_key)

    async def load_skill_documents(self, storage_key: str) -> dict[str, str]:
        """加载 Skill 包中的所有 Markdown 文档"""
        import zipfile, io
        skill_data = await self.download_skill_package(storage_key)
        documents = {}

        try:
            with zipfile.ZipFile(io.BytesIO(skill_data)) as zf:
                for file_info in zf.filelist:
                    if file_info.filename.endswith(".md"):
                        documents[file_info.filename] = zf.read(file_info.filename).decode("utf-8")
        except zipfile.BadZipFile:
            documents["SKILL.md"] = skill_data.decode("utf-8")

        return documents
```

### 8.3 错误处理体系

```python
# server/python/src/ai/components/plugin/engine/core/exceptions.py

class SkillError(Exception):
    """Skill 错误基类"""

class SkillNotFoundError(SkillError):
    """Skill 不存在"""

class SkillPreparationError(SkillError):
    """Skill 准备失败"""
    def __init__(self, skill_id: str, reason: str):
        self.skill_id = skill_id
        self.reason = reason
        super().__init__(f"Skill 准备失败 [{skill_id}]: {reason}")

class SkillInvocationError(SkillError):
    """Skill 调用失败"""
    def __init__(self, skill_id: str, reason: str):
        self.skill_id = skill_id
        self.reason = reason
        super().__init__(f"Skill 调用失败 [{skill_id}]: {reason}")

class SkillSecurityError(SkillError):
    """Skill 安全验证失败"""
    def __init__(self, skill_id: str, violations: list[str]):
        self.skill_id = skill_id
        self.violations = violations
        super().__init__(f"Skill 安全验证失败 [{skill_id}]: {', '.join(violations)}")

class SkillTimeoutError(SkillError):
    """Skill 执行超时"""
    def __init__(self, skill_id: str, timeout: int):
        self.skill_id = skill_id
        self.timeout = timeout
        super().__init__(f"Skill 执行超时 [{skill_id}]: {timeout}s")
```

### 8.4 错误处理策略

| 错误类型 | 处理策略 | 是否重试 |
|---------|---------|---------|
| SkillNotFoundError | 立即返回错误 | 否 |
| SkillPreparationError | 返回详细原因 | 否 |
| SkillSecurityError | 立即返回，记录安全日志 | 否 |
| SkillTimeoutError | 立即返回，终止执行 | 否 |
| SkillInvocationError | 指数退避重试（最多 2 次） | 是 |
| 网络错误 | 指数退避重试（最多 2 次） | 是 |

### 8.5 事件监听器扩展

```python
# server/python/src/tenant/listeners/handlers/skill_handler.py

class SkillInstallationFailedHandler:
    """Skill 安装失败处理器"""
    async def handle(self, message: dict) -> None:
        tenant_id = message["tenant_id"]
        skill_id = message["skill_id"]
        reason = message["reason"]

        TenantContext.set_tenant_id(tenant_id)
        async with get_listener_session() as session:
            installation = await TenantPluginInstallation.first_by_fields(
                session, {"tenant_id": tenant_id, "plugin_id": skill_id}
            )
            if installation:
                await installation.update(session, {
                    "status": "FAILED",
                    "error_message": reason,
                })

class SkillUninstallFailedHandler:
    """Skill 卸载失败处理器"""
    async def handle(self, message: dict) -> None:
        # 记录失败日志，标记为需手动处理
        ...
```

### 8.6 监控指标

```python
class SkillMetrics:
    """Skill 运行时指标"""
    invoke_count: int
    success_count: int
    failure_count: int
    total_duration_ms: int
    last_invoke_at: datetime | None
    recent_errors: list[dict]  # 保留最近 10 条错误

    def get_metrics(self) -> dict:
        return {
            "invoke_count": self.invoke_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.success_count / self.invoke_count if self.invoke_count > 0 else 0,
            "avg_duration_ms": self.total_duration_ms / self.invoke_count if self.invoke_count > 0 else 0,
            "last_invoke_at": self.last_invoke_at.isoformat() if self.last_invoke_at else None,
            "recent_errors": self.recent_errors,
        }
```

---

## 9. 测试策略设计

### 9.1 测试架构

```
server/python/tests/
├── tenant/
│   ├── unit/
│   │   ├── marketplace/
│   │   │   ├── test_agentskills_adapter.py      # 新增
│   │   │   ├── test_modelscope_skill_adapter.py # 新增
│   │   │   └── test_local_skill_adapter.py      # 新增
│   │   └── services/
│   │       └── test_plugin_storage_service.py   # 扩展
│   └── integration/
│       └── test_skill_sync_flow.py              # 新增
│
├── ai/
│   ├── unit/
│   │   ├── runtime/
│   │   │   ├── test_knowledge_skill_runtime.py  # 新增
│   │   │   └── test_sandbox_skill_runtime.py    # 新增
│   │   ├── skill/
│   │   │   ├── test_chain_builder.py            # 新增
│   │   │   └── test_context_manager.py          # 新增
│   │   └── security/
│   │       └── test_sandbox_security.py         # 新增
│   └── integration/
│       ├── test_skill_invocation_flow.py        # 新增
│       └── test_skill_conversation_flow.py      # 新增
│
└── e2e/
    └── test_skill_marketplace_e2e.py            # 新增
```

### 9.2 测试用例覆盖矩阵

| 测试场景 | 单元测试 | 集成测试 | E2E 测试 |
|---------|---------|---------|---------|
| 市场适配器连接 | ✅ | ✅ | ✅ |
| Skill 列表浏览 | ✅ | ✅ | ✅ |
| Skill 下载 | ✅ | ✅ | ✅ |
| Skill 同步 | ✅ | ✅ | ✅ |
| Skill 安装 | ✅ | ✅ | ✅ |
| 知识文档加载 | ✅ | ✅ | - |
| 知识文档调用 | ✅ | ✅ | ✅ |
| 脚本沙箱安全 | ✅ | - | - |
| 脚本执行 | ✅ | ✅ | ✅ |
| 多 Skill 组合 | ✅ | ✅ | - |
| 错误处理 | ✅ | ✅ | - |
| 超时处理 | ✅ | - | - |
| 资源限制 | ✅ | - | - |

### 9.3 关键测试用例

**市场适配器测试：**
- 测试成功获取 Skill 列表
- 测试分页获取 Skill 列表
- 测试成功下载 Skill 包
- 测试下载不存在的 Skill
- 测试连接测试功能

**运行时测试：**
- 测试成功准备 Skill（KnowledgeSkillRuntime）
- 测试 Skill 包缺少 SKILL.md 时的错误处理
- 测试成功调用 Skill（流式返回）
- 测试未启动时调用 Skill 的错误处理

**沙箱安全测试：**
- 测试禁止的导入（os、subprocess、sys）
- 测试禁止的函数（eval、exec、compile）
- 测试安全的脚本通过验证
- 测试安全全局命名空间只允许白名单
- 测试超时限制

**LangChain 集成测试：**
- 测试构建知识文档 Chain
- 测试构建多 Skill 组合 Chain
- 测试构建带历史记录的 Chain

**E2E 测试：**
- 完整流程：市场配置 → 浏览 → 同步 → 安装 → 调用
- 多 Skill 组合调用

---

## 10. 实现优先级

### 10.1 阶段划分

| 阶段 | 内容 | 依赖 |
|------|------|------|
| Phase 1 | 数据模型扩展 + 迁移 | 无 |
| Phase 2 | 市场适配器实现（AgentSkills、ModelScope Skill、Local） | Phase 1 |
| Phase 3 | 存储服务扩展（MinIO） | Phase 1 |
| Phase 4 | 运行时实现（KnowledgeSkillRuntime、SandboxSkillRuntime） | Phase 1 |
| Phase 5 | LangChain 集成（ChainBuilder、ContextManager） | Phase 4 |
| Phase 6 | 对话系统集成 + API 控制器 | Phase 5 |
| Phase 7 | 前端集成（市场浏览、调用面板、聊天集成） | Phase 6 |
| Phase 8 | 事件监听器 + 监控指标 | Phase 4 |
| Phase 9 | 测试覆盖（单元/集成/E2E） | 全部 |

### 10.2 关键交付物

1. **数据库迁移脚本**：扩展 `plugin_definitions` 表
2. **3 个市场适配器**：AgentSkills、ModelScope Skill、Local
3. **2 个运行时实现**：KnowledgeSkillRuntime、SandboxSkillRuntime
4. **LangChain 集成组件**：ChainBuilder、ContextManager
5. **API 控制器**：Skill 调用、预览接口
6. **前端页面**：Skill 市场浏览、调用面板、聊天集成
7. **测试套件**：单元测试、集成测试、E2E 测试

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Skill 包格式不统一 | 适配器实现复杂 | 支持 ZIP 和单文件两种格式 |
| 沙箱逃逸 | 安全风险 | 多层防御：RestrictedPython + 白名单 + 子进程 |
| LLM 调用成本 | 运营成本 | Chain 缓存 + 上下文复用 |
| 市场接口变更 | 适配器失效 | 适配器版本化 + 连接测试 |
| 前端复杂度增加 | 用户体验 | 复用现有组件 + 渐进式集成 |

---

## 12. 参考资源

- 现有插件市场设计：`docs/superpowers/specs/2026-06-29-remote-plugin-marketplace-design.md`
- 插件定义管理设计：`docs/superpowers/specs/2026-06-29-plugin-definition-management-design.md`
- 插件资源管理设计：`docs/superpowers/specs/2026-06-25-plugin-resource-management-enhancement-design.md`
- Hermes Agent Skills 文档：`D:\Project\ai\marketplace\hermes-agent\website\docs\user-guide\features\skills.md`
- AgentSkills 开放标准：https://agentskills.io/specification
- ModelScope Skills 市场：https://www.modelscope.cn/skills
- LangChain 文档：https://python.langchain.com/docs/get_started/introduction
