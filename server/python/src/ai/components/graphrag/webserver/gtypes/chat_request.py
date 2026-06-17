"""GraphRAG Web 服务器请求参数类型定义。

GraphRAG Web Server request parameter type definitions.
"""

from enum import Enum

from fastapi import Body
from pydantic import BaseModel

import ai.components.graphrag.config.defaults as defs
from ai.components.graphrag.query.__main__ import SearchType


class IndexAction(Enum):
    """
    索引操作方式。

    Index action types.
    """

    UPDATE = "update"
    UPDATE_WITH_PROMPT = "update_with_prompt"
    RECREATE = "recreate"

    def __str__(self):
        """
        返回枚举值的字符串表示。

        Return the string representation of the enum value.
        """
        return self.value


class BaseIndexParam(BaseModel):
    """
    基础索引参数类。

    Base index parameter class.
    """

    namespace: str = Body(..., description="知识库命名空间")
    code: str = Body(..., description="知识库编码")
    filename: str = Body(..., description="知识库文件名")


class SearchParam(BaseIndexParam):
    """
    搜索参数类。

    Search parameter class.
    """

    query: str = Body(..., description="问题")
    query_method: str = Body(
        SearchType.LOCAL.value, description="查询方式，可选值：global，local"
    )
    community_level: int = 2
    min_score: float = Body(defs.RERANKER_MIN_SCORE, description="最低分数")
    response_type: str = Body(
        "多段落，markdown格式",
        description="返回类型: 多段落，markdown格式, Single Paragraph, Single Sentence, List of 3-7 Points, Single Page, Multi-Page Report. 默认为：Multiple Paragraphs",
    )


class IndexData(BaseIndexParam):
    """
    索引数据类。

    Index data class.
    """

    class Data(BaseModel):
        """
        数据模型类。

        Data model class.
        """

        title: str = Body(None, description="实体/社区报告中的标题")
        type: str = Body(None, description="实体类型")
        degree: int = Body(None, description="实体排名")
        description: str = Body(None, description="实体/实体关系中的描述")
        source: str = Body(None, description="实体关系中的原实体")
        target: str = Body(None, description="实体关系中的目标实体")
        weight: int = Body(None, description="实体关系中的权重")
        rank: int = Body(None, description="实体关系/社区报告中的排名")
        id: str = Body(None, description="实体/实体关系/社区报告中的id，用于删除更新")
        summary: str = Body(None, description="社区报告中的摘要")
        full_content: str = Body(None, description="社区报告中的描述")
        community: str = Body("1", description="实体/社区报告中的community，默认1")
        level: int = Body(1, description="实体/社区报告中的级别，默认1")
        custom_add: str = Body(None, description="实体/实体关系/社区报告中的新建标识")
        custom_update: str = Body(
            None, description="实体/实体关系/社区报告中的修改标识"
        )

    datatype: str = Body(
        ..., description="数据类型，可选值：entities，reports，relationships"
    )
    data: Data = Body(..., description="数据对象")


class GraphJsonParam(BaseIndexParam):
    """
    图 JSON 参数类。

    Graph JSON parameter class.
    """


class GraphReferenceParam(BaseIndexParam):
    """
    图引用参数类。

    Graph reference parameter class.
    """

    datatype: str = Body(
        ...,
        description="数据类型，可选值：entities，sources，reports，relationships，prompts",
    )
    id: str = Body(
        None,
        description="数据ID, 与ids二选一, 如果id参数有值，则忽略ids参数。此处返回一个实体对象",
    )
    ids: list[str] = Body(
        None,
        description="数据IDS, 与id二选一, 如果id参数有值，则忽略ids参数。此处返回实体对象数组",
    )
    response_type: str = Body("json", description="返回类型: json, html. 默认为：json")


class TaskQueryParam(BaseModel):
    """
    任务查询参数类。

    Task query parameter class.
    """

    taskId: str = Body(..., description="任务ID")


class TaskStopParam(BaseModel):
    """
    任务停止参数类。

    Task stop parameter class.
    """

    taskId: str = Body(..., description="任务ID")


class IndexParam(BaseIndexParam):
    """
    索引参数类。

    Index parameter class.
    """

    docs: list[str] = None
    file_url: str = None
    action: IndexAction = IndexAction.UPDATE


class IndexDeleteParam(BaseIndexParam):
    """
    索引删除参数类。

    Index delete parameter class.
    """


class IndexCheckParam(BaseIndexParam):
    """
    索引检查参数类。

    Index check parameter class.
    """


class PromptTuneParam(BaseIndexParam):
    """
    提示词调优参数类。

    Prompt tuning parameter class.
    """

    docs: list[str] = None
    file_url: str = None


class PromptListParam(BaseIndexParam):
    """
    提示词列表参数类。

    Prompt list parameter class.
    """


class PromptUpdateParam(BaseIndexParam):
    """
    提示词更新参数类。

    Prompt update parameter class.
    """

    type: str = Body(
        ...,
        description="类型，可选值：community_report，entity_extraction，summarize_descriptions",
    )
    content: str = Body(..., description="内容")
