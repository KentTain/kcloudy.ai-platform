from collections import defaultdict
from enum import Enum
from typing import Any, Union

from pydantic import BaseModel

from ai_plugin.sdk.entities import *  # noqa: F403
from ai_plugin.sdk.entities.agent import *  # noqa: F403
from ai_plugin.sdk.entities.endpoint import *  # noqa: F403
from ai_plugin.sdk.entities.model import *  # noqa: F403
from ai_plugin.sdk.entities.model.llm import *  # noqa: F403
from ai_plugin.sdk.entities.model.moderation import *  # noqa: F403
from ai_plugin.sdk.entities.model.provider import *  # noqa: F403
from ai_plugin.sdk.entities.model.rerank import *  # noqa: F403
from ai_plugin.sdk.entities.model.speech2text import *  # noqa: F403
from ai_plugin.sdk.entities.model.text_embedding import *  # noqa: F403
from ai_plugin.sdk.entities.model.tts import *  # noqa: F403
from ai_plugin.sdk.entities.tool import *  # noqa: F403
from ai_plugin.server.core.documentation.schema_doc import list_schema_docs
from ai_plugin.server.core.entities import *  # noqa: F403
from ai_plugin.server.core.entities.plugin import *  # noqa: F403
from ai_plugin.server.core.entities.plugin.setup import *  # noqa: F403


class SchemaDocumentationGenerator:
    """模式文档生成器

    用于生成插件SDK的模式文档，包括类型引用关系分析和层次化文档组织。
    """

    def __init__(self):
        """初始化文档生成器

        设置各种数据结构用于跟踪类型引用关系和文档组织。
        """
        self._reference_counts: dict[type, int] = {}  # 引用计数
        self._reference_graph: dict[type, set[type]] = defaultdict(set)  # 引用关系图
        self._processed_types: set[type] = set()  # 已处理的类型
        self._field_descriptions: dict[tuple[type, str], str] = {}  # 字段描述
        self._schema_descriptions: dict[type, str] = {}  # 模式描述
        self._processed_field_types: set[type] = set()  # 已处理的字段类型
        self._type_to_schema: dict[type, Any] = {}  # 类型到模式的映射
        self._type_blocks: dict[type, int] = {}  # 类型块索引
        self._blocks: list[list] = []  # 文档块列表
        self._types: set[type] = set()  # 所有类型集合

    def _organize_toc(self) -> list[tuple[type, list[Any]]]:
        """组织目录的层次结构

        基于以下规则构建层次结构：
        1. 标记为top=True的类型首先放在根级别
        2. 被多个其他类型引用的类型放在根级别
        3. 未被任何其他类型引用的类型放在根级别
        4. 只被一个其他类型引用的类型作为其父类型的子级
        5. 对每个子类型递归继续此过程

        这确保了：
        - 重要类型（标记为top=True）易于访问
        - 属于多个其他类型的类型在根级别便于访问
        - 属于单个父级的类型正确嵌套
        - 层次结构反映了代码中的实际引用关系
        - 深层引用链得到正确表示（A -> B -> C显示为嵌套结构）

        Returns:
            元组列表，每个元组包含：
            - 父类型
            - 其子节点列表，每个都是(Type, List[Any])元组
        """
        # 构建反向引用映射：类型 -> 引用它的类型集合
        referenced_by = {t: set() for t in self._types}
        for t, refs in self._reference_graph.items():
            for ref in refs:
                if ref in referenced_by:
                    referenced_by[ref].add(t)

        def build_subtree(type_: type, processed: set[type]) -> tuple[type, list[Any]]:
            """递归为一个类型及其引用构建子树

            Args:
                type_: 要构建子树的类型
                processed: 已处理类型的集合，避免循环引用

            Returns:
                包含类型及其嵌套子级的元组
            """
            if type_ in processed:
                return type_, []

            processed.add(type_)
            children = []

            # 查找仅被此类型引用的所有类型
            for ref_type in self._reference_graph.get(type_, set()):
                # 如果这是对ref_type的唯一引用
                refs = referenced_by.get(ref_type, set())
                if len(refs) == 1 and next(iter(refs)) == type_:
                    subtree = build_subtree(ref_type, processed)
                    children.append(subtree)

            return type_, children

        # 开始构建层次结构
        hierarchy = []
        processed = set()

        # 阶段1：在根级别添加标记为top=True的类型
        for t in self._types:
            if (
                t not in processed
                and hasattr(t, "__schema_docs__")
                and any(doc.top for doc in t.__schema_docs__)
            ):
                subtree = build_subtree(t, processed)
                hierarchy.append(subtree)

        # 阶段2：添加未被任何其他类型引用的类型
        # 或被多个类型引用的类型
        remaining = [t for t in self._types if len(referenced_by[t]) != 1]
        for t in remaining:
            if t not in processed:
                subtree = build_subtree(t, processed)
                hierarchy.append(subtree)

        # 阶段3：添加任何未处理的剩余类型
        for t in self._types:
            if t not in processed:
                subtree = build_subtree(t, processed)
                hierarchy.append(subtree)

        return hierarchy

    def generate_docs(self, output_file: str):
        """生成文档

        Args:
            output_file: 输出文件路径
        """
        with open(output_file, "w") as f:
            # 写入头部
            f.write("# Dify Plugin SDK Schema Documentation\n\n")

            schemas = list_schema_docs()

            # 构建类型到模式的映射
            for schema in schemas:
                self._type_to_schema[schema.cls] = schema
                self._types.add(schema.cls)

            # 预处理模式以收集字段描述
            self._preprocess_schemas(schemas)

            # 计算引用并构建引用图
            self._build_reference_graph(schemas)

            # 创建块
            self._create_blocks()

            # 生成目录
            f.write("## Table of Contents\n\n")
            hierarchy = self._organize_toc()

            def write_toc_item(node: tuple[type, list[Any]], indent: int = 0):
                """写入目录项

                Args:
                    node: 包含类型和子级的节点元组
                    indent: 缩进级别
                """
                type_, children = node
                schema = self._type_to_schema[type_]
                name = schema.name or type_.__name__
                f.write(f"{' ' * (indent * 2)}- [{name}](#{name.lower()})\n")
                for child in children:
                    write_toc_item(child, indent + 1)

            for node in hierarchy:
                write_toc_item(node)
            f.write("\n")

            # 为每个块生成文档
            for block in self._blocks:
                for type_ in block:
                    self._write_schema_doc(f, type_)

    def _preprocess_schemas(self, schemas: list) -> None:
        """预处理模式以收集字段描述并合并重复项

        Args:
            schemas: 模式列表
        """
        # 第一遍：收集所有字段描述
        for schema in schemas:
            cls = schema.cls
            if not issubclass(cls, BaseModel):
                continue

            # 存储模式描述
            if cls not in self._schema_descriptions or len(schema.description) > len(
                self._schema_descriptions[cls]
            ):
                self._schema_descriptions[cls] = schema.description

            # 存储字段描述
            outside_reference_fields = (
                getattr(schema, "outside_reference_fields", {}) or {}
            )
            for field_name, field_info in cls.model_fields.items():
                field_type = field_info.annotation
                if field_type is None:
                    continue

                # 对于非外部引用的BaseModel类型，我们将单独记录它们
                if (
                    isinstance(field_type, type)
                    and issubclass(field_type, BaseModel)
                    and field_name not in outside_reference_fields
                ):
                    continue

                key = (cls, field_name)
                description = field_info.description or ""

                # 处理动态字段
                if (
                    hasattr(schema, "dynamic_fields")
                    and schema.dynamic_fields
                    and field_name in schema.dynamic_fields
                ):
                    description = schema.dynamic_fields[field_name]

                # 对于外部引用字段，将引用信息附加到描述中
                if field_name in outside_reference_fields:
                    referenced_type = outside_reference_fields[field_name]
                    referenced_schema = self._type_to_schema.get(referenced_type)
                    schema_name = (
                        referenced_schema.name
                        if referenced_schema
                        else referenced_type.__name__
                    )
                    if description:
                        description = f"{description} "
                        f"(将作为 [{schema_name}](#{schema_name.lower()}) 加载的yaml文件路径)"
                    else:
                        description = f"将作为 [{schema_name}](#{schema_name.lower()}) 加载的yaml文件路径"

                # 存储最详细的描述
                if key not in self._field_descriptions or len(description) > len(
                    self._field_descriptions[key]
                ):
                    self._field_descriptions[key] = description

    def _extract_referenced_types(self, field_type):
        """递归提取字段类型中引用的所有BaseModel和Enum类型

        Args:
            field_type: 字段类型

        Returns:
            引用类型的集合
        """
        referenced = set()
        if field_type is None:
            return referenced

        # 处理直接类型引用（BaseModel和Enum）
        if isinstance(field_type, type):
            if issubclass(field_type, BaseModel | Enum):
                referenced.add(field_type)
        # 处理泛型类型（List、Dict、Union等）
        elif (
            hasattr(field_type, "__origin__") and field_type.__origin__ == Union
        ) or hasattr(field_type, "__args__"):
            # 处理Union类型
            for arg in field_type.__args__:
                referenced.update(self._extract_referenced_types(arg))

        return referenced

    def _build_reference_graph(self, schemas: list) -> None:
        """构建类型之间的引用图（递归处理所有嵌套类型）

        Args:
            schemas: 模式列表
        """
        for schema in schemas:
            cls = schema.cls
            if not issubclass(cls, BaseModel):
                continue

            # 计算字段中的引用
            for field_name, field_info in cls.model_fields.items():
                field_type = field_info.annotation
                if field_type is None:
                    continue

                # 处理外部引用字段
                outside_reference_fields = (
                    getattr(schema, "outside_reference_fields", {}) or {}
                )
                if field_name in outside_reference_fields:
                    referenced_type = outside_reference_fields[field_name]
                    # 将引用添加到图中
                    self._reference_graph[cls].add(referenced_type)
                    self._reference_counts[referenced_type] = (
                        self._reference_counts.get(referenced_type, 0) + 1
                    )
                    continue

                for ref_type in self._extract_referenced_types(field_type):
                    if ref_type != cls:  # 避免自引用
                        self._reference_graph[cls].add(ref_type)
                        self._reference_counts[ref_type] = (
                            self._reference_counts.get(ref_type, 0) + 1
                        )

    def _create_blocks(self) -> None:
        """为所有类型创建文档块"""
        # 第一遍：为每个类型分配块索引
        for type_ in self._types:
            if type_ not in self._type_blocks:
                # 如果类型标记为top=True，分配到块0
                if hasattr(type_, "__schema_docs__") and any(
                    doc.top for doc in type_.__schema_docs__
                ):
                    self._type_blocks[type_] = 0
                else:
                    # 分配到新块，从1开始
                    self._type_blocks[type_] = len(self._type_blocks) + 1

        # 第二遍：创建实际的块
        # 初始化足够的空列表
        max_block_index = max(self._type_blocks.values()) if self._type_blocks else 0
        self._blocks = [[] for _ in range(max_block_index + 1)]

        for type_, block_index in self._type_blocks.items():
            self._blocks[block_index].append(type_)

        # 排序块以确保顶级类型在前面
        # 只有当块0包含顶级类型时才将其移到前面
        if (
            self._blocks
            and self._blocks[0]
            and any(
                hasattr(t, "__schema_docs__")
                and any(doc.top for doc in t.__schema_docs__)
                for t in self._blocks[0]
            )
        ):
            top_block = self._blocks[0]
            self._blocks.sort(key=lambda block: 0 if block is top_block else 1)

    def _is_container_type(self, field_type: Any, container_types=(list, set)) -> bool:
        """检查字段类型是否为容器类型（list、set等）

        Args:
            field_type: 字段类型
            container_types: 容器类型元组

        Returns:
            是否为容器类型
        """
        try:
            return (
                hasattr(field_type, "__origin__")
                and isinstance(getattr(field_type, "__origin__", None), type)
                and getattr(field_type, "__origin__", None) in container_types
            )
        except Exception:
            return False

    def _get_container_name(self, field_type: Any) -> str:
        """获取容器类型的名称

        Args:
            field_type: 字段类型

        Returns:
            容器类型名称
        """
        try:
            origin = getattr(field_type, "__origin__", None)
            return origin.__name__ if origin else str(field_type)
        except Exception:
            return str(field_type)

    def _write_schema_doc(self, f, type_) -> None:
        """为单个模式写入文档

        Args:
            f: 文件对象
            type_: 类型对象
        """
        schema = self._type_to_schema[type_]
        name = schema.name or type_.__name__

        f.write(f"## {name}\n\n")

        # 写入描述
        description = self._schema_descriptions.get(type_, "")
        f.write(f"{description}\n\n")

        if issubclass(type_, BaseModel):
            f.write("### Fields\n\n")
            f.write("| Name | Type | Description | Default | Extra |\n")
            f.write("|------|------|-------------|---------|---------|\n")

            # 跟踪已处理的字段以避免重复
            processed_fields = set()
            ignore_fields = set(getattr(schema, "ignore_fields", []) or [])
            outside_reference_fields = (
                getattr(schema, "outside_reference_fields", {}) or {}
            )

            for field_name, field_info in type_.model_fields.items():
                if field_name in ignore_fields:
                    continue
                field_type = field_info.annotation
                if field_type is None:
                    continue

                # 如果我们已经处理过这个字段类型，跳过
                if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                    if field_type in self._processed_field_types:
                        continue
                    self._processed_field_types.add(field_type)

                # 如果我们已经处理过这个字段，跳过
                field_key = (field_type, field_name)
                if field_key in processed_fields:
                    continue
                processed_fields.add(field_key)

                # 获取最详细的描述
                description = self._field_descriptions.get(
                    (type_, field_name), field_info.description or ""
                )

                # 格式化类型名称
                type_name = self._format_type_name(field_type)

                # 处理外部引用字段
                if field_name in outside_reference_fields:
                    if self._is_container_type(field_type):
                        type_name = f"{self._get_container_name(field_type)}[str]"
                    else:
                        type_name = "str"

                # 获取字段元数据
                default = field_info.default
                # 用户友好的默认值
                if str(default) == "PydanticUndefined":
                    default = ""

                # 获取模式（如果存在）（健壮）
                extra = ""
                if hasattr(field_info, "metadata"):
                    for value in field_info.metadata:
                        extra += f"{value} "

                f.write(
                    f"| {field_name} | {type_name} | {description} | {default} | {extra} |\n"
                )

            f.write("\n")

        elif issubclass(type_, Enum):
            f.write("### Values\n\n")
            for member in type_:
                f.write(f"- `{member.name}`: {member.value}\n")
            f.write("\n")

    def _format_type_name(self, field_type: Any) -> str:
        """格式化类型名称以供显示，处理复杂类型和引用

        对于BaseModel和Enum类型，如果可用则使用其模式名称。
        对于容器类型（list、dict等），递归格式化其类型参数。

        Args:
            field_type: 字段类型

        Returns:
            格式化的类型名称字符串
        """
        if field_type is None:
            return "Any"

        if isinstance(field_type, type):
            if issubclass(field_type, BaseModel | Enum):
                # 如果可用，使用模式名称
                schema = self._type_to_schema.get(field_type)
                name = schema.name if schema else field_type.__name__
                return f"[{name}](#{name.lower()})"
            return field_type.__name__

        if hasattr(field_type, "__origin__") and hasattr(field_type, "__args__"):
            origin = field_type.__origin__
            if origin in (list, set):
                inner_type = self._format_type_name(field_type.__args__[0])
                return f"{origin.__name__}[{inner_type}]"
            elif origin is dict:
                key_type = self._format_type_name(field_type.__args__[0])
                value_type = self._format_type_name(field_type.__args__[1])
                return f"dict[{key_type}, {value_type}]"
            elif origin is tuple:
                types = [self._format_type_name(arg) for arg in field_type.__args__]
                return f"tuple[{', '.join(types)}]"
            elif origin is Union:
                types = [self._format_type_name(arg) for arg in field_type.__args__]
                return f"Union[{', '.join(types)}]"

        return str(field_type)
