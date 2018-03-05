# ajson-rpc2
An implementation of [json rpc 2.0](http://www.jsonrpc.org/) which is based on python3 asyncio module, it's designed for *async* and *extensible* for json-rpc based protocol (like language server protocol).  And the json-rpc protocol is based on *TCP*.

# Install
Use through *setup.py*

```shell
    python setup.py install
```

# Usage
It's easy to use :)

## Server
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

## Client
When we run the server successfully, we can use *telnet* to test it:

    $ telnet localhost 9999
    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}

    # should return
    {"jsonrpc": "2.0", "result": 19, "id": 1}

Note that there is no standard client implementation, if you need a client sample(written in python), you can check `client.py` file which lays in `accept_tests` folder. Here is an example for the usage of `client.py`:

    # assume that you have run server successfully, and the port is 9999
    from client import MockJsonRPC2Client

    client = MockJsonRPC2Client(ip_addr, 9999)
    client.connect()
    client.send_data({"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1})

    client.recv()  # which will get result back from server

`MockJsonRPC2Client` can send python object(which can be parsed in json) to server.  But please note that it's just a client for testing.

# Features
1. Easy to use, support both async call and sync call
2. Extensible for json-rpc based protocol (like language server protocol)

# Limited
For now the client can only send one-line request to the server, like this:

    {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}

or like this in batched requests:

    [ {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}, {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 2} ]

Which is client un friendly, and it will be resolved in the future version.

# Support version
The *ajson-rpc2* is only support for **python3.6+**

# Tests
*ajson-rpc2* uses pytest to write unit tests.  And it also have acceptance tests.  To run unit test, use the following command:

    pytest

To run acceptance tests, please go into `accept_tests` folder, then runs the following command:

    python accept_test.py

If the output message is like this:

    all tests run complete with no errors

Then all tests runs successful, most of test cases is get from the [jsonrpc page](http://www.jsonrpc.org/specification)


# Best practise
ajson-rpc2 is based on *asyncio*, which is good for IO bound processes, so it is recommended to define rpc call as async functions, this is an example:

    # good
    @ajson_rpc.rpc_call
    async def fetch():
        await asyncio.sleep(3)
        return 5

    # bad
    @ajson_rpc.rpc_call
    def fetch():
        time.sleep(3)
        return 5
