"""包含read_dotenv实用工具的模块."""

import logging
import os
from pathlib import Path

from dotenv import dotenv_values

log = logging.getLogger(__name__)


def read_dotenv(root: str) -> None:
    """在给定的根路径中读取.env文件."""
    env_path = Path(root) / ".env"
    if env_path.exists():
        log.info("Loading pipeline .env file")
        env_config = dotenv_values(f"{env_path}")
        for key, value in env_config.items():
            if key not in os.environ:
                os.environ[key] = value or ""
    else:
        log.info("No .env file found at %s", root)
