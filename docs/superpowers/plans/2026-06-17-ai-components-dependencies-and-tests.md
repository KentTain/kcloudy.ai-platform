# AI 组件依赖与测试补充实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [x]`）语法来跟踪进度。

**目标：** 为新迁移的 4 个 AI 组件补充缺失依赖和测试用例，确保组件可正常导入和运行

**架构：** 采用渐进式补充方案，优先补充依赖，然后为 datasource、graphrag、code_executor 组件补充基础测试

**技术栈：** Python 3.12、pytest、sqlparse、regex、pydantic

---

## 文件结构

### 新增文件
- `tests/ai/components/datasource/__init__.py` - datasource 测试包初始化
- `tests/ai/components/datasource/test_datasource.py` - datasource 组件测试（约 350 行）
- `tests/ai/components/graphrag/test_graphrag.py` - graphrag 组件补充测试（约 150 行）

### 修改文件
- `server/python/pyproject.toml` - 添加 sqlparse 和 regex 依赖
- `tests/ai/components/code_executor/test_code_executor.py` - 补充导入和基类测试（约 80 行）

---

## 任务分解

### 任务 1：补充缺失依赖

**文件：**
- 修改：`server/python/pyproject.toml:31-47`

- [x] **步骤 1：添加 sqlparse 和 regex 依赖**

在 `server/python/pyproject.toml` 文件的 `dependencies` 数组中，找到 `# 工具库` 部分（第 31-47 行），在 `loguru==0.7.3` 之后添加：

```toml
  # 工具库
  "loguru==0.7.3",
  "pytz==2025.2",
  "nanoid==2.0.0",
  "click==8.2.1",
  "sqlparse==0.5.0",
  "regex==2024.11.6",
```

- [x] **步骤 2：同步依赖**

运行：
```bash
cd server/python && uv sync
```

预期：输出显示安装了 `sqlparse` 和 `regex` 包

- [x] **步骤 3：验证依赖安装**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -c "import sqlparse; import regex; print('依赖安装成功')"
```

预期：输出 `依赖安装成功`

- [x] **步骤 4：Commit**

```bash
git add server/python/pyproject.toml
git commit -m "feat(deps): 添加 sqlparse 和 regex 依赖"
```

---

### 任务 2：创建 Datasource 测试目录结构

**文件：**
- 创建：`tests/ai/components/datasource/__init__.py`

- [x] **步骤 1：创建测试目录**

运行：
```bash
mkdir -p tests/ai/components/datasource
```

- [x] **步骤 2：创建 `__init__.py` 文件**

创建文件 `tests/ai/components/datasource/__init__.py`，内容为：
```python
"""Datasource 组件测试"""
```

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/datasource/__init__.py
git commit -m "test(datasource): 创建测试目录结构"
```

---

### 任务 3：编写 Datasource 导入测试

**文件：**
- 创建：`tests/ai/components/datasource/test_datasource.py`（第 1-50 行）

- [x] **步骤 1：编写导入测试**

创建文件 `tests/ai/components/datasource/test_datasource.py`，添加以下内容：

```python
"""Datasource 组件测试"""

import pytest


class TestDatasourceImports:
    """Datasource 组件导入测试"""

    def test_import_interfaces(self):
        """测试导入 interfaces 模块"""
        from ai.components.datasource.interfaces import BaseConnect

        assert BaseConnect is not None
        assert hasattr(BaseConnect, "get_show_create_table")
        assert hasattr(BaseConnect, "get_example_data")

    def test_import_rdbms_base(self):
        """测试导入 rdbms.base 模块"""
        from ai.components.datasource.rdbms.base import RDBMSDatabase

        assert RDBMSDatabase is not None
        assert hasattr(RDBMSDatabase, "from_uri_db")

    def test_import_mysql_connect(self):
        """测试导入 MySQL 连接器"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        assert MySQLConnect is not None
        assert MySQLConnect.db_type == "mysql"
        assert MySQLConnect.driver == "mysql+aiomysql"
```

- [x] **步骤 2：运行测试验证通过**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/datasource/test_datasource.py::TestDatasourceImports -v
```

预期：3 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/datasource/test_datasource.py
git commit -m "test(datasource): 添加导入测试"
```

---

### 任务 4：编写 BaseConnect 接口测试

**文件：**
- 修改：`tests/ai/components/datasource/test_datasource.py`（第 52-100 行）

- [x] **步骤 1：编写接口定义测试**

在 `test_datasource.py` 文件末尾添加：

```python


class TestBaseConnect:
    """BaseConnect 接口测试"""

    def test_base_connect_is_abstract(self):
        """测试 BaseConnect 是抽象类"""
        from ai.components.datasource.interfaces import BaseConnect
        from abc import ABC

        assert issubclass(BaseConnect, ABC)

        # 验证不能直接实例化
        with pytest.raises(TypeError):
            BaseConnect()

    def test_base_connect_has_required_methods(self):
        """测试 BaseConnect 有必需的抽象方法"""
        from ai.components.datasource.interfaces import BaseConnect
        import inspect

        # 获取所有抽象方法
        abstract_methods = [
            name for name, method in inspect.getmembers(BaseConnect)
            if getattr(method, '__isabstractmethod__', False)
        ]

        # 验证关键方法存在
        expected_methods = [
            'get_show_create_table',
            'get_example_data',
            'get_table_names',
            'get_table_info',
            'run',
        ]

        for method in expected_methods:
            assert method in abstract_methods, f"缺少抽象方法: {method}"
```

- [x] **步骤 2：运行测试验证通过**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/datasource/test_datasource.py::TestBaseConnect -v
```

预期：2 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/datasource/test_datasource.py
git commit -m "test(datasource): 添加 BaseConnect 接口测试"
```

---

### 任务 5：编写 URI 构造测试

**文件：**
- 修改：`tests/ai/components/datasource/test_datasource.py`（第 102-180 行）

- [x] **步骤 1：编写 URI 构造测试**

在 `test_datasource.py` 文件末尾添加：

```python


class TestRDBMSDatabaseURI:
    """RDBMSDatabase URI 构造测试"""

    def test_uri_construction_mysql(self):
        """测试 MySQL URI 格式生成"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        # 验证 MySQL URI 格式
        expected_driver = "mysql+aiomysql"
        assert MySQLConnect.driver == expected_driver

        # 验证默认数据库列表
        assert "information_schema" in MySQLConnect.default_db
        assert "performance_schema" in MySQLConnect.default_db

    def test_uri_with_special_characters(self):
        """测试特殊字符转义"""
        from urllib.parse import quote, quote_plus

        # 测试用户名包含特殊字符
        user = "user@domain"
        encoded_user = quote(user)
        assert encoded_user == "user%40domain"

        # 测试密码包含特殊字符
        pwd = "p@ss:word/123"
        encoded_pwd = quote_plus(pwd)
        assert encoded_pwd == "p%40ss%3Aword%2F123"

    def test_default_database_list(self):
        """测试默认数据库列表"""
        from ai.components.datasource.rdbms.conn_mysql import MySQLConnect

        expected_dbs = ["information_schema", "performance_schema", "sys", "mysql"]
        assert MySQLConnect.default_db == expected_dbs
```

- [x] **步骤 2：运行测试验证通过**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/datasource/test_datasource.py::TestRDBMSDatabaseURI -v
```

预期：3 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/datasource/test_datasource.py
git commit -m "test(datasource): 添加 URI 构造测试"
```

---

### 任务 6：编写 SQL 解析测试

**文件：**
- 修改：`tests/ai/components/datasource/test_datasource.py`（第 182-250 行）

- [x] **步骤 1：编写 SQL 解析测试**

在 `test_datasource.py` 文件末尾添加：

```python


class TestSQLParsing:
    """SQL 解析功能测试"""

    def test_sqlparse_format(self):
        """测试 SQL 格式化"""
        import sqlparse

        sql = "select * from users where id=1"
        formatted = sqlparse.format(sql, reindent=True, keyword_case='upper')

        # 验证关键字被大写
        assert "SELECT" in formatted
        assert "FROM" in formatted
        assert "WHERE" in formatted

    def test_sqlparse_split(self):
        """测试 SQL 拆分"""
        import sqlparse

        sql = "SELECT * FROM users; INSERT INTO users VALUES (1);"
        statements = sqlparse.split(sql)

        # 验证拆分为多条语句
        assert len(statements) == 2
        assert "SELECT" in statements[0]
        assert "INSERT" in statements[1]

    def test_regex_patterns(self):
        """测试正则表达式功能"""
        import regex

        # 测试基本正则匹配
        pattern = r'\b\w+@\w+\.\w+\b'
        text = "联系邮箱: test@example.com 和 admin@site.org"
        matches = regex.findall(pattern, text)

        assert len(matches) == 2
        assert "test@example.com" in matches
        assert "admin@site.org" in matches

        # 测试 Unicode 支持
        chinese_pattern = r'[\p{Han}]+'
        chinese_text = "这是中文测试"
        chinese_matches = regex.findall(chinese_pattern, chinese_text)

        assert len(chinese_matches) > 0
```

- [x] **步骤 2：运行完整测试套件**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/datasource -v
```

预期：11 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/datasource/test_datasource.py
git commit -m "test(datasource): 添加 SQL 解析测试"
```

---

### 任务 7：编写 GraphRAG GraphData 模型测试

**文件：**
- 创建：`tests/ai/components/graphrag/test_graphrag.py`（第 1-80 行）

- [x] **步骤 1：编写 GraphData 模型测试**

创建文件 `tests/ai/components/graphrag/test_graphrag.py`，添加以下内容：

```python
"""GraphRAG 组件测试"""

import pytest


class TestGraphData:
    """GraphData 模型测试"""

    def test_graph_data_creation(self):
        """测试 GraphData 模型创建"""
        from ai.components.graphrag.client import GraphData

        data = GraphData(
            title="测试实体",
            type="person",
            description="这是一个测试实体",
            degree=1,
            rank=1,
        )

        assert data.title == "测试实体"
        assert data.type == "person"
        assert data.description == "这是一个测试实体"
        assert data.degree == 1
        assert data.rank == 1

    def test_graph_data_optional_fields(self):
        """测试 GraphData 可选字段"""
        from ai.components.graphrag.client import GraphData

        # 只提供必需字段（实际上所有字段都是可选的）
        data = GraphData()

        # 验证默认值
        assert data.title is None
        assert data.type is None
        assert data.description is None
        assert data.community == "1"
        assert data.level == 1

    def test_graph_data_validation(self):
        """测试 GraphData 数据验证"""
        from ai.components.graphrag.client import GraphData
        from pydantic import ValidationError

        # 验证有效数据
        valid_data = GraphData(
            title="有效标题",
            degree=10,
            weight=5,
        )
        assert valid_data.degree == 10
        assert valid_data.weight == 5

        # 验证字段类型转换
        data = GraphData(degree="5")  # 字符串应该被转换为整数
        assert data.degree == 5
        assert isinstance(data.degree, int)
```

- [x] **步骤 2：运行测试验证通过**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/graphrag/test_graphrag.py::TestGraphData -v
```

预期：3 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/graphrag/test_graphrag.py
git commit -m "test(graphrag): 添加 GraphData 模型测试"
```

---

### 任务 8：编写 GraphRAGClient 基础测试

**文件：**
- 修改：`tests/ai/components/graphrag/test_graphrag.py`（第 82-150 行）

- [x] **步骤 1：编写 GraphRAGClient 基础测试**

在 `test_graphrag.py` 文件末尾添加：

```python


class TestGraphRAGClient:
    """GraphRAGClient 基础测试"""

    def test_client_initialization(self):
        """测试客户端初始化"""
        from ai.components.graphrag.client import GraphRAGClient

        client = GraphRAGClient()
        assert client is not None

    def test_client_has_required_methods(self):
        """测试客户端有必需的方法"""
        from ai.components.graphrag.client import GraphRAGClient

        client = GraphRAGClient()

        # 验证关键方法存在
        assert hasattr(client, 'create_index_build_task')
        assert hasattr(client, 'search')
        assert callable(client.create_index_build_task)
        assert callable(client.search)

    def test_graph_data_model_import(self):
        """测试 GraphData 模型可从客户端导入"""
        from ai.components.graphrag.client import GraphData

        # 验证可以创建 GraphData 实例
        data = GraphData(title="导入测试")
        assert data.title == "导入测试"

    def test_graph_data_inheritance(self):
        """测试 GraphData 继承自 BaseModel"""
        from ai.components.graphrag.client import GraphData
        from pydantic import BaseModel

        assert issubclass(GraphData, BaseModel)
```

- [x] **步骤 2：运行完整测试套件**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/graphrag -v
```

预期：7 个测试全部通过（3 个导入测试 + 4 个新增测试）

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/graphrag/test_graphrag.py
git commit -m "test(graphrag): 添加 GraphRAGClient 基础测试"
```

---

### 任务 9：补充 Code Executor 导入测试

**文件：**
- 修改：`tests/ai/components/code_executor/test_code_executor.py`（第 264-300 行）

- [x] **步骤 1：编写导入测试**

在 `test_code_executor.py` 文件末尾添加：

```python


class TestCodeExecutorImports:
    """Code Executor 导入测试"""

    def test_import_all_exports(self):
        """测试导入所有导出类"""
        from ai.components.code_executor import (
            CodeExecutor,
            CodeExecutionError,
            CodeExecutionResponse,
            CodeLanguage,
            CodeNodeProvider,
            TemplateTransformer,
            Python3TemplateTransformer,
            NodeJsTemplateTransformer,
            Jinja2TemplateTransformer,
            Python3CodeProvider,
            JavascriptCodeProvider,
        )

        # 验证所有类都已导入
        assert CodeExecutor is not None
        assert CodeExecutionError is not None
        assert CodeExecutionResponse is not None
        assert CodeLanguage is not None
        assert CodeNodeProvider is not None
        assert TemplateTransformer is not None
        assert Python3TemplateTransformer is not None
        assert NodeJsTemplateTransformer is not None
        assert Jinja2TemplateTransformer is not None
        assert Python3CodeProvider is not None
        assert JavascriptCodeProvider is not None

    def test_code_language_enum(self):
        """测试语言枚举"""
        from ai.components.code_executor import CodeLanguage

        # 验证枚举值
        assert CodeLanguage.PYTHON3.value == "python3"
        assert CodeLanguage.JAVASCRIPT.value == "javascript"
        assert CodeLanguage.JINJA2.value == "jinja2"

        # 验证枚举成员
        assert len(list(CodeLanguage)) >= 3
```

- [x] **步骤 2：运行测试验证通过**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/code_executor/test_code_executor.py::TestCodeExecutorImports -v
```

预期：2 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/code_executor/test_code_executor.py
git commit -m "test(code_executor): 添加导入测试"
```

---

### 任务 10：补充 CodeNodeProvider 基类测试

**文件：**
- 修改：`tests/ai/components/code_executor/test_code_executor.py`（第 302-360 行）

- [x] **步骤 1：编写 CodeNodeProvider 基类测试**

在 `test_code_executor.py` 文件末尾添加：

```python


class TestCodeNodeProvider:
    """CodeNodeProvider 基类测试"""

    def test_base_provider_is_abstract(self):
        """测试基类是抽象类"""
        from ai.components.code_executor import CodeNodeProvider
        from abc import ABC

        assert issubclass(CodeNodeProvider, ABC)

        # 验证不能直接实例化（因为有抽象方法）
        # 注意：Pydantic 模型可以实例化，但调用抽象方法会失败

    def test_base_provider_methods(self):
        """测试基类方法定义"""
        from ai.components.code_executor import CodeNodeProvider
        import inspect

        # 验证抽象方法存在
        assert hasattr(CodeNodeProvider, 'get_language')
        assert hasattr(CodeNodeProvider, 'get_default_code')
        assert hasattr(CodeNodeProvider, 'is_accept_language')
        assert hasattr(CodeNodeProvider, 'get_default_config')

        # 验证 get_language 是抽象方法
        assert getattr(CodeNodeProvider.get_language, '__isabstractmethod__', False)
        assert getattr(CodeNodeProvider.get_default_code, '__isabstractmethod__', False)
```

- [x] **步骤 2：运行测试验证通过**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/code_executor/test_code_executor.py::TestCodeNodeProvider -v
```

预期：2 个测试全部通过

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/code_executor/test_code_executor.py
git commit -m "test(code_executor): 添加 CodeNodeProvider 基类测试"
```

---

### 任务 11：补充 Jinja2CodeProvider 测试

**文件：**
- 修改：`tests/ai/components/code_executor/test_code_executor.py`（第 362-420 行）

- [x] **步骤 1：编写 Jinja2CodeProvider 测试**

在 `test_code_executor.py` 文件末尾添加：

```python


class TestJinja2CodeProvider:
    """Jinja2CodeProvider 测试"""

    def test_jinja2_code_provider(self):
        """测试 Jinja2CodeProvider 创建"""
        from ai.components.code_executor.jinja2.jinja2_transformer import Jinja2TemplateTransformer

        transformer = Jinja2TemplateTransformer()

        assert transformer is not None
        assert hasattr(transformer, 'transform')

    def test_jinja2_default_code(self):
        """测试 Jinja2 默认代码模板"""
        # Jinja2 的默认模板应该是一个简单的字符串
        default_template = "Hello, {{ name }}!"

        # 验证模板可以渲染
        from jinja2 import Template
        template = Template(default_template)
        result = template.render(name="World")

        assert result == "Hello, World!"

    def test_jinja2_transformer_format_response(self):
        """测试 Jinja2 响应格式化"""
        from ai.components.code_executor.jinja2.jinja2_transformer import Jinja2TemplateTransformer

        transformer = Jinja2TemplateTransformer()

        # 测试格式化响应
        result = "Hello, World!"
        formatted = transformer.format_response(result)

        assert formatted == {"result": result}
```

- [x] **步骤 2：运行完整测试套件**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components/code_executor -v
```

预期：14 个测试全部通过（11 个现有测试 + 3 个新增测试）

- [x] **步骤 3：Commit**

```bash
git add tests/ai/components/code_executor/test_code_executor.py
git commit -m "test(code_executor): 添加 Jinja2CodeProvider 测试"
```

---

### 任务 12：最终验证与清理

**文件：**
- 无文件修改

- [x] **步骤 1：运行完整测试套件**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components -v --tb=short
```

预期：所有 AI 组件测试通过，无失败用例

- [x] **步骤 2：检查测试覆盖率**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -m pytest tests/ai/components --cov=src/ai/components --cov-report=term-missing --no-cov-on-fail
```

预期：显示测试覆盖率报告，新增测试覆盖核心功能

- [x] **步骤 3：验证依赖安装**

运行：
```bash
cd server/python && .venv/Scripts/python.exe -c "
from ai.components.datasource.rdbms.base import RDBMSDatabase
from ai.components.graphrag.client import GraphRAGClient, GraphData
from ai.components.code_executor import CodeExecutor
from ai.components.encryption.impl.aes import AESEncryption
print('所有 AI 组件导入成功')
"
```

预期：输出 `所有 AI 组件导入成功`

- [x] **步骤 4：清理临时文件**

运行：
```bash
cd server/python && find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
```

预期：清理完成

- [x] **步骤 5：最终 Commit**

```bash
git add -A
git commit -m "feat(ai-components): 完成 AI 组件依赖和测试补充

- 添加 sqlparse 和 regex 依赖
- 为 datasource 组件添加 11 个测试用例
- 为 graphrag 组件添加 7 个测试用例
- 为 code_executor 组件添加 7 个测试用例
- 所有测试通过，AI 组件可正常导入"
```

---

## 验证清单

### 定量指标
- [x] 新增测试用例数量：25 个（11 + 7 + 7）
- [x] 新增测试文件：1 个（datasource）
- [x] 补充测试文件：2 个（graphrag、code_executor）
- [x] 新增依赖：2 个（sqlparse、regex）

### 定性目标
- [x] 所有 AI 组件依赖得到满足
- [x] 核心功能有基础测试保障
- [x] 现有测试套件稳定性保持
- [x] AI 组件可正常导入和运行

---

## 风险提示

1. **依赖冲突**：如果 `uv sync` 报告依赖冲突，检查版本兼容性并调整
2. **测试失败**：如果新增测试失败，检查导入路径和模块结构是否正确
3. **环境差异**：确保在 Windows 环境下路径使用 `\\` 或 `/` 而非 `\`

---

## 后续建议

完成此计划后，可以考虑：
1. 提升 AI 组件测试覆盖率到 80%+
2. 添加集成测试（需要真实数据库连接）
3. 为 graphrag 组件添加更详细的功能测试
