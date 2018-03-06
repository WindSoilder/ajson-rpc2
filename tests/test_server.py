import pytest
from queue import Queue

from .context import JsonRPC2

mock_queue = Queue()


class MockStreamReader:
    async def readline():
        global mock_queue
        return mock_queue.get()


class MockStreamWriter:
    async def write(content):
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

def test_handle_simple_rpc_call(test_app):
    pass


def test_handle_simple_rpc_call_with_error(test_app):
    pass


def test_handle_notification(test_app):
    pass


def test_simple_rpc_call_with_internal_error(test_app):
    pass


def test_handle_batched_rpc_call(test_app):
    pass


def test_handle_empty_batched(test_app):
    pass


def test_handle_one_batched_call(test_app):
    pass


def test_handle_batched_call_with_all_notifications(test_app):
    pass


def test_read(test_app):
    pass


def test_invoke_method(test_app):
    pass


def test_invoke_method_with_keyword_parameter(test_app):
    pass


def test_invoke_no_parameter_method(test_app):
    pass


def test_invoke_async_method(test_app):
    pass


def test_get_method(test_app):
    pass


def test_get_not_existed_method(test_app):
    pass


def test_add_method(test_app):
    pass


def test_add_method_with_restrict_mode(test_app):
    pass


def test_send_response(test_app, reader, writer):
    pass


def test_get_request_id(test_app):
    pass


def test_get_request_id_for_errors(test_app):
    pass


def test_check_invalid_request_errors(test_app):
    pass


def test_check_method_not_exist_errors(test_app):
    pass


def test_check_params_invalid_errors(test_app):
    pass


def test_check_no_errors(test_app):
    pass


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


def test_replace_rpc_call(test_app: JsonRPC2):
    pass


def test_replace_rpc_call_with_restrict_mode(test_app: JsonRPC2):
    pass
