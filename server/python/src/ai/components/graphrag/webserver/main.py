"""GraphRAG Web 服务器。

GraphRAG Web Server.

这个模块提供了一个 FastAPI Web 服务器,用于 GraphRAG 应用程序,处理各种端点。
This module provides a FastAPI web server for GraphRAG applications, handling various endpoints.
"""

import asyncio
import json
import logging
import os
import threading
import time
from io import BytesIO

from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Template

from ai.components.graphrag.webserver.gtypes.chat_request import (
    GraphJsonParam,
    GraphReferenceParam,
    IndexAction,
    IndexCheckParam,
    IndexData,
    IndexDeleteParam,
    IndexParam,
    PromptListParam,
    PromptTuneParam,
    PromptUpdateParam,
    SearchParam,
    TaskQueryParam,
    TaskStopParam,
)
from ai.components.graphrag.webserver.gtypes.chat_result import SearchResult
from ai.components.graphrag.webserver.task.task import Task, task_factory
from ai.components.graphrag.webserver.task.task_exception import TaskStopError
from ai.components.graphrag.webserver.utils.consts import DOC_TYPE_DOC_LIST, ROOT_PATH
from ai.components.graphrag.webserver.utils.rag_util import build_root_path

logger = logging.getLogger(__name__)

logger.info(
    "GraphRAG Web Server initializing, time: %s",
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())),
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Web 服务器启动事件处理。

    Web server startup event handler.
    """
    logger.info("webserver startup event triggered.")
    from webserver import START_TIME

    from ai.components.graphrag.index.__main__ import run_index
    from ai.components.graphrag.prompt_tune.__main__ import run_prompt_tune
    from ai.components.graphrag.query.__main__ import run_search

    logger.info(
        "webserver startup complete, cost: %s s, %s, %s, %s",
        time.time() - START_TIME,
        run_search.__name__,
        run_index.__name__,
        run_prompt_tune.__name__,
    )


@app.get("/")
async def index():
    """
    首页路由,返回 HTML 页面。

    Index route, returns HTML page.
    """
    html_file_path = os.path.join(ROOT_PATH, "webserver", "templates", "index.html")
    with open(html_file_path, encoding="utf-8") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.post("/v1/graphrag/prompt_tune", summary="生成prompt")
async def graphrag_prompt_tune(request: PromptTuneParam):
    """
    处理graphrag_prompt_tune。

    Args:
        request (PromptTuneParam): request 参数。

    Returns:
        处理结果。
    """
    task: Task = task_factory.create()

    try:
        from ai.components.graphrag.webserver.service.prompt_tune import (
            async_run_prompt_tune,
        )

        override = True

        if request.docs is None and request.file_url is None:
            override = False

        index_param = IndexParam(
            namespace=request.namespace, code=request.code, filename=request.filename
        )

        index_param.docs = request.docs
        index_param.file_url = request.file_url

        init(index_param, task)

        root_dir = build_root_path(request.namespace, request.code, request.filename)

        input_dir = root_dir + "/input"
        file_path = os.path.join(input_dir, _build_filename(request.filename))
        if not os.path.exists(file_path):
            raise ValueError("源文档未找到，请先初始化索引")

        start_time = int(round(time.time() * 1000))

        task_factory.set_thread(threading.current_thread(), task)  # 记录线程到任务中

        # 运行提示词调优
        await async_run_prompt_tune(request, task)

        end_time = int(round(time.time() * 1000))

        task.done("ok")

        return JSONResponse(
            content=jsonable_encoder(
                {"success": True, "time(ms)": end_time - start_time}
            )
        )
    except Exception as e:
        task.fail(str(e))
        logger.exception("创建索引失败")
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        task_factory.delete(task.taskId, True)


def _build_filename(filename: str) -> str:
    """
    构建文件名,添加 .dtxt 扩展名。

    Build filename by adding .dtxt extension.

    参数 Parameters
    ----------
    filename : str
        原始文件名。Original filename.

    返回 Returns
    -------
    str
        带扩展名的文件名。Filename with extension.
    """
    return f"{filename}.dtxt"


@app.post("/v1/graphrag/prompt_list", summary="查询prompt列表")
async def graphrag_prompt_list(request: PromptListParam):
    """
    处理graphrag_prompt。

    Args:
        request (PromptListParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        root_dir = build_root_path(request.namespace, request.code, request.filename)
        data_dir = os.path.join(root_dir, "prompts")

        result = [
            {"name": "社区报告", "type": "community_report", "content": ""},
            {"name": "实体抽取", "type": "entity_extraction", "content": ""},
            {"name": "总结描述", "type": "summarize_descriptions", "content": ""},
        ]

        for e in result:
            data_path = os.path.join(data_dir, f"{e['type']}.txt")
            if not os.path.exists(data_path):
                continue
            with open(data_path) as file:
                _content = file.read()
                e["content"] = _content

        return JSONResponse(content=jsonable_encoder(result))

    except Exception as e:
        logger.exception("读取 prompt 信息失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/graphrag/prompt_update", summary="编辑prompt")
async def graphrag_prompt_update(request: PromptUpdateParam):
    """
    处理graphrag_prompt。

    Args:
        request (PromptUpdateParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        if request.type not in [
            "community_report",
            "entity_extraction",
            "summarize_descriptions",
        ]:
            raise ValueError(f"{request.type} not found")

        root_dir = build_root_path(request.namespace, request.code, request.filename)
        data_dir = os.path.join(root_dir, "prompts")

        data_path = os.path.join(data_dir, f"{request.type}.txt")
        # 判断data_path是否存在
        if os.path.exists(data_path):
            with open(data_path, "w") as file:
                file.write(request.content)
        else:
            raise ValueError("索引或者prompt不存在，请先生成prompt")

        return JSONResponse(content=jsonable_encoder({"success": True}))

    except Exception as e:
        logger.exception("更新 prompt 失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/graphrag/index", summary="创建索引")
async def graphrag_index(request: IndexParam):
    # 判断是否有任务正在运行,目前只允许运行一个任务
    """
    处理graphrag_index。

    Args:
        request (IndexParam): request 参数。

    Returns:
        处理结果。
    """
    running_tasks = task_factory.list("running")
    if len(running_tasks) > 0:
        print(f"running_tasks: {[task.taskId for task in running_tasks]}")
        raise HTTPException(status_code=400, detail="当前有任务正在运行，请稍后再试(0)")

    running_tasks = task_factory.list("cancelling")
    if len(running_tasks) > 0:
        print(f"running_tasks: {[task.taskId for task in running_tasks]}")
        raise HTTPException(status_code=400, detail="当前有任务正在运行，请稍后再试(1)")

    abnormal_task = task_factory.list_abnormal_task()
    if len(abnormal_task) > 0:
        print(f"abnormal_task: {[task.taskId for task in abnormal_task]}")
        raise HTTPException(
            status_code=400, detail="当前有任务正在运行，请稍后再试(2)！！"
        )

    # 清理过期的任务
    task_factory.clean()

    # 创建新的任务
    task: Task = task_factory.create()
    try:
        task.ext_info(
            {
                "namespace": request.namespace,
                "code": request.code,
                "filename": request.filename,
            }
        )

        if request.action == IndexAction.RECREATE:
            # 删除原来的索引
            await graphrag_index_delete(
                IndexDeleteParam(
                    namespace=request.namespace,
                    code=request.code,
                    filename=request.filename,
                )
            )

        init(request, task)

        run_in_background(request, task)

        return JSONResponse(content=jsonable_encoder(task.to_task_result()))
    except Exception as e:
        task.fail(f"error: {e!s}")
        logger.exception("索引任务执行失败")
        return JSONResponse(content=jsonable_encoder(task.to_task_result()))


@app.post("/v1/graphrag/index/delete", summary="删除索引")
async def graphrag_index_delete(request: IndexDeleteParam):
    """
    删除索引,将索引目录移动到备份位置。

    Delete index by moving the index directory to a backup location.
    """
    root_dir = build_root_path(request.namespace, request.code, request.filename)

    print(f"try delete index: {root_dir}")
    if os.path.exists(root_dir):
        import shutil

        bak_dir = root_dir + f".del.{time.strftime('%Y%m%d_%H%M%S')}"
        print(f"move index to {bak_dir}")
        shutil.move(root_dir, bak_dir)

        success = True
    else:
        success = False
    return JSONResponse(content=jsonable_encoder({"delete": success}))


@app.post("/v1/graphrag/index/check", summary="检查索引是否存在")
async def graphrag_index_check(request: IndexCheckParam):
    """
    检查索引是否存在,通过检查关键文件判断。

    Check if index exists by verifying key files.
    """
    root_dir = build_root_path(request.namespace, request.code, request.filename)
    prompts_dir = os.path.join("prompts")
    community_report_path = os.path.join(prompts_dir, "community_report.txt")

    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    # storage = StorageObject(request.namespace, request.code, request.filename, ConfigType.prompt)
    # community_report_exists = storage.exists(community_report_path)

    storage = StorageObject(
        request.namespace, request.code, request.filename, ConfigType.storage
    )
    create_final_community_reports_exists = storage.exists(
        "create_final_community_reports.parquet"
    )

    if create_final_community_reports_exists:
        # 目前只是判断输入文件,一个prompt,一个生成物 是否存在来判断该索引之前是否执行过
        print(f"index exists: {root_dir}")
        exists = True
    else:
        print(f"index not exists: {root_dir}")
        exists = False
    return JSONResponse(content=jsonable_encoder({"exists": exists}))


def background_task(request: IndexParam, task: Task):
    """
    后台任务执行函数,运行提示词调优和索引创建。

    Background task execution function for running prompt tuning and index creation.

    参数 Parameters
    ----------
    request : IndexParam
        索引参数。Index parameters.
    task : Task
        任务对象。Task object.
    """
    print("Running in the background...")

    try:
        from ai.components.graphrag.webserver.service.index import run_index
        from ai.components.graphrag.webserver.service.prompt_tune import (
            run_prompt_tune,
        )

        root_dir = build_root_path(request.namespace, request.code, request.filename)

        if request.action == IndexAction.UPDATE_WITH_PROMPT:
            # 强制执行prompt_tune
            prompt_tune = True
            print("强制执行prompt_tune")
        else:
            # 判断是否需要执行prompt_tune
            prompts_dir = os.path.join(root_dir, "prompts")
            community_report_path = os.path.join(prompts_dir, "community_report.txt")
            entity_extraction_pah = os.path.join(prompts_dir, "entity_extraction.txt")
            summarize_descriptions_path = os.path.join(
                prompts_dir, "summarize_descriptions.txt"
            )

            if (
                os.path.exists(community_report_path)
                and os.path.exists(entity_extraction_pah)
                and os.path.exists(summarize_descriptions_path)
            ):
                # 存在索引目录,则不需要进行prompt_tune
                prompt_tune = False
                print("不需要执行prompt_tune")
            else:
                # 不存在索引目录,则需要进行prompt_tune
                prompt_tune = True
                print("需要执行prompt_tune")

        if prompt_tune:
            # 运行提示词调优
            run_prompt_tune(
                PromptTuneParam(
                    namespace=request.namespace,
                    code=request.code,
                    filename=request.filename,
                ),
                task,
            )

        # 运行索引
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        run_index(request, task)
    except Exception as e:
        if task.is_done() or task.is_failed() or task.is_cancelled():
            # 如果任务已经完成,则不记录异常
            pass
        elif task.is_cancelling() and isinstance(e, TaskStopError):
            # 如果进来了这里,是因为生成提示词阶段被用户终止了该任务。如果是索引阶段,不会进来这里的
            task.cancelled(f"任务已取消：{e!s}")
        else:
            task.fail(f"任务失败(3)：{e!s}")

        logger.exception("索引初始化失败")
        raise e


def run_in_background(request: IndexParam, task: Task):
    """
    在后台线程中运行索引任务。

    Run index task in a background thread.

    参数 Parameters
    ----------
    request : IndexParam
        索引参数。Index parameters.
    task : Task
        任务对象。Task object.
    """
    t = threading.Thread(target=lambda: background_task(request, task))
    t.start()  # 启动线程
    task_factory.set_thread(t, task)  # 记录线程到任务中


def init(request: IndexParam, task: Task):
    """
    初始化工程,包括输入文件等。

    Initialize project, including input files.

    参数 Parameters
    ----------
    request : IndexParam
        请求参数。Request parameters.
    task : Task
        任务对象。Task object.

    说明 Notes
    -----
    如果覆盖,当里面的内容是一样的,会使用缓存,当里面的内容不一样的,会更新新的知识。
    注意:目前只会添加新的知识,旧的知识并不会删除掉。
    If overriding, cached data will be used when content is identical. When content differs,
    new knowledge will be added. Note: Currently only new knowledge is added, old knowledge
    is not removed.
    """
    root_dir = build_root_path(request.namespace, request.code, request.filename)
    input_dir = root_dir + "/input"

    filename = _build_filename(request.filename)

    file_path = os.path.join(input_dir, filename)

    task.add_log("初始化索引输入文件")

    # 创建相关目录
    os.makedirs(root_dir, exist_ok=True)
    os.makedirs(input_dir, exist_ok=True)

    if request.docs and len(request.docs) > 0:
        # 如果docs存在, 则将docs写入到input_dir目录中

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(DOC_TYPE_DOC_LIST + json.dumps(request.docs, ensure_ascii=False))

    elif request.file_url and len(request.file_url) > 0:
        # 如果docs不存在,则从文件url中获取
        # 下载文件到input_dir目录
        download_file(request.file_url, file_path)
    else:
        raise ValueError("docs or file_url must be set")

    # 上传到存储
    _upload_to_storage(request, filename, file_path)


def _upload_to_storage(request: IndexParam, filename: str, file_path: str):
    """
    上传文件到存储。

    Upload file to storage.

    参数 Parameters
    ----------
    request : IndexParam
        索引参数。Index parameters.
    filename : str
        文件名。Filename.
    file_path : str
        文件路径。File path.
    """
    from ai.components.graphrag.webserver.utils.storage_util import (
        ConfigType,
        StorageObject,
    )

    storage = StorageObject(
        request.namespace, request.code, request.filename, ConfigType.input
    )
    # 从 file_path 中提取文件名

    storage.upload(filename, file_path)


def download_file(url, file_path):
    """
    下载文件并保存到指定文件夹中,支持 HTTP 和本地文件。

    Download file and save to specified folder, supporting HTTP and local files.

    参数 Parameters
    ----------
    url : str
        文件的网络地址或本地路径。File URL or local path.
    file_path : str
        文件下载后保存的文件路径。File path for saving downloaded file.

    异常 Raises
    ------
    ValueError
        当路径包含非法字符时。When path contains illegal characters.
    Exception
        当文件下载失败或文件不存在时。When file download fails or file doesn't exist.
    """
    if url.startswith("http://") or url.startswith("https://"):
        # 下载文件
        import requests

        response = requests.get(url)

        # 检查请求是否成功
        if response.status_code == 200:
            # 将文件内容写入到文件中
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"文件已成功下载到 {file_path}")
        else:
            print(
                f"文件下载失败，状态码：{response.status_code}, 错误信息：{response.text}"
            )
            raise Exception(
                f"文件下载失败，状态码：{response.status_code}, 错误信息：{response.text}"
            )
    else:
        # 本地文件
        url = url.removeprefix("file://")
        ## 循环将img_path 中的.. 替换为空字符串,防止路径注入
        if url.find("..") != -1:
            print("img_path contains ..")
            raise ValueError(f"路径非法: {url}")
        if os.path.exists(url):
            import shutil

            shutil.copyfile(url, file_path)
            print(f"文件已成功复制到指定目录: {file_path}")
        else:
            raise Exception(f"文件不存在：{url}")


@app.post("/v1/graphrag/task_query", summary="查询任务")
async def graphrag_query_task(request: TaskQueryParam):
    """
    处理graphrag_query_task。

    Args:
        request (TaskQueryParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        task = task_factory.get(request.taskId)

        if task is None:
            # 如果未找到,则从磁盘中加载 todo
            raise ValueError(f"Task {request.taskId} not found")

        return JSONResponse(content=jsonable_encoder(task.to_task_result()))
    except Exception as e:
        logger.exception("查询任务失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/graphrag/task_list", summary="查询任务列表")
async def graphrag_list_task(status: str | None = None):
    """
    处理graphrag_task。

    Args:
        status (str | None): status 参数。

    Returns:
        处理结果。
    """
    try:
        return JSONResponse(content=jsonable_encoder(task_factory.list(status=status)))
    except Exception as e:
        logger.exception("查询任务列表失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/graphrag/task_list_running", summary="查询正在运行的索引任务")
async def graphrag_task_running_check():
    """
    处理graphrag_task_running_check。

    Returns:
        处理结果。
    """
    try:
        # 判断是否有任务正在运行,目前只允许运行一个任务
        running_tasks = task_factory.list("running")
        cancelling_tasks = task_factory.list("cancelling")
        return JSONResponse(
            content=jsonable_encoder(
                {
                    "running": running_tasks,
                    "cancelling": cancelling_tasks,
                    "total": len(running_tasks) + len(cancelling_tasks),
                }
            )
        )
    except Exception as e:
        logger.exception("查询正在运行的任务失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/graphrag/task_stop", summary="终止任务")
async def graphrag_stop_task(request: TaskStopParam):
    """
    处理graphrag_stop_task。

    Args:
        request (TaskStopParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        task = task_factory.get(request.taskId)

        if task is None:
            # 如果未找到,则从磁盘中加载 todo
            raise ValueError(f"Task {request.taskId} not found")

        if task.is_running():
            if task.thread and task.thread.is_alive():
                # 终止任务,设置状态,后台任务会判断该状态进行任务的终止
                task.cancelling("手工终止任务，任务取消中...")
            else:
                # 任务已经终止,直接设置状态为cancelled
                task.cancelled("任务已取消")

            return JSONResponse(content=jsonable_encoder(task.to_task_result()))

        raise ValueError(f"Task {request.taskId} is not running, status: {task.status}")
    except Exception as e:
        logger.exception("终止任务失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/v1/graphrag/list_abnormal_task", summary="查询异常任务列表")
async def graphrag_list_abnormal_task():
    """
    处理graphrag_abnormal_task。

    Returns:
        处理结果。
    """
    try:
        return JSONResponse(content=jsonable_encoder(task_factory.list_abnormal_task()))
    except Exception as e:
        logger.exception("查询异常任务列表失败")
        raise HTTPException(status_code=400, detail=str(e))


async def _check_index_exist(namespace: str, code: str, filename: str):
    """
    检查索引是否存在,如果不存在则抛出异常。

    Check if index exists, raise exception if not.

    参数 Parameters
    ----------
    namespace : str
        命名空间。Namespace.
    code : str
        代码标识。Code identifier.
    filename : str
        文件名。Filename.

    异常 Raises
    ------
    ValueError
        当索引不存在时。When index doesn't exist.
    """
    response: JSONResponse = await graphrag_index_check(
        IndexCheckParam(namespace=namespace, code=code, filename=filename)
    )

    if response.body:
        body: dict = json.loads(response.body)
        if not body.get("exists", False):
            # 索引不存在,则提示用户不存在
            raise ValueError("索引不存在，请先创建索引")


@app.post("/v1/graphrag/graph_json", summary="查询图json")
async def get_graph_json(request: GraphJsonParam):
    """
    获取graph_json。

    Args:
        request (GraphJsonParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        await _check_index_exist(request.namespace, request.code, request.filename)

        from ai.components.graphrag.webserver.utils.storage_util import (
            ConfigType,
            StorageObject,
        )

        storage = StorageObject(
            request.namespace, request.code, request.filename, ConfigType.storage
        )
        file_content = storage.get(filename="summarized_graph.graphml", as_bytes=True)

        from scripts.graphml_to_json import to_json

        out = to_json(BytesIO(file_content))  # type: ignore

        return JSONResponse(content=jsonable_encoder(out))
    except Exception as e:
        logger.exception("查看数据表详情失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/graphrag/references", summary="查询索引数据")
async def get_reference(request: GraphReferenceParam):
    """
    获取reference。

    Args:
        request (GraphReferenceParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        datatype = request.datatype

        if datatype not in [
            "entities",
            "claims",
            "sources",
            "reports",
            "relationships",
        ]:
            raise ValueError(f"{datatype} not found")

        await _check_index_exist(request.namespace, request.code, request.filename)

        from ai.components.graphrag.webserver.service.indexdata import get_index_data

        if request.id:
            # 如果id不为空,则查询单个数据
            row_ids = request.id
        elif request.ids and len(request.ids) > 0:
            # 如果id为空,则查询ids数据
            row_ids = ",".join(request.ids)
        else:
            # 查询所有数据
            row_ids = None

        data = await get_index_data(
            request.namespace, request.code, request.filename, datatype, row_ids
        )

        if request.id:
            # 如果id不为空,则查询单个数据,所以此处返回单条数据
            if len(data) > 0:
                data = data[0]
            else:
                raise ValueError(f"data [{request.id}] not found")

        if request.id and request.response_type == "html":
            html_file_path = os.path.join(
                ROOT_PATH, "webserver", "templates", f"{datatype}_template.html"
            )
            with open(html_file_path) as file:
                html_content = file.read()
            template = Template(html_content)
            html_content = template.render(data=data)
            return HTMLResponse(content=html_content)
        return JSONResponse(content=jsonable_encoder(data))

    except Exception as e:
        logger.exception("查询索引数据失败")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/graphrag/index_data/add", summary="实体，实体关系，社区报告新增")
async def index_data_add(indexdata: IndexData):
    """
    处理index_data。

    Args:
        indexdata (IndexData): indexdata 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.service.indexdata import index_data_add

    datatype = indexdata.datatype

    if datatype not in ["entities", "reports", "relationships"]:
        raise ValueError(f"{datatype} not found")

    root_dir = build_root_path(indexdata.namespace, indexdata.code, indexdata.filename)
    data_dir = os.path.join(root_dir, "output", "artifacts")

    data = await index_data_add(data_dir, datatype, indexdata.data)

    return JSONResponse(content=jsonable_encoder(data))


@app.post("/v1/graphrag/index_data/update", summary="实体，实体关系，社区报告更新")
async def index_data_update(indexdata: IndexData):
    """
    处理index_data。

    Args:
        indexdata (IndexData): indexdata 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.service.indexdata import index_data_update

    datatype = indexdata.datatype

    if datatype not in ["entities", "reports", "relationships"]:
        raise ValueError(f"{datatype} not found")

    root_dir = build_root_path(indexdata.namespace, indexdata.code, indexdata.filename)
    data_dir = os.path.join(root_dir, "output", "artifacts")

    data = await index_data_update(data_dir, datatype, indexdata.data)

    return JSONResponse(content=jsonable_encoder(data))


@app.post("/v1/graphrag/index_data/delete", summary="实体，实体关系，社区报告删除")
async def index_data_delete(indexdata: IndexData):
    """
    处理index_data。

    Args:
        indexdata (IndexData): indexdata 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.service.indexdata import index_data_delete

    datatype = indexdata.datatype

    if datatype not in ["entities", "reports", "relationships"]:
        raise ValueError(f"{datatype} not found")

    root_dir = build_root_path(indexdata.namespace, indexdata.code, indexdata.filename)
    data_dir = os.path.join(root_dir, "output", "artifacts")

    data = await index_data_delete(data_dir, datatype, indexdata.data)

    return JSONResponse(content=jsonable_encoder(data))


@app.post(
    "/v1/graphrag/index_data/get_by_id", summary="通过id查询实体，实体关系，社区报告"
)
async def index_data_get_by_id(indexdata: IndexData):
    """
    处理index_data_id。

    Args:
        indexdata (IndexData): indexdata 参数。

    Returns:
        处理结果。
    """
    from ai.components.graphrag.webserver.service.indexdata import (
        index_data_get_by_id,
    )

    datatype = indexdata.datatype

    if datatype not in ["entities", "reports", "relationships"]:
        raise ValueError(f"{datatype} not found")

    root_dir = build_root_path(indexdata.namespace, indexdata.code, indexdata.filename)
    data_dir = os.path.join(root_dir, "output", "artifacts")

    data = await index_data_get_by_id(data_dir, datatype, indexdata.data)

    return JSONResponse(content=jsonable_encoder(data))


@app.post("/v1/graphrag/search", summary="检索")
async def graphrag_search(request: SearchParam):
    """
    处理graphrag_search。

    Args:
        request (SearchParam): request 参数。

    Returns:
        处理结果。
    """
    try:
        await _check_index_exist(request.namespace, request.code, request.filename)

        from ai.components.graphrag.query.__main__ import (
            INVALID_METHOD_ERROR,
            SearchType,
        )
        from ai.components.graphrag.webserver.service.search import (
            run_global_search,
            run_local_search,
        )

        match request.query_method:
            case SearchType.LOCAL.value:
                response = await run_local_search(
                    request.namespace,
                    request.code,
                    request.filename,
                    request.community_level,
                    request.response_type,
                    request.query,
                    request.min_score,
                )
            case SearchType.GLOBAL.value:
                response = await run_global_search(
                    request.namespace,
                    request.code,
                    request.filename,
                    request.community_level,
                    request.response_type,
                    request.query,
                )
            case _:
                raise ValueError(INVALID_METHOD_ERROR)

        return JSONResponse(content=jsonable_encoder(SearchResult(response=response)))
    except Exception as e:
        logger.exception("搜索失败")
        raise HTTPException(status_code=400, detail=str(e))
