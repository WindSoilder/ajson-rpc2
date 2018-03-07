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
    class _ConnectionInfo:
        def getpeername(self):
            pass

    def write(self, content):
        global mock_queue
        mock_queue.put(content)

    def close(self):
        ''' mock close will empty the queue '''
        global mock_queue
        mock_queue = Queue()

    def get_extra_info(self, info):
        return self._ConnectionInfo()


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


def test_handle_client(test_app: JsonRPC2, reader: MockStreamReader, writer: MockStreamWriter):
    # for testing handle_client method
    # the inner method handle_rpc_call is not what we interested
    # so mock the function to make test_app call
    async def mock_handle_rpc_call(reader, writer):
        pass

    setattr(test_app, "handle_rpc_call", mock_handle_rpc_call)
    test_app.loop.run_until_complete(test_app.handle_client(reader, writer))


def test_handle_client_for_client_error(test_app: JsonRPC2, reader: MockStreamReader, writer: MockStreamWriter):
    # for testing handle_client method
    # the inner method handle_rpc_call is not what we interested
    # so mock the function to make test_app call
    async def mock_handle_error_rpc_call(reader, writer):
        1 / 0

    setattr(test_app, "handle_rpc_call", mock_handle_error_rpc_call)

    test_app.loop.run_until_complete(test_app.handle_client(reader, writer))


def test_handle_rpc_call(test_app: JsonRPC2, reader: MockStreamReader, writer: MockStreamWriter):
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


def test_handle_rpc_call_with_invalid_json(test_app: JsonRPC2, reader: MockStreamReader, writer: MockStreamWriter):
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
def test_handle_rpc_call_with_batched_request(test_app: JsonRPC2, reader: MockStreamReader, writer: MockStreamWriter):
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


def test_start():
    # here we will create a mock loop
    # to test the logic of start
    class MockLoop(asyncio.AbstractEventLoop):
        def __init__(self):
            self.have_invoke_run_until_complete = False
            self.have_invoke_run_forever = False
            self.have_invoke_close = False

        def run_until_complete(self, coroutine):
            self.have_invoke_run_until_complete = True

        def run_forever(self):
            self.have_invoke_run_forever = True

        def close(self):
            self.have_invoke_close = True

    loop = MockLoop()
    test_app = JsonRPC2(loop)

    test_app.start()

    assert loop.have_invoke_run_until_complete is True
    assert loop.have_invoke_run_forever is True
    assert loop.have_invoke_close is True
