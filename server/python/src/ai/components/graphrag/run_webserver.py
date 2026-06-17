"""提供组件图谱检索增强生成相关功能。"""

if __name__ == "__main__":
    import os
    from datetime import datetime

    print(f"[{datetime.now()}] [{os.getpid()}] 开始启动服务: [start graphrag engine]")

    from ai.components.graphrag.webserver.utils.consts import ROOT_PATH

    print("ROOT_PATH: ", ROOT_PATH)

    import uvicorn

    from ai.components.graphrag.webserver.main import app

    uvicorn.run(app, host="0.0.0.0", port=20214)
