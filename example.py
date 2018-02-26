import json
from asyncio import BaseEventLoop, get_event_loop, start_server
import asyncio
from ajson_rpc2.server import JsonRPC2
import signal
import logging


async def subtract(num1: int, num2: int) -> int:
    await asyncio.sleep(2)
    return num1 - num2


loop: BaseEventLoop = get_event_loop()
json_rpc2 = JsonRPC2(loop)
json_rpc2.add_method(subtract)
f = start_server(json_rpc2.handle_client,
                 port=9999, loop=loop)
server = loop.run_until_complete(f)
loop.add_signal_handler(signal.SIGINT, loop.stop)
try:
    loop.run_forever()
finally:
    loop.close()
