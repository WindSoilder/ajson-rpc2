''' example for add rpc method which need multi processing '''

from ajson_rpc2.server import JsonRPC2

rpc_server = JsonRPC2()


def subtract(minuend, subtrahend):
    b = 0
    for i in range(100000000):
        b += i
    return b + minuend - subtrahend


rpc_server.add_method(subtract, need_multiprocessing=True)
rpc_server.start()
