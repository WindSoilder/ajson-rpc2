import pytest

from ..context import Request, Notification


def test_request_from_json_with_invalid_type():
    with pytest.raises(TypeError):
        Request.from_json([])


def test_request_from_json():
    req_json = {
        'method': 'test',
        'params': [1],
        'id': 3
    }
    req = Request.from_json(req_json)
    assert req.method == 'test'
    assert req.params == [1]
    assert req.req_id == 3


def test_request_from_json_with_no_params():
    req_json = {
        'method': 'test',
        'id': 4
    }
    req = Request.from_json(req_json)

    assert req.method == 'test'
    assert req.params is None
    assert req.req_id == 4


def test_notification_from_json():
    req_json = {
        'method': 'test',
        'params': [1]
    }
    req = Notification.from_json(req_json)

    assert req.method == 'test'
    assert req.params == [1]


def test_notification_from_json_with_wrong_type():
    with pytest.raises(TypeError):
        Notification.from_json([])


def test_notification_from_json_with_no_params():
    req_json = {
        'method': 'test'
    }

    req = Notification.from_json(req_json)

    assert req.method == 'test'
    assert req.params is None
