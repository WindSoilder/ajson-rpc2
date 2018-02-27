import time
from ajson_rpc2.server import JsonRPC2

rpc_server = JsonRPC2()


@rpc_server.rpc_call
async def subtract(num1: int, num2: int) -> int:
    time.sleep(2)
    return num1 - num2

rpc_server.start()
