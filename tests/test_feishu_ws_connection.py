import asyncio
import logging
import threading
import time
import lark_oapi as lark
import lark_oapi.ws as ws
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_feishu_ws")

import os

app_id = os.environ.get("FEISHU_APP_ID", "")
app_secret = os.environ.get("FEISHU_APP_SECRET", "")

def do_p2_im_message_receive_v1(data: P2ImMessageReceiveV1) -> None:
    logger.info("收到飞书消息事件: %s", data)

event_handler = (
    lark.EventDispatcherHandler.builder("", "")
    .register_p2_im_message_receive_v1(do_p2_im_message_receive_v1)
    .build()
)

cli = ws.Client(
    app_id=app_id,
    app_secret=app_secret,
    event_handler=event_handler,
    log_level=lark.LogLevel.INFO,
    auto_reconnect=True
)

def start_worker():
    # 确保子线程拥有并运行事件循环
    asyncio.set_event_loop(ws.client.loop)
    logger.info("线程内开始启动 cli.start()...")
    cli.start()

thread = threading.Thread(target=start_worker, daemon=True)
thread.start()

time.sleep(3)
conn_status = cli._conn is not None and not getattr(cli._conn, "closed", True)
logger.info("检查结果: connected=%s", conn_status)
time.sleep(1)
