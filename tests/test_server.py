import pytest
import json
from queue import Queue

from .context import (
    JsonRPC2,
    InvalidParamsError, InvalidRequestError, MethodNotFoundError,
    ParseError, InternalError,
    SuccessResponse, ErrorResponse,
)

mock_queue = Queue()


class MockStreamReader:
    async def readline(self):
        global mock_queue
        return mock_queue.get()


class MockStreamWriter:
    def write(self, content):
        global mock_queue
        mock_queue.put(content)


@pytest.fixture
def test_app():
    return JsonRPC2()


@pytest.fixture
def reader():
    return MockStreamReader()


@pytest.fixture
def writer():
    return MockStreamWriter()


# for now it still lack tests for handle rpc_call method
# and handle_client method

def test_init_server_with_other_eventloop():
    pass


def test_handle_simple_rpc_call(test_app: JsonRPC2):
    pass


def test_handle_simple_rpc_call_with_error(test_app: JsonRPC2):
    pass


def test_handle_notification(test_app: JsonRPC2):
    pass


def test_simple_rpc_call_with_internal_error(test_app: JsonRPC2):
    pass


def test_handle_batched_rpc_call(test_app: JsonRPC2):
    pass


def test_handle_empty_batched(test_app: JsonRPC2):
    pass


def test_handle_one_batched_call(test_app: JsonRPC2):
    pass


def test_handle_batched_call_with_all_notifications(test_app: JsonRPC2):
    pass


def test_read(test_app: JsonRPC2):
    pass


def test_invoke_method(test_app: JsonRPC2):
    pass


def test_invoke_method_with_keyword_parameter(test_app: JsonRPC2):
    pass


def test_invoke_no_parameter_method(test_app: JsonRPC2):
    pass


def test_invoke_async_method(test_app: JsonRPC2):
    pass


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
    pass


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
