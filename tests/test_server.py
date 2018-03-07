import pytest
import json
import asyncio
from queue import Queue

from .context import (
    JsonRPC2,
    InvalidParamsError, InvalidRequestError, MethodNotFoundError,
    ParseError, InternalError,
    SuccessResponse, ErrorResponse,
    Request, Notification,
    BatchRequest, BatchResponse
)

mock_queue = Queue()


def duplicate_add():
    pass


class MockStreamReader:
    async def readline(self):
        global mock_queue
        return mock_queue.get()

    def close(self):
        ''' mock close will empty the queue '''
        global mock_queue
        mock_queue = Queue()


class MockStreamWriter:
    def write(self, content):
        global mock_queue
        mock_queue.put(content)

    def close(self):
        ''' mock close will empty the queue '''
        global mock_queue
        mock_queue = Queue()


@pytest.fixture
def test_app():
    return JsonRPC2()


@pytest.fixture
def reader():
    mock_reader = MockStreamReader()
    yield mock_reader
    mock_reader.close()


@pytest.fixture
def writer():
    mock_writer = MockStreamWriter()
    yield mock_writer
    mock_writer.close()


# for now it still lack tests for handle rpc_call method
# and handle_client method

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


def test_read(test_app: JsonRPC2, reader: MockStreamReader, writer: MockStreamWriter):
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

    assert test_app.methods['add'] is add


def test_get_not_existed_method(test_app: JsonRPC2):
    with pytest.raises(ValueError):
        test_app.get_method("test")


def test_add_method(test_app: JsonRPC2):
    def add(num1, num2):
        pass

    test_app.add_method(add)
    assert 'add' in test_app.methods
    assert len(test_app.methods) == 1


def test_add_method_with_restrict_mode(test_app: JsonRPC2):
    with pytest.raises(ValueError):
        global duplicate_add
        test_app.add_method(duplicate_add)

        def duplicate_add():
            pass

        test_app.add_method(duplicate_add)


def test_send_response(test_app: JsonRPC2,
                       reader: MockStreamReader,
                       writer: MockStreamWriter):
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
