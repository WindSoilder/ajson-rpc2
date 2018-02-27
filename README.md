# ajson-rpc2
An implementation of [json rpc 2.0](http://www.jsonrpc.org/) which is based on python3 asyncio module, it's designed for *async* and *extensible* for json-rpc based protocol (like language server protocol, or HTTP based json rpc 2.0).  And the json-rpc protocol is based on *TCP*.

# Usage
It's easy to use :)
```python
    from ajson_rpc2 import JsonRPC2

    server = JsonRPC2()

    # make one function to be rpc called
    @server.rpc_call
    def substract(num1, num2):
        return num1 - num2

    # also support for the async rpc call
    @server.rpc_call
    async def io_bound_call(num1):
        await asyncio.sleep(3)
        return num1

    server.start(port=9999)
```

When we run the server successfully, we can use *telnet* to test it:

    $ telnet localhost 9999
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}

    # should return
    {"jsonrpc": "2.0", "result": 19, "id": 1}

# Features
1. Easy to use, support both async call and sync call
2. Extensible for json-rpc based protocol (like language server protocol)

# Support version
The *ajson-rpc2* is only support for **python3.5+**
