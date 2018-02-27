''' test for util module '''
from .context.utils import (
    is_json_invalid, is_method_not_exist,
    is_params_invalid, is_request_invalid
)


def test_is_json_invalid():
    assert is_json_invalid('{"foo": "bar"}') is False
    assert is_json_invalid("{'foo': 'bar'}") is True


def test_is_json_invalid_with_empty_val():
    assert is_json_invalid("") is True
    assert is_json_invalid(None) is True


def test_is_request_invalid():
    pass


def test_is_request_invalid_when_id_not_exist():
    pass


def test_is_request_invalid_when_jsonrpc_not_exist():
    pass


def test_is_request_invalid_when_method_not_exist():
    pass


def test_is_request_invalid_when_params_not_exist():
    pass


def test_is_request_invalid_when_given_not_recognize_key():
    pass


def test_is_method_not_exist():
    pass


def test_is_params_invalid():
    pass


def test_is_param_invalid_for_keyword_args_function():
    pass


def test_is_param_invalid_for_position_args_to_defaults_values():
    pass


def test_is_params_invalid_for_keyword_args_to_defaults_values():
    pass
