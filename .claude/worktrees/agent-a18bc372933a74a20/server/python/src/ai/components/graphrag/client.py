"""GraphRAG 客户端 — 调用本地 GraphRAG 服务（非 HTTP）。"""

import threading

from fastapi import Body
from loguru import logger
from pydantic import BaseModel

_logger = logger.bind(name=__name__)


class GraphData(BaseModel):
    """封装组件图谱检索增强生成中的GraphData逻辑。"""

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
    custom_update: str = Body(None, description="实体/实体关系/社区报告中的修改标识")


class GraphRAGClient:
    """GraphRAG 客户端 — 调用本地服务"""

    def __init__(self):
        """初始化实例。"""
        pass

    async def create_index_build_task(
        self, namespace: str, kb_code: str, filename: str, docs: list[str]
    ) -> dict:
        """
        创建索引构建任务（本地调用）

        Args:
            namespace: 命名空间（dataset_id）
            kb_code: 知识库编码
            filename: 文件名
            docs: 分段内容列表

        Returns:
            Dict: 任务状态
        """
        try:
            from ai.components.graphrag.webserver.gtypes.chat_request import (
                IndexAction,
                IndexParam,
            )
            from ai.components.graphrag.webserver.main import background_task, init
            from ai.components.graphrag.webserver.task.task import task_factory

            # 创建任务
            task = task_factory.create()
            task.ext_info(
                {
                    "namespace": namespace,
                    "code": kb_code,
                    "filename": filename,
                }
            )

            # 构建请求参数
            request = IndexParam(
                namespace=namespace,
                code=kb_code,
                filename=filename,
                docs=docs,
                action=IndexAction.UPDATE,
            )

            # 初始化输入文件
            init(request, task)

            # 启动后台线程执行索引构建
            t = threading.Thread(
                target=lambda: background_task(request, task),
                name=f"graphrag-index-{task.taskId}",
            )
            t.start()
            task_factory.set_thread(t, task)

            _logger.info(
                f"GraphRAG 索引任务已创建: task_id={task.taskId}, "
                f"namespace={namespace}, docs_count={len(docs)}"
            )

            return {
                "task_id": task.taskId,
                "status": task.status,
                "log": task.log,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "ext_info": getattr(task, "_ext_info", {}),
                "progress": task.progress,
                "update_time": task.update_time,
            }

        except Exception:
            _logger.exception("创建 GraphRAG 索引任务失败")
            return {
                "task_id": None,
                "status": "api_failed",
                "log": "",
            }

    async def query_index_build_task(self, task_id: str) -> dict | None:
        """
        查询索引构建任务状态

        Args:
            task_id: 索引任务ID

        Returns:
            Dict: 任务状态
        """
        try:
            from ai.components.graphrag.webserver.task.task import task_factory

            task = task_factory.get(task_id)
            if not task:
                _logger.warning(f"GraphRAG 任务不存在: task_id={task_id}")
                return None

            return {
                "task_id": task.taskId,
                "status": task.status,
                "log": task.log,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "ext_info": getattr(task, "_ext_info", {}),
                "progress": task.progress,
                "update_time": task.update_time,
            }

        except Exception:
            _logger.exception(f"查询 GraphRAG 任务失败: task_id={task_id}")
            return {"status": "retry"}

    async def search_graph_references(
        self,
        namespace: str,
        kb_code: str,
        filename: str,
        datatype: str,
        id: str | None,
        ids: list[str] | None,
        _response_type: str = "json",
    ) -> list[dict] | None:
        """
        查询图谱引用数据（实体、关系、社区报告等）

        Args:
            namespace: 命名空间
            kb_code: 知识库编码
            filename: 文件名称
            datatype: 数据类型 (entities, relationships, reports)
            id: 数据ID
            ids: 数据ID列表
            response_type: 返回类型

        Returns:
            数据列表
        """
        try:
            from ai.components.graphrag.webserver.service.indexdata import (
                get_index_data,
            )

            # 构建 row_id 参数
            row_id = None
            if id:
                row_id = id
            elif ids:
                row_id = ",".join(ids)

            result = await get_index_data(
                namespace=namespace,
                code=kb_code,
                filename=filename,
                datatype=datatype,
                row_id=row_id,
            )

            # 将结果转换为字典列表
            return [
                item.model_dump() if hasattr(item, "model_dump") else dict(item)
                for item in result
            ]

        except Exception:
            _logger.exception("查询图谱引用数据失败")
            return None

    async def search_graph_json(
        self, namespace: str, kb_code: str, filename: str
    ) -> str | None:
        """
        查询图谱 JSON 数据

        Args:
            namespace: 命名空间
            kb_code: 知识库编码
            filename: 文件名称

        Returns:
            图谱 JSON 数据
        """
        try:
            import json
            from io import BytesIO

            from ai.components.graphrag.webserver.utils.consts import ROOT_PATH
            from ai.components.graphrag.webserver.utils.storage_util import (
                ConfigType,
                StorageObject,
            )

            storage = StorageObject(namespace, kb_code, filename, ConfigType.storage)
            file_content = storage.get(
                filename="summarized_graph.graphml", as_bytes=True
            )

            # 动态导入转换脚本
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                "graphml_to_json", f"{ROOT_PATH}/scripts/graphml_to_json.py"
            )
            if spec and spec.loader:
                graphml_to_json = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(graphml_to_json)
                result = graphml_to_json.to_json(BytesIO(file_content))
            else:
                raise ImportError("无法加载 graphml_to_json 模块")

            return json.dumps(result, ensure_ascii=False)

        except Exception:
            _logger.exception("查询图谱 JSON 失败")
            return None

    async def search(
        self,
        namespace: str,
        kb_code: str,
        filename: str,
        query: str,
        query_method: str,
        score_threshold: float,
    ) -> str | None:
        """
        搜索

        Args:
            namespace: 命名空间
            kb_code: 知识库编码
            filename: 文件名
            query: 查询文本
            query_method: 查询方法 (local/global)
            score_threshold: 分数阈值

        Returns:
            搜索结果
        """
        try:
            from ai.components.graphrag.webserver.service.search import (
                run_global_search,
                run_local_search,
            )

            community_level = 2
            response_type = "Multiple Paragraphs"

            if query_method == "local":
                result = await run_local_search(
                    namespace=namespace,
                    code=kb_code,
                    filename=filename,
                    community_level=community_level,
                    response_type=response_type,
                    query=query,
                    min_score=score_threshold,
                )
            elif query_method == "global":
                result = await run_global_search(
                    namespace=namespace,
                    code=kb_code,
                    filename=filename,
                    community_level=community_level,
                    response_type=response_type,
                    query=query,
                )
            else:
                raise ValueError(f"不支持的查询方法: {query_method}")

            return result.response if hasattr(result, "response") else str(result)

        except Exception:
            _logger.exception("搜索失败")
            return None

    async def handle_graph_index_data(
        self,
        namespace: str,
        kb_code: str,
        filename: str,
        datatype: str,
        data: GraphData,
        option: str,
    ) -> dict | None:
        """
        处理图谱索引数据（增删改查）

        Args:
            namespace: 命名空间
            kb_code: 知识库编码
            filename: 文件名称
            datatype: 数据类型
            data: 操作的数据对象
            option: 操作类型 (add, update, delete, get_by_id)

        Returns:
            操作结果
        """
        try:
            import os

            from ai.components.graphrag.webserver.gtypes.chat_request import IndexData
            from ai.components.graphrag.webserver.service.indexdata import (
                index_data_add,
                index_data_delete,
                index_data_get_by_id,
                index_data_update,
            )
            from ai.components.graphrag.webserver.utils.rag_util import (
                build_root_path,
            )

            root_dir = build_root_path(namespace, kb_code, filename)
            data_dir = os.path.join(root_dir, "output", "artifacts")

            # 构建 IndexData 对象
            index_data = IndexData(
                namespace=namespace,
                code=kb_code,
                filename=filename,
                datatype=datatype,
                data=IndexData.Data(**data.model_dump(exclude_none=True)),
            )

            if option == "add":
                result = await index_data_add(data_dir, datatype, index_data.data)
            elif option == "update":
                result = await index_data_update(data_dir, datatype, index_data.data)
            elif option == "delete":
                result = await index_data_delete(data_dir, datatype, index_data.data)
            elif option == "get_by_id":
                result = await index_data_get_by_id(data_dir, datatype, index_data.data)
            else:
                raise ValueError(f"不支持的操作类型: {option}")

            return {"success": True, "result": result}

        except Exception:
            _logger.exception("处理图谱索引数据失败")
            return {"success": False, "error": ""}

    async def stop_graph_task(self, task_id: str) -> dict | None:
        """
        终止索引任务

        Args:
            task_id: 索引任务ID

        Returns:
            任务状态
        """
        try:
            from ai.components.graphrag.webserver.task.task import task_factory

            task = task_factory.get(task_id)
            if not task:
                _logger.warning(f"GraphRAG 任务不存在: task_id={task_id}")
                return {
                    "task_id": None,
                    "status": "api_failed",
                    "log": "任务不存在",
                }

            # 标记为取消中
            task.cancelling("用户请求取消")

            return {
                "task_id": task.taskId,
                "status": task.status,
                "log": task.log,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "ext_info": getattr(task, "_ext_info", {}),
                "progress": task.progress,
                "update_time": task.update_time,
            }

        except Exception as e:
            _logger.exception(f"终止 GraphRAG 任务失败: task_id={task_id}")
            return {
                "task_id": None,
                "status": "api_failed",
                "log": str(e),
            }
