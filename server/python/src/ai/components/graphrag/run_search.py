"""提供组件图谱检索增强生成相关功能。"""

if __name__ == "__main__":
    import time

    # 命令行:
    # python -m graphrag.query --root ./ragdemo --method global "文档的主要内容是什么"
    # python -m graphrag.query --root ./ragdemo --method local "刘备是什么样的人?"

    print("running query, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))

    from ai.components.graphrag.query.__main__ import run_search

    print("running query2, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))
    run_search()
    print("end query, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))
