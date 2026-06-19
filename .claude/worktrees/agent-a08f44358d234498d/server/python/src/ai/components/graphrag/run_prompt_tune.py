# 命令行:python -m graphrag.prompt_tune --no-entity-types  --root ./ragdemo
"""提供组件图谱检索增强生成相关功能。"""

if __name__ == "__main__":
    import time

    print("running run_prompt_tune, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))

    from ai.components.graphrag.prompt_tune.__main__ import run_prompt_tune

    print("running run_prompt_tune2, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))
    run_prompt_tune()
    print("end run_prompt_tune, time: ", time.strftime("%Y-%m-%d %H:%M:%S"))
