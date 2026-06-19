# AI 组件依赖与测试补充设计文档

**日期**：2026-06-17
**状态**：设计完成，待实施
**目标**：为新迁移的 4 个 AI 组件（encryption、datasource、code_executor、graphrag）补充依赖和测试用例

## 背景

### 项目现状

通过最近的代码迁移，项目中新增了 4 个 AI 组件：

1. **encryption** - 加密组件（AES/RSA）
   - ✅ 已有完整测试覆盖（287行测试代码）
   - ✅ 依赖已满足

2. **datasource** - 数据源组件
   - ⚠️ 缺少测试文件
   - ❌ 缺少依赖：`sqlparse`、`regex`

3. **code_executor** - 代码执行器
   - ✅ 已有测试框架
   - ⚠️ 部分测试覆盖不足

4. **graphrag** - 图谱 RAG
   - ⚠️ 仅有导入测试
   - ⚠️ 组件结构复杂

### 测试运行情况

- 后端测试通过率：99.7%（702/705）
- 前端测试通过率：99.4%（497/501）
- AI 组件测试因缺少依赖部分未运行

## 目标

### 主要目标

1. 补充缺失的依赖包
2. 为缺少测试的组件补充基础测试
3. 确保所有 AI 组件可正常导入和运行
4. 保持现有测试套件的稳定性

### 测试覆盖策略

采用**快速覆盖**策略：
- 重点保证核心功能可用
- 测试覆盖主要路径
- 快速验证组件集成
- 不追求 100% 覆盖率

## 设计方案

### 方案选择

采用**渐进式补充**方案：
- 优先补充缺失依赖
- 为缺少测试的组件补充基础测试
- 验证现有测试通过
- 每步可验证，风险可控

### 实施步骤

#### 阶段一：依赖补充（5分钟）

**缺失依赖**：
- `sqlparse==0.5.0` - SQL 解析库（datasource 组件需要）
- `regex==2024.11.6` - 增强正则表达式库（datasource 组件需要）

**实施位置**：
- 文件：`server/python/pyproject.toml`
- 位置：`dependencies` 数组中的 `# 工具库` 部分

**验证方式**：
```bash
cd server/python
uv sync
.venv/Scripts/python.exe -c "import sqlparse; import regex; print('依赖安装成功')"
```

#### 阶段二：Datasource 组件测试（30分钟）

**组件结构**：
- `interfaces.py` - 抽象基类 BaseConnect
- `rdbms/base.py` - RDBMSDatabase（SQLAlchemy 异步包装器）
- `rdbms/conn_mysql.py` - MySQL 连接器

**测试文件**：`tests/ai/components/datasource/test_datasource.py`

**测试用例设计**（约 10-15 个）：

1. **导入测试**（3个）
   - `test_import_interfaces` - 验证 interfaces 模块可导入
   - `test_import_rdbms_base` - 验证 rdbms.base 模块可导入
   - `test_import_mysql_connect` - 验证 MySQL 连接器可导入

2. **接口定义测试**（2个）
   - `test_base_connect_is_abstract` - 验证 BaseConnect 是抽象类
   - `test_base_connect_has_required_methods` - 验证抽象方法定义

3. **URI 构造测试**（3个）
   - `test_uri_construction_mysql` - 测试 MySQL URI 格式生成
   - `test_uri_with_special_characters` - 测试特殊字符转义
   - `test_default_database_list` - 测试默认数据库列表

4. **SQL 解析测试**（3个）
   - `test_sqlparse_format` - 测试 SQL 格式化
   - `test_sqlparse_split` - 测试 SQL 拆分
   - `test_regex_patterns` - 测试正则表达式功能

**验证方式**：
```bash
.venv/Scripts/python.exe -m pytest tests/ai/components/datasource -v
```

#### 阶段三：GraphRAG 组件测试（20分钟）

**组件结构**：
- `client.py` - GraphRAGClient 客户端、GraphData 数据模型
- 多个子模块：index、llm、model、prompt、query、vector_stores、webserver

**已有测试**：
- `tests/ai/components/graphrag/test_imports.py` - 导入测试

**补充测试**：`tests/ai/components/graphrag/test_graphrag.py`

**测试用例设计**（约 8-10 个）：

1. **GraphData 模型测试**（3个）
   - `test_graph_data_creation` - 测试模型创建
   - `test_graph_data_optional_fields` - 测试可选字段
   - `test_graph_data_validation` - 测试数据验证

2. **GraphRAGClient 基础测试**（3个）
   - `test_client_initialization` - 测试客户端初始化
   - `test_client_has_required_methods` - 测试方法存在性
   - `test_graph_data_model_import` - 测试数据模型导入

**验证方式**：
```bash
.venv/Scripts/python.exe -m pytest tests/ai/components/graphrag -v
```

#### 阶段四：Code Executor 组件测试补充（15分钟）

**组件结构**：
- `code_executor.py` - 核心执行器
- `code_node_provider.py` - 代码提供者基类
- `template_transformer.py` - 模板转换器基类
- 三种语言支持：python3、javascript、jinja2

**已有测试**：
- `tests/ai/components/code_executor/test_code_executor.py` - 执行器测试

**补充测试**：在现有文件中补充

**测试用例设计**（约 5-8 个）：

1. **导入测试**（2个）
   - `test_import_all_exports` - 验证所有导出类
   - `test_code_language_enum` - 验证语言枚举

2. **CodeNodeProvider 基类测试**（2个）
   - `test_base_provider_is_abstract` - 验证基类是抽象类
   - `test_base_provider_methods` - 验证方法定义

3. **Jinja2CodeProvider 测试**（2个）
   - `test_jinja2_code_provider` - 测试 Provider 创建
   - `test_jinja2_default_code` - 测试默认代码模板

**验证方式**：
```bash
.venv/Scripts/python.exe -m pytest tests/ai/components/code_executor -v
```

#### 阶段五：验证与清理（10分钟）

**验证步骤**：

1. 运行完整测试套件
   ```bash
   .venv/Scripts/python.exe -m pytest tests/demo tests/framework tests/ai/components -v
   ```

2. 检查测试覆盖率
   ```bash
   .venv/Scripts/python.exe -m pytest --cov=src/ai/components --cov-report=term-missing
   ```

3. 清理临时文件和缓存

**验证标准**：
- 所有新增测试通过
- 现有测试不退化
- AI 组件可正常导入

## 预期成果

### 定量指标

- 新增测试用例：约 25-35 个
- 新增测试文件：1 个（datasource）
- 补充测试文件：2 个（graphrag、code_executor）
- 新增依赖：2 个（sqlparse、regex）

### 定性目标

1. **依赖完整性**：所有 AI 组件依赖得到满足
2. **测试覆盖**：核心功能有基础测试保障
3. **代码质量**：保持现有测试套件稳定性
4. **文档更新**：更新组件文档，说明测试覆盖情况

## 风险与缓解

### 潜在风险

1. **依赖冲突**
   - 风险：新增依赖可能与现有依赖冲突
   - 缓解：使用 uv sync 自动解决依赖冲突

2. **测试失败**
   - 风险：新增测试可能发现现有代码问题
   - 缓解：逐步验证，发现问题及时修复

3. **环境差异**
   - 风险：测试在不同环境可能表现不同
   - 缓解：使用 mock 隔离外部依赖

### 回滚方案

如果出现问题，可以：
1. 移除新增依赖
2. 删除新增测试文件
3. 恢复到之前状态

## 后续工作

### 短期（1周内）

1. 监控测试运行情况
2. 补充遗漏的测试用例
3. 修复发现的 bug

### 中期（1月内）

1. 提升测试覆盖率到 80%+
2. 添加集成测试
3. 性能测试

### 长期

1. 持续集成优化
2. 测试自动化
3. 代码质量监控

## 参考资料

- 测试执行结果报告：后端测试通过率 99.7%，前端测试通过率 99.4%
- 组件迁移记录：Git commit 28a50d2
- 项目架构文档：server/python/CLAUDE.md
