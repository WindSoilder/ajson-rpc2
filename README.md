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

## Module support
Actually, you can support method call like *document/open*, *window.write*, when you use module features.  Sample code is like this:
```Python
    from ajson_rpc2 import JsonRPC2, Module

    document_module = Module('document')
    window_module = Module('window')

    @document_module.rpc_call
    def open():
        pass

    @window_module.rpc_call
    def write():
        pass

    app = JsonRPC2()
    app.register_module(document_module)
    app.register_module(window_module)

    app.run()
```

Then you can pass method like this: `document/open`, `document.open`, `window.open`, `window/open`

# Features
1. Easy to use, support both async call and sync call
2. Configuable for the rpc call, you can make it to be called with multi processing or multi threading
3. Extensible for json-rpc based protocol (like language server protocol)

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


# Advanced Usage
Assume that you have a CPU bound function, and you need to make it rpc call, it's recommended to use `add_method` method with `need_multiprocessing` argument, this is an example:

    json_rpc = JsonRPC2()

    def subtract(num1, num2):
        total = 0
        for i in range(1000000):
            total += i
        return total / 100 + num1 - num2

    # use add_method with need_multiprocessing to
    # make the method is called in another process
    json_rpc.add_method(high_cpu, need_multiprocessing=True)

When client send batch request to server like this:

    [{"jsonrpc": "2.0", "method": "subtract", "params": [2, 3], "id": 3}, {"jsonrpc": "2.0", "method": "subtract", "params": [2, 3], "id": 3},{"jsonrpc": "2.0", "method": "subtract", "params": [2, 3], "id": 3}, {"jsonrpc": "2.0", "method": "subtract", "params": [2, 3], "id": 3}, {"jsonrpc": "2.0", "method": "subtract", "params": [2, 3], "id": 3}]

Here are run time tests (My test dev machine have 2-cores CPU, and 2GB memory) for the subtract rpc call:

    data = {"jsonrpc": "2.0", "method": "subtract", "params": [1, 2], "id": "4"}
    batch_data = [data] * 10

1. have config `need_multiprocessing`
    the rpc call takes about 24 seconds
2. don't config `need_multiprocessing`
    the rpc call takes about 46 seconds
3. simply call the `subtract(1, 2)` with 10 times
    takes about 45 seconds


The subtract method will be called in the inner process pool executor, which can improve performance.  The default max process in the server is 4, you can create your own *concurrent.futures.ProcessPoolExecutor* and transfer it to json rpc server, to make it can work with more processes.  this is an example:

    from concurrent.futures import ProcessPoolExecutor

    executor = ProcessPoolExecutor(max_workers=10)
    json_rpc = JsonRPC2(process_executor=executor)

Note that for the rpc call which need to be execute with multiprocess or multithread, we **can not** add method to our json rpc2 server by using `@rpc_call` decorator, because decorated function is not **picklable**, which is required by the underlying module `multiprocessing`
