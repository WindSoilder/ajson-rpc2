''' test for util module '''
import pytest
from .context import (
    is_json_invalid, is_method_not_exist,
    is_params_invalid, is_request_invalid
)


@pytest.fixture
def request():
    return {
        "method": "substract",
        "id": 2,
        "jsonrpc": "2.0",
        "params": [1, 2]
    }


@pytest.fixture
def keyword_params_request():
    return {
        "method": "substract",
        "id": 2,
        "jsonrpc": "2.0",
        "params": {
            "num1": 4,
            "num2": 2
        }
    }


def rpc_call(num1, num2, num3, num4=1000, num5=2000):
    return num1 + num2 + num3 - num4 - num5


def simple_rpc_call(num1, num2):
    return num1 - num2


def test_is_json_invalid():
    assert is_json_invalid('{"foo": "bar"}') is False
    assert is_json_invalid("{'foo': 'bar'}") is True


def test_is_json_invalid_with_empty_val():
    assert is_json_invalid("") is True
    assert is_json_invalid(None) is True


def test_is_request_invalid(request):
    invalid_test_data = {'name': 'zero'}
    assert is_request_invalid(invalid_test_data) is True
    assert is_request_invalid(request) is False


def test_is_request_invalid_when_id_not_exist(request):
    request.pop('id')
    assert is_request_invalid(request) is False


def test_is_request_invalid_when_jsonrpc_not_exist(request):
    request.pop('jsonrpc')
    assert is_request_invalid(request) is True


def test_is_request_invalid_when_method_not_exist(request):
    request.pop('method')
    assert is_request_invalid(request) is True


def test_is_request_invalid_when_params_not_exist(request):
    request.pop('params')
    assert is_request_invalid(request) is False


def test_is_request_invalid_when_given_not_recognize_key(request):
    request['foo'] = 'bar'
    assert is_request_invalid(request) is True


def test_is_method_not_exist():
    def substract(num1, num2):
        return num1 - num2

    rpc_methods = {
        substract.__name__: substract
    }
    existed_method_name = 'substract'
    unexisted_method_name = 'add'

    assert is_method_not_exist(existed_method_name, rpc_methods) is False
    assert is_method_not_exist(unexisted_method_name, rpc_methods) is True


def test_is_params_invalid():
    less_params = [1]
    valid_params = [1, 2]
    more_params = [1, 2, 3]

    assert is_params_invalid(simple_rpc_call, less_params) is True
    assert is_params_invalid(simple_rpc_call, valid_params) is False
    assert is_params_invalid(simple_rpc_call, more_params) is True


def test_is_param_invalid_for_keyword_args_function():
    valid_params = {
        'num1': 1,
        'num2': 2
    }
    less_params = {
        'num1': 1
    }
    more_params = {
        'num1': 1,
        'num2': 2,
        'num3': 3
    }

    assert is_params_invalid(simple_rpc_call, less_params) is True
    assert is_params_invalid(simple_rpc_call, valid_params) is False
    assert is_params_invalid(simple_rpc_call, more_params) is True


def test_is_params_invalid_for_default_value_functions():
    less_params = [1]
    valid_params_tuple = (
        [1, 2, 3],
        [1, 2, 3, 4],
        [1, 2, 3, 4, 5]
    )
    more_params = [1, 2, 3, 4, 5, 6]

    assert is_params_invalid(rpc_call, less_params) is True
    assert is_params_invalid(rpc_call, more_params) is True

    for valid_params in valid_params_tuple:
        assert is_params_invalid(rpc_call, valid_params_tuple) is False


def test_is_params_invalid_for_default_value_functions_with_keyword_arguments():
    less_params = {
        'num1': 3,
        'num2': 5
    }

    valid_params_tuple = (
        {
            'num1': 3, 'num2': 4, 'num3': 5
        },
        {
            'num1': 3, 'num2': 4, 'num3': 5, 'num4': 5
        },
        {
            'num1': 3, 'num2': 4, 'num3': 5, 'num4': 6, 'num5': 7
        }
    )

    more_params_tuple = (
        {
            'num1': 3, 'num2': 4, 'num3': 5, 'num4': 10, 'num5': 8, 'num6': 12
        },
        {
            'num1': 3, 'num2': 4, 'num3': 5, 'num7': 9
        }
    )

    assert is_params_invalid(rpc_call, less_params) is True

    for valid_params in valid_params_tuple:
        assert is_params_invalid(rpc_call, valid_params) is False

    for more_params in more_params_tuple:
        assert is_params_invalid(rpc_call, more_params) is True
