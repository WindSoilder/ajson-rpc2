import pytest

from ..context import (
    BatchRequest, FixedList,
    Request, Notification
)


def test_batch_request_initialize():
    requests = BatchRequest()
    assert isinstance(requests.requests, FixedList) is True
    assert isinstance(requests.notifications, FixedList) is True
    assert len(requests.requests) == 0
    assert len(requests.notifications) == 0


def test_batch_request_initialize_with_initial_requests_and_notifications():
    init_requests = FixedList(Request)
    init_requests.append(Request("test", [1, 2], 3))
    notifications = FixedList(Notification)
    notifications.append(Notification("test", None))
    requests = BatchRequest(init_requests, notifications)

    assert requests.requests is init_requests
    assert requests.notifications is notifications


def test_batch_request_from_json():
    req_json = [
        {"jsonrpc": "2.0", "method": "test", "id": 4, "params": [1, 2, 3]},
        {"jsonrpc": "2.0", "method": "test", "params": [1, 2, 4]},
        {"jsonrpc": "2.0", "method": "test", "id": 6, "params": [1, 5, 3]}
    ]

    requests = BatchRequest.from_json(req_json)

    assert len(requests.requests) == 2
    assert len(requests.notifications) == 1


def test_batch_request_from_json_with_all_request():
    req_json = [
        {"jsonrpc": "2.0", "method": "test", "id": 4, "params": [1, 2, 3]},
        {"jsonrpc": "2.0", "method": "test", "id": 5, "params": [1, 2, 4]},
        {"jsonrpc": "2.0", "method": "test", "id": 6, "params": [1, 5, 3]}
    ]

    requests = BatchRequest.from_json(req_json)
    assert len(requests.requests) == 3
    assert len(requests.notifications) == 0


def test_batch_request_from_json_with_all_notifications():
    req_json = [
        {"jsonrpc": "2.0", "method": "test", "params": [1, 2, 3]},
        {"jsonrpc": "2.0", "method": "test", "params": [1, 2, 4]},
        {"jsonrpc": "2.0", "method": "test", "params": [1, 5, 3]}
    ]

    requests = BatchRequest.from_json(req_json)
    assert len(requests.requests) == 0
    assert len(requests.notifications) == 3


def test_batch_request_with_empty_json():
    requests = BatchRequest.from_json([])
    assert len(requests.requests) == 0
    assert len(requests.notifications) == 0


def test_batch_request_from_json_wrong_type():
    with pytest.raises(TypeError):
        BatchRequest.from_json({})
