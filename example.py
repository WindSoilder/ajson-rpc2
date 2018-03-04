from ajson_rpc2.server import JsonRPC2

rpc_server = JsonRPC2()


@rpc_server.rpc_call
async def subtract(minuend, subtrahend):
    return minuend - subtrahend

rpc_server.start()
