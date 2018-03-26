import pytest
import json
import asyncio

from unittest.mock import Mock, patch
from queue import Queue

from .context import (
    JsonRPC2,
    InvalidParamsError, InvalidRequestError, MethodNotFoundError,
    ParseError, InternalError,
    SuccessResponse, ErrorResponse,
    Request,
    BatchResponse,
    ExtraNeed
)

mock_queue = Queue()


def duplicate_add():
    return 4


def substract_for_multiprocessing(num1, num2):
    return num1 - num2


def have_exception_call():
    1 / 0


async def read_request():
    global mock_queue
    return mock_queue.get()


def write_request(content):
    global mock_queue
    mock_queue.put(content)


def empty_queue():
    global mock_queue
    mock_queue.queue.clear()


@pytest.fixture
def test_app():
    return JsonRPC2()


@pytest.fixture
def reader():
    mock_reader = Mock()
    mock_reader.readline.side_effect = read_request
    mock_reader.close.side_effect = empty_queue

    yield mock_reader
    mock_reader.close()


@pytest.fixture
def writer():
    mock_writer = Mock()

    mock_writer.write.side_effect = write_request
    mock_writer.close.side_effect = empty_queue
    connection_info = mock_writer.get_extra_info.return_value
    connection_info.getpeername.return_value = "test"

    yield mock_writer
    mock_writer.close()


def test_handle_client(test_app: JsonRPC2, reader: Mock, writer: Mock):
    # for testing handle_client method
    # the inner method handle_rpc_call is not what we interested
    # so mock the function to make test_app call
    async def mock_handle_rpc_call(reader, writer):
        pass

    setattr(test_app, "handle_rpc_call", mock_handle_rpc_call)
    test_app.loop.run_until_complete(test_app.handle_client(reader, writer))


def test_handle_client_for_client_error(test_app: JsonRPC2, reader: Mock, writer: Mock):
    # for testing handle_client method
    # the inner method handle_rpc_call is not what we interested
    # so mock the function to make test_app call
    async def mock_handle_error_rpc_call(reader, writer):
        1 / 0

    setattr(test_app, "handle_rpc_call", mock_handle_error_rpc_call)

    test_app.loop.run_until_complete(test_app.handle_client(reader, writer))


def test_handle_rpc_call(test_app: JsonRPC2, reader: Mock, writer: Mock):
    @test_app.rpc_call
    def half(num):
        return num // 2

    # send mock request to server
    writer.write(json.dumps({
        "id": 1,
        "jsonrpc": "2.0",
        "method": "half",
        "params": [4]
    }).encode())
    # send empty string to break server forever loop
    writer.write('')

    test_app.loop.run_until_complete(test_app.handle_rpc_call(reader, writer))

    # fetch response from reader and check result
    resp_bytes = test_app.loop.run_until_complete(reader.readline())
    resp_json = json.loads(resp_bytes.decode())
    assert resp_json == {
        "id": 1,
        "jsonrpc": "2.0",
        "result": 2
    }


def test_handle_rpc_call_with_invalid_json(test_app: JsonRPC2, reader: Mock, writer: Mock):
    # send mock request to server
    writer.write(b'{"id": 1, "jsonrpc":}')
    # send empty string to break server forever loop
    writer.write('')

    test_app.loop.run_until_complete(test_app.handle_rpc_call(reader, writer))

    # fetch response from reader and check result
    resp_bytes = test_app.loop.run_until_complete(reader.readline())
    resp_json = json.loads(resp_bytes.decode())
    assert resp_json == {
        "id": "null",
        "error": {
            "code": -32700,
            "message": "Parse error"
        },
        "jsonrpc": "2.0"
    }


# for now it still lack tests for handle rpc_call method
# and handle_client method
def test_handle_rpc_call_with_batched_request(test_app: JsonRPC2, reader: Mock, writer: Mock):
    @test_app.rpc_call
    def half(num):
        return num // 2

    # send mock request to server
    send_data = [
        {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "half",
            "params": [4]
        },
        {
            "id": 3,
            "jsonrpc": "2.0",
            "method": "half",
            "params": [9]
        }
    ]
    writer.write(json.dumps(send_data).encode())
    # send empty string to break server forever loop
    writer.write('')

    test_app.loop.run_until_complete(test_app.handle_rpc_call(reader, writer))

    # fetch response from reader and check result
    resp_bytes = test_app.loop.run_until_complete(reader.readline())
    resp_json = json.loads(resp_bytes.decode())

    id_to_result_dict = {
        1: 2,
        3: 4
    }

    for resp in resp_json:
        assert resp['result'] == id_to_result_dict[resp['id']]


def test_init_server_with_other_eventloop():
    loop = asyncio.new_event_loop()
    app = JsonRPC2(loop=loop)
    assert app.loop is loop


def test_handle_simple_rpc_call(test_app: JsonRPC2):
    @test_app.rpc_call
    def half(num):
        return num // 2

    request_data = {
        "id": 1,
        "method": "half",
        "params": [1000],
        "jsonrpc": "2.0"
    }

    response = test_app.loop.run_until_complete(test_app.handle_simple_rpc_call(request_data))

    assert isinstance(response, SuccessResponse)
    assert response.resp_id == 1
    assert response.result == 500


def test_handle_simple_rpc_call_with_error(test_app: JsonRPC2):
    request_data = {"method": "not_hello"}

    response = test_app.loop.run_until_complete(test_app.handle_simple_rpc_call(request_data))

    assert isinstance(response, ErrorResponse)


def test_handle_notification(test_app: JsonRPC2):
    @test_app.rpc_call
    def not_hello():
        return 3

    request_data = {"method": "not_hello", "jsonrpc": "2.0"}

    response = test_app.loop.run_until_complete(test_app.handle_simple_rpc_call(request_data))

    assert response is None


def test_handle_simple_rpc_call_with_internal_error(test_app: JsonRPC2):
    @test_app.rpc_call
    def sub(num):
        1 / 0

    request_data = {
        "id": 1,
        "method": "sub",
        "params": [2],
        "jsonrpc": "2.0"
    }

    response = test_app.loop.run_until_complete(test_app.handle_simple_rpc_call(request_data))

    assert isinstance(response, ErrorResponse)
    assert isinstance(response.error, InternalError)


def test_handle_batched_rpc_call(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        return num1 + num2

    request_data = [
        {"id": 1, "method": "add", "params": [1, 2], "jsonrpc": "2.0"},
        {"id": 2, "method": "add", "params": [4, 5], "jsonrpc": "2.0"}
    ]

    responses = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call(request_data))

    assert len(responses) == 2
    response_dict = {
        1: 3,
        2: 9,
    }
    for response in responses:
        assert response.result == response_dict[response.resp_id]


def test_handle_batched_rpc_call_with_an_invalid_batch(test_app: JsonRPC2):
    request_data = [1]

    responses = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call(request_data))

    assert responses.to_json() == [
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}, "id": "null"}
    ]


def test_handle_batched_rpc_call_which_need_multiprocessing_with_no_parameters(test_app: JsonRPC2):
    _test_for_special_need_rpc_call(test_app, "multiprocessing")


def test_handle_batched_rpc_call_which_need_multiprocessing_with_parameters(test_app: JsonRPC2):
    test_app.add_method(substract_for_multiprocessing, need_multiprocessing=True)
    request_data = [
        {"id": 1, "method": "substract_for_multiprocessing", "jsonrpc": "2.0", "params": [1, 2]},
        {"id": 2, "method": "substract_for_multiprocessing", "jsonrpc": "2.0", "params": {"num1": 3, "num2": 5}},
    ]

    resp_data_dict = {
        1: {"result": -1},
        2: {"result": -2},
    }
    responses = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call(request_data))

    for response in responses:
        assert response.to_json()["result"] == resp_data_dict[response.resp_id]["result"]


def test_handle_batched_rpc_call_which_need_multithreading(test_app: JsonRPC2):
    _test_for_special_need_rpc_call(test_app, "multithreading")


def test_handle_empty_batched(test_app: JsonRPC2):
    response = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call([]))
    assert isinstance(response, ErrorResponse)


def test_handle_one_batched_call(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        return num1 + num2

    request_data = [
        {"id": 1, "method": "add", "params": [1, 2]}
    ]

    response = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call(request_data))

    assert isinstance(response, BatchResponse)
    assert len(response) == 1


def test_handle_batched_call_with_all_notifications(test_app: JsonRPC2):
    @test_app.rpc_call
    def not_hello():
        return 3

    @test_app.rpc_call
    def not_world():
        return 4

    request_data = [
        {"method": "not_hello", "jsonrpc": "2.0"},
        {"method": "not_world", "jsonrpc": "2.0"}
    ]

    response = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call(request_data))

    assert response is None


def test_read(test_app: JsonRPC2, reader: Mock, writer: Mock):
    data = {'name': 'zero', 'age': 19}
    writer.write(data)
    assert test_app.loop.run_until_complete(test_app.read(reader)) is data


def test_invoke_method(test_app: JsonRPC2):
    @test_app.rpc_call
    def foo(num1, num2):
        return num1 - num2

    request = Request('foo', [4, 2], 2)
    assert test_app.loop.run_until_complete(test_app.invoke_method(request)) == 2


def test_invoke_method_with_keyword_parameter(test_app: JsonRPC2):
    @test_app.rpc_call
    def foo(num1, num2):
        return num1 + num2

    request = Request('foo', {'num2': 1, 'num1': 5}, 2)
    assert test_app.loop.run_until_complete(test_app.invoke_method(request)) == 6


def test_invoke_no_parameter_method(test_app: JsonRPC2):
    @test_app.rpc_call
    def foo():
        return 3

    request = Request('foo', [], 2)
    assert test_app.loop.run_until_complete(test_app.invoke_method(request)) == 3


def test_invoke_async_method(test_app: JsonRPC2):
    @test_app.rpc_call
    async def a(num):
        return 2

    request = Request('a', [1], 2)
    assert test_app.loop.run_until_complete(test_app.invoke_method(request)) == 2


def test_get_method(test_app: JsonRPC2):
    def add(num1):
        pass
    test_app.add_method(add)

    assert test_app.get_method('add') is add


def test_get_not_existed_method(test_app: JsonRPC2):
    with pytest.raises(ValueError):
        test_app.get_method("test")


def test_get_rpc_method(test_app: JsonRPC2):
    def add(num1):
        pass
    test_app.add_method(add)

    assert test_app.get_rpc_method('add').func is add


def test_get_not_existed_rpc_method(test_app: JsonRPC2):
    with pytest.raises(ValueError):
        test_app.get_rpc_method('abc')


def test_add_method(test_app: JsonRPC2):
    def add(num1, num2):
        pass

    test_app.add_method(add)
    assert 'add' in test_app.methods
    assert len(test_app.methods) == 1
    assert test_app.get_rpc_method('add').extra_need is ExtraNeed.NOTHING


def test_add_method_with_restrict_mode(test_app: JsonRPC2):
    with pytest.raises(ValueError):
        global duplicate_add
        test_app.add_method(duplicate_add)

        def duplicate_add():
            pass

        test_app.add_method(duplicate_add)


def test_add_method_which_need_multiprocessing(test_app: JsonRPC2):
    def add(num1, num2):
        pass

    test_app.add_method(add, need_multiprocessing=True)

    assert 'add' in test_app.methods
    assert test_app.get_rpc_method('add').extra_need is ExtraNeed.PROCESS


def test_add_method_which_need_multithreading(test_app: JsonRPC2):
    def add(num1, num2):
        pass

    test_app.add_method(add, need_multithreading=True)

    assert 'add' in test_app.methods
    assert test_app.get_rpc_method('add').extra_need is ExtraNeed.THREAD


def test_send_response(test_app: JsonRPC2,
                       reader: Mock,
                       writer: Mock):
    response = SuccessResponse("10", 3)
    test_app.send_response(writer, response)

    content = test_app.loop.run_until_complete(reader.readline())
    content_json = json.loads(content.decode())
    assert content_json == {
        "jsonrpc": "2.0",
        "result": "10",
        "id": 3
    }


def test_get_request_id(test_app: JsonRPC2):
    request = {
        "method": "add",
        "id": 4,
        "jsonrpc": "2.0"
    }
    assert test_app.get_request_id(request, None) == 4


def test_get_request_id_for_errors(test_app: JsonRPC2):
    request = {
        "method": "add",
        "id": 4,
        "jsonrpc": "2.0"
    }
    assert test_app.get_request_id(request, ParseError("Parse error")) is None
    assert test_app.get_request_id(request, InvalidRequestError("Invalid request")) is None


def test_check_invalid_request_errors(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        pass

    request = {
        "id": 1,
        "method": "add",
        "params": [1, 2]
    }
    assert isinstance(test_app.check_errors(request),
                      InvalidRequestError)


def test_check_method_not_exist_errors(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        pass

    request = {
        "id": 1,
        "method": "substract",
        "params": [1],
        "jsonrpc": "2.0"
    }
    assert isinstance(test_app.check_errors(request),
                      MethodNotFoundError)


def test_check_params_invalid_errors(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        pass

    request = {
        "id": 1,
        "method": "add",
        "params": [1],
        "jsonrpc": "2.0"
    }
    assert isinstance(test_app.check_errors(request),
                      InvalidParamsError)


def test_check_no_errors(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        pass

    request = {
        "id": 1,
        "method": "add",
        "params": [1, 2],
        "jsonrpc": "2.0"
    }
    assert test_app.check_errors(request) is None


def test_rpc_call(test_app: JsonRPC2):
    assert len(test_app.methods) == 0


def test_decorate_a_rpc_call(test_app: JsonRPC2):
    @test_app.rpc_call
    def substract(num1, num2):
        return num1 - num2

    assert len(test_app.methods) == 1


def test_decorate_annotation_rpc_call(test_app: JsonRPC2):
    @test_app.rpc_call
    def add(num1, num2):
        return num1 + num2

    @test_app.rpc_call
    def multi(num1: int, num2: int):
        return num1 * num2

    assert len(test_app.methods) == 2


def test_start():
    # here we will create a mock loop
    # to test the logic of start
    mock_loop = Mock()
    mock = Mock(return_value=1)
    test_app = JsonRPC2(mock_loop)

    with patch("asyncio.start_server", mock):
        test_app.start()
        mock_loop.run_until_complete.assert_called_with(1)
        mock_loop.run_forever.assert_called_with()
        mock_loop.close.assert_called_with()


def _test_for_special_need_rpc_call(test_app: JsonRPC2, special_need: str):
    if special_need == "multiprocessing":
        test_app.add_method(duplicate_add, need_multiprocessing=True)
        test_app.add_method(have_exception_call, need_multiprocessing=True)
    elif special_need == "multithreading":
        test_app.add_method(duplicate_add, need_multithreading=True)
        test_app.add_method(have_exception_call, need_multithreading=True)
    request_data = [
        {"id": 1, "method": "duplicate_add", "jsonrpc": "2.0"},
        {"id": 2, "method": "duplicate_add", "jsonrpc": "2.0"},
        {"id": 4, "method": "add", "jsonrpc": "2.0"},
        {"id": 5, "method": "duplicate_add", "jsonrpc": "2.0", "params": [1, 2]},
        {"id": 6, "method": "add"},
        {"id": 7, "method": "have_exception_call", "jsonrpc": "2.0"}
    ]

    resp_data_dict = {
        1: {"result": 4},
        2: {"result": 4},
        4: {"error": {"code": -32601, "message": "Method not found"}},
        5: {"error": {"code": -32602, "message": "Invalid params"}},
        None: {"error": {"code": -32600, "message": "Invalid Request"}},
        7: {"error": {"code": -32603, "message": "Internal error"}}
    }
    responses = test_app.loop.run_until_complete(test_app.handle_batched_rpc_call(request_data))

    for response in responses:
        if isinstance(response, SuccessResponse):
            assert response.to_json()["result"] == resp_data_dict[response.resp_id]["result"]
        else:
            assert response.to_json()["error"] == resp_data_dict[response.resp_id]["error"]
