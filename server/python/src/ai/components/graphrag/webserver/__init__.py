"""初始化组件图谱检索增强生成包。"""

import logging
import time


START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
logger.info(
    "Initializing webserver module, time: %s",
    time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(START_TIME)),
)
