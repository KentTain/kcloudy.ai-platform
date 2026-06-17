"""提供组件图谱检索增强生成相关功能。"""

import threading
import time
import uuid
import zoneinfo
from datetime import datetime

from ai.components.graphrag.webserver.gtypes.chat_result import TaskResult

# 3天,单位毫秒
TIME_3_DAY = 1000 * 60 * 60 * 24 * 3


class Task:
    """封装组件图谱检索增强生成中的Task逻辑。"""

    def __init__(self, task_id: str):
        """
        初始化实例。

        Args:
            task_id (str): task_id 参数。
        """
        self.taskId: str = task_id  # 任务id
        self.status: str = "running"  # running, done, failed, cancelling, cancelled
        self.log: str = ""  # 日志
        self.start_time: int | None = None  # 开始时间
        self.end_time: int | None = None  # 结束时间
        self._ext_info = {}  # 扩展信息，用于存储一些额外信息
        self.progress = 0  # 0-100
        self.save_path: str | None = None  # 序列化到磁盘的地址
        self.update_time: int | None = None  # 更新时间
        self.thread: threading.Thread | None = None  # 任务线程
        self.token_info: dict = {}  # 大模型交互信息，包括调用次数、token数

    def is_running(self):
        """
        处理running。

        Returns:
            处理结果。
        """
        return self.status == "running"

    def is_done(self):
        """
        处理done。

        Returns:
            处理结果。
        """
        return self.status == "done"

    def is_failed(self):
        """
        处理failed。

        Returns:
            处理结果。
        """
        return self.status == "failed"

    def is_cancelling(self):
        """
        处理cancelling。

        Returns:
            处理结果。
        """
        return self.status == "cancelling"

    def is_cancelled(self):
        """
        处理cancelled。

        Returns:
            处理结果。
        """
        return self.status == "cancelled"

    def set_thread(self, thread: threading.Thread):
        """设置线程"""
        self.thread = thread

    def start(self):
        """启动start。"""
        self.start_time = int(round(time.time() * 1000))
        self.update()

    def add_token_info(self, _count: int, _input: int, _output: int):
        """
        新增token_info。

        Args:
            _count (int): _count 参数。
            _input (int): _input 参数。
            _output (int): _output 参数。
        """
        self.token_info = {
            "input": self.token_info.get("input", 0) + _input,
            "output": self.token_info.get("output", 0) + _output,
            "count": self.token_info.get("count", 0) + _count,
        }

    def add_log(self, log: str):
        """添加日志"""
        if log:
            # 在log中添加时间
            formatted_beijing_now = (
                datetime.now()
                .astimezone(zoneinfo.ZoneInfo("UTC"))
                .astimezone(zoneinfo.ZoneInfo("Asia/Shanghai"))
                .strftime("%Y-%m-%d %H:%M:%S")
            )
            self.log = f"{self.log}\n{formatted_beijing_now}: {log}"
        self.update()

    def ext_info(self, ext_info: dict):
        """扩展信息,用于存储一些额外信息"""
        self._ext_info.update(ext_info)
        self.update()

    def set_progress(self, progress: float):
        """更新进度,0-100"""
        if progress < 0:
            progress = 0
        if progress > 100:
            progress = 100
        self.progress = progress
        self.update()

    def add_progress(self, progress: float):
        """增加进度,0-100"""
        if progress < 0:
            progress = 0
        if progress > 100:
            progress = 100
        new_progress = self.progress + progress

        if new_progress > 100:
            new_progress = 99

        self.progress = new_progress
        self.update()

    def done(self, log: str):
        """
        处理done。

        Args:
            log (str): log 参数。
        """
        self.status = "done"
        self.progress = 100
        self.end_time = int(round(time.time() * 1000))
        self.add_log(log)

    def fail(self, log: str):
        """
        处理fail。

        Args:
            log (str): log 参数。
        """
        self.status = "failed"
        self.end_time = int(round(time.time() * 1000))
        self.add_log(log)

    def cancelling(self, log: str = "取消中"):
        """
        处理cancelling。

        Args:
            log (str): log 参数。
        """
        self.status = "cancelling"
        self.add_log(log)

    def cancelled(self, log: str = "取消成功"):
        """
        处理cancelled。

        Args:
            log (str): log 参数。
        """
        self.status = "cancelled"
        self.end_time = int(round(time.time() * 1000))
        self.add_log(log)

    def update(self):
        """更新update。"""
        self.update_time = int(round(time.time() * 1000))
        self.save()

    def save(self):
        """将任务以json方式序列化到磁盘"""
        if self.save_path:
            print(f"save task {self.taskId} to {self.save_path}")
            task = self.to_task_result()
            # todo
            # with open(self.save_path, "w") as f:
            #     f.write(task.to_json())

    def to_task_result(self):
        """
        处理task_result。

        Returns:
            处理结果。
        """
        return TaskResult(
            taskId=self.taskId,
            status=self.status,
            log=self.log,
            start_time=self.start_time,
            end_time=self.end_time,
            ext_info=self._ext_info,
            progress=self.progress,
            update_time=self.update_time,
            thread_info={
                "ident": self.thread.ident if self.thread else None,
                "native_id": self.thread.native_id if self.thread else None,
                "name": self.thread.name if self.thread else None,
                "is_alive": self.thread.is_alive() if self.thread else None,
            },
            token_info=self.token_info,
        )


class TaskFactory:
    """封装组件图谱检索增强生成中的TaskFactory逻辑。"""

    def __init__(self):
        """初始化实例。"""
        self.tasks: dict[str, Task] = {}
        self.threadId_taskId: dict[str, str] = {}

    def set_thread(self, thread: threading.Thread, task: Task):
        """设置线程"""
        if thread.ident:
            self.threadId_taskId[self._build_thread_uid(thread)] = task.taskId
            task.set_thread(thread)
        else:
            print(
                f"----------ERROR---------- thread id is None! task: {task.to_task_result()}"
            )
            raise Exception("thread id is None")

    def get_task(self, thread: threading.Thread):
        """获取任务"""
        taskId = self.threadId_taskId.get(self._build_thread_uid(thread), None)
        if taskId:
            return self.tasks[taskId]

    def create(self):
        """
        创建create。

        Returns:
            处理结果。
        """
        taskId = str(uuid.uuid4())
        task = Task(taskId=taskId)

        task.start()

        self.tasks[taskId] = task
        return task

    def get(self, task_id: str) -> Task:
        """
        获取get。

        Args:
            task_id (str): task_id 参数。

        Returns:
            处理结果。
        """
        return self.tasks.get(task_id, None)

    def _delete_completed_task(self, task: Task):
        """
        删除completed_task。

        Args:
            task (Task): task 参数。

        Returns:
            处理结果。
        """
        if task.status in ("done", "failed"):
            print(f"delete completed task: {task}")
            self.tasks.pop(task.taskId, None)
            return True
        print(
            f"-----------ERROR---------- delete task {task.taskId} but status is not done or failed"
        )
        return False

    def delete(self, task_id: str, force: bool = False):
        """
        删除delete。

        Args:
            task_id (str): task_id 参数。
            force (bool): force 参数。
        """
        task = self.tasks.get(task_id, None)
        if task:
            thread = task.thread

            if force:
                # 强制删除,不管任务状态是什么,都删掉
                print(f"force delete task {task_id}")
                self.tasks.pop(task_id, None)
                if thread:
                    self.threadId_taskId.pop(self._build_thread_uid(thread), None)
                return

            # 开始删除操作已完成的task和thread
            print(f"delete task {task_id}")

            if thread:
                if thread.is_alive():
                    # 线程还在运行,就不删除了
                    print(
                        f"-----------ERROR---------- delete task {task_id} but thread is alive. task:{task.to_task_result()}"
                    )
                else:
                    if self._delete_completed_task(task):
                        print(f"delete task {task_id} and thread")
                        self.tasks.pop(task_id, None)
                        self.threadId_taskId.pop(self._build_thread_uid(thread), None)
                    else:
                        pass

            else:
                self._delete_completed_task(task)

    def _build_thread_uid(self, thread: threading.Thread):
        """
        构建build_thread_uid。

        Args:
            thread (threading.Thread): thread 参数。

        Returns:
            处理结果。
        """
        from ai.components.graphrag.webserver.utils.rag_util import md5

        return f"{thread.ident}_{thread.native_id}_{md5(thread.name)}"

    def list(self, status: str | None = None):
        """
        查询列表list。

        Args:
            status (str | None): status 参数。

        Returns:
            处理结果。
        """
        if status:
            return [
                task.to_task_result()
                for task in self.tasks.values()
                if task.status == status
            ]
        return [task.to_task_result() for task in self.tasks.values()]

    def list_abnormal_task(self):
        """获取不正常的任务"""
        # 如果线程还在运行,则任务状态为running, cancelling
        # 如果线程已经结束,则任务状态为done或者failed,cancelled

        result = []
        for task in self.tasks.values():
            thread = task.thread
            if thread:
                if task.is_running() or task.is_cancelling():
                    if thread.is_alive() is False:
                        # 任务运行中, 线程不应该结束的
                        result.append(task.to_task_result())

                elif task.is_done() or task.is_failed() or task.is_cancelled():
                    if thread.is_alive() is True:
                        # 任务已经结束, 线程不应该运行的
                        result.append(task.to_task_result())
                    else:
                        pass

            else:
                # 线程如果不存在, 则将任务状态标志为failed
                if task.is_running() or task.is_cancelling():
                    curr_status = task.status
                    task.status = "failed"
                    task.add_log(f"发生异常, 之前状态: {curr_status}")
                elif task.is_done() or task.is_failed() or task.is_cancelled():
                    pass
                else:
                    result.append(task.to_task_result())

        return result

    def clean(self):
        """处理clean。"""
        task_id_list = []
        # 定时清除状态为done或者failed,并且结束超过3天的task
        for task in self.tasks.values():
            if task.status in ("done", "failed") and (
                (int(round(time.time() * 1000)) - task.end_time) > TIME_3_DAY
            ):
                print(f"删除已经结束的任务： {task.taskId}")
                task_id_list.append(task.taskId)

        for task_id in task_id_list:
            self.delete(task_id)


task_factory = TaskFactory()
