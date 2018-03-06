''' test for the error object
to make sure that the error object contains
proper error code '''
from ..context import (
    ParseError, InvalidRequestError,
    MethodNotFoundError, InvalidParamsError,
    InternalError
)


def test_parse_error_code():
    assert ParseError.err_code == -32700


def test_invalid_params_err_code():
    assert InvalidParamsError.err_code == -32602


def test_method_not_found_err_code():
    assert MethodNotFoundError.err_code == -32601


def test_invalid_request_err_code():
    assert InvalidRequestError.err_code == -32600


def test_internal_error_code():
    assert InternalError.err_code == -32603
