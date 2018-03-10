import pytest
from ..context import (
    SuccessResponse, ErrorResponse,
    FixedList, BatchResponse, MethodNotFoundError
)


def test_init_empty_batch_response():
    responses = BatchResponse()
    assert isinstance(responses.successes, FixedList) is True
    assert isinstance(responses.errors, FixedList) is True


def test_init_batch_response():
    response_list = FixedList(SuccessResponse)
    error_list = FixedList(ErrorResponse)

    response_list.append(SuccessResponse(3, 4))
    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 3))

    responses = BatchResponse(response_list, error_list)
    assert responses.successes is response_list
    assert responses.errors is error_list


def test_batch_response_to_json():
    response_list = FixedList(SuccessResponse)
    error_list = FixedList(ErrorResponse)

    response_list.append(SuccessResponse(3, 4))
    response_list.append(SuccessResponse(4, 5))
    response_list.append(SuccessResponse("test_result", 10))

    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 4))
    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 3))

    responses = BatchResponse(response_list, error_list)

    resp_json = responses.to_json()

    assert resp_json == [
        {"result": 3, "id": 4, "jsonrpc": "2.0"},
        {"result": 4, "id": 5, "jsonrpc": "2.0"},
        {"result": "test_result", "id": 10, "jsonrpc": "2.0"},
        {"id": 4, "error": {"code": -32601, "message": "Method not found"}, "jsonrpc": "2.0"},
        {"id": 3, "error": {"code": -32601, "message": "Method not found"}, "jsonrpc": "2.0"}
    ]


def test_batch_response_to_json_with_only_success():
    response_list = FixedList(SuccessResponse)

    response_list.append(SuccessResponse(3, 4))
    responses = BatchResponse(response_list)

    resp_json = responses.to_json()
    assert resp_json == [
        {"result": 3, "id": 4, "jsonrpc": "2.0"}
    ]


def test_batch_response_to_json_with_only_error():
    error_list = FixedList(ErrorResponse)

    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 4))
    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 3))

    responses = BatchResponse(errors=error_list)

    resp_json = responses.to_json()
    assert resp_json == [
        {"id": 4, "error": {"code": -32601, "message": "Method not found"}, "jsonrpc": "2.0"},
        {"id": 3, "error": {"code": -32601, "message": "Method not found"}, "jsonrpc": "2.0"}
    ]


def test_batch_response_to_json_with_empty():
    responses = BatchResponse()

    resp_json = responses.to_json()
    assert resp_json == []


def test_append_success_response():
    responses = BatchResponse()
    success_resp = SuccessResponse(3, 4)
    responses.append(success_resp)

    assert len(responses.successes) == 1
    assert len(responses.errors) == 0
    assert responses.successes[-1] is success_resp


def test_append_error_response():
    responses = BatchResponse()
    error = ErrorResponse(MethodNotFoundError("Method not found"), 4)

    responses.append(error)

    assert len(responses.successes) == 0
    assert len(responses.errors) == 1
    assert responses.errors[-1] is error


def test_append_other_things():
    responses = BatchResponse()

    with pytest.raises(TypeError):
        responses.append(3)


def test_len_method_on_batch_response():
    responses = BatchResponse()
    assert len(responses) == 0

    success_resp = SuccessResponse(3, 4)
    responses.append(success_resp)

    error = ErrorResponse(MethodNotFoundError("Method not found"), 4)
    responses.append(error)

    assert len(responses) == 2


def test_batch_response_iterable():
    response_list = FixedList(SuccessResponse)
    error_list = FixedList(ErrorResponse)

    response_list.append(SuccessResponse(3, 4))
    response_list.append(SuccessResponse(4, 5))
    response_list.append(SuccessResponse("test_result", 10))

    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 4))
    error_list.append(ErrorResponse(MethodNotFoundError("Method not found"), 3))

    responses = BatchResponse(response_list, error_list)

    response_index = 0
    success_resp_length = len(response_list)
    for response in responses:
        if response_index < success_resp_length:
            assert isinstance(response, SuccessResponse)
        else:
            assert isinstance(response, ErrorResponse)
        response_index += 1
