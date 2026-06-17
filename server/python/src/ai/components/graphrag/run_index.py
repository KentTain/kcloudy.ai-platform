"""提供组件图谱检索增强生成相关功能。"""

if __name__ == "__main__":
    import time

    # 命令行:
    # python -m graphrag.index --verbose --root ./ragdemo

    print("running index, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))

    from ai.components.graphrag.index.__main__ import run_index

    print("running index2, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))
    run_index()
    print("end index, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))
