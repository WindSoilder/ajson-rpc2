''' basic usage example '''

from ajson_rpc2.server import JsonRPC2

rpc_server = JsonRPC2()


def subtract(minuend, subtrahend):
    return minuend - subtrahend


@rpc_server.rpc_call
def add(num1, num2):
    return num1 + num2


rpc_server.add_method(subtract)
rpc_server.start()
