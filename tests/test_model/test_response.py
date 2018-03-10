from ..context import (
    SuccessResponse, ErrorResponse,
    ParseError, MethodNotFoundError
)


def test_success_response_to_json():
    response = SuccessResponse(3, 5)
    response_json = response.to_json()
    assert response_json == {
        "jsonrpc": "2.0",
        "id": 5,
        "result": 3
    }


def test_err_response_to_json():
    err = MethodNotFoundError("Method not found")
    resp = ErrorResponse(err, "3")
    resp_json = resp.to_json()
    assert resp_json == {
        "jsonrpc": "2.0",
        "id": "3",
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }


def test_err_response_to_json_with_no_id():
    err = ParseError("Parse error")
    resp = ErrorResponse(err, None)
    resp_json = resp.to_json()
    assert resp_json == {
        "jsonrpc": "2.0",
        "id": "null",
        "error": {
            "code": -32700,
            "message": "Parse error"
        }
    }
