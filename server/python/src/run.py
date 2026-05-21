"""
Web 服务器入口
"""

import click
import uvicorn

from demo.configs import settings


@click.command()
@click.option("--host", default=settings.server.host, help="服务器主机")
@click.option("--port", default=settings.server.port, help="服务器端口")
@click.option("--reload", is_flag=True, default=False, help="启用热重载")
def main(host: str, port: int, reload: bool):
    """启动 Web 服务器"""
    uvicorn.run(
        "application_web:app",
        host=host,
        port=port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
