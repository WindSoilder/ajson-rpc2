from client import MockJsonRPC2Client

client = MockJsonRPC2Client('localhost', 8080)

err_format = "\n\tActual Val: {actual}\n\tExpect Val: {expect}"


def send_and_receive_data(data):
    client.connect()
    client.send_data(data)
    return client.recv()


def send_raw_and_receive_data(data):
    client.connect()
    client.send_raw_data(data)
    return client.recv()


def test_simple_rpc_call():
    data = {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}
    resp = send_and_receive_data(data)
    expect = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": 19
    }
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = {"jsonrpc": "2.0", "method": "subtract", "params": {"subtrahend": 23, "minuend": 42}, "id": 3}
    resp = send_and_receive_data(data)
    expect = {"jsonrpc": "2.0", "result": 19, "id": 3}
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = {"jsonrpc": "2.0", "method": "subtract", "params": [23, 42], "id": 2}
    expect = {"jsonrpc": "2.0", "result": -19, "id": 2}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = {"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 42, "subtrahend": 23}, "id": 4}
    expect = {"jsonrpc": "2.0", "result": 19, "id": 4}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_invalid_request():
    data = {"jsonrpc": "2.0", "method": 1, "params": "bar"}
    expect = {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_parse_error():
    data = b'{"jsonrpc": "2.0", "method": 1'
    expect = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": 'null'}
    resp = send_raw_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_not_existed_method():
    data = {"jsonrpc": "2.0", "method": "foobar", "id": "1"}
    expect = {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "1"}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_invalid_params():
    data = {"jsonrpc": "2.0", "method": "subtract", "id": 2}
    expect = {"jsonrpc": "2.0", "error": {"code": -32602, "message": "Invalid params"}, "id": 2}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = {"jsonrpc": "2.0", "method": "subtract", "params": [23, 42, 51], "id": 2}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = {"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 42, "subtrahenda": 23}, "id": 2}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = {"jsonrpc": "2.0", "method": "subtract", "params": {"minuend": 42}, "id": 2}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_internal_error():
    data = {"jsonrpc": "2.0", "method": "have_error_method", "params": [23], "id": 2}
    expect = {"jsonrpc": "2.0", "error": {"code": -32603, "message": "Internal error"}, "id": 2}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


# tests for batched requests
def test_batched_request():
    data = [
        {"jsonrpc": "2.0", "method": "subtract", "params": [1, 5], "id": "1"},
        {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"}
    ]
    expect = [
        {"jsonrpc": "2.0", "result": -4, "id": "1"},
        {"jsonrpc": "2.0", "result": 19, "id": "2"}
    ]
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_batched_request_with_invalid_json():
    data = b'[{"jsonrpc": "2.0", "method": "sum", "params": [1,2,4], "id": "1"},{"jsonrpc": "2.0", "method"]'
    expect = {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": "null"}
    resp = send_raw_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_batched_request_with_empty_array():
    data = []
    expect = {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"}
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)


def test_batched_request_with_an_invalid_batch():
    data = [1]
    expect = [
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"}
    ]
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)

    data = [1, 2, 3]
    expect = [
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"},
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"},
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"}
    ]
    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)    


def regular_rpc_call():
    data = [
        {"jsonrpc": "2.0", "method": "sum", "params": [1, 2, 4], "id": "1"},
        {"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": "2"},
        {"foo": "boo"},
        {"jsonrpc": "2.0", "method": "foo.get", "params": {"name": "myself"}, "id": "5"},
        {"jsonrpc": "2.0", "method": "get_data", "id": "9"} 
    ]

    expect = [
        {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "1"},
        {"jsonrpc": "2.0", "result": 19, "id": "2"},
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"},
        {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "5"},
        {"jsonrpc": "2.0", "error": {"code": -32601, "message": "Method not found"}, "id": "9"}
    ]

    resp = send_and_receive_data(data)
    assert resp == expect, err_format.format(actual=resp, expect=expect)    