''' utils for json-rpc2 '''
import json
import inspect
from .typedef import JSON, Mapping, Union


def is_json_invalid(json_str: str) -> bool:
    ''' return true if input is invalid JSON object '''
    try:
        json.loads(json_str)
    except (json.decoder.JSONDecodeError, TypeError) as e:
        return True
    return False


def is_request_invalid(json: JSON) -> bool:
    ''' return true if input is invalid json-rpc2 request object '''
    # the request may be not dict type
    if isinstance(json, dict) is False:
        return True

    REQUIRED_MEMBERS = set(["jsonrpc", "method"])
    VALID_MEMBERS = set(["jsonrpc", "method", "id", "params"])

    if not REQUIRED_MEMBERS.issubset(json.keys()):
        return True
    for key in json.keys():
        if key not in VALID_MEMBERS:
            return True
    if isinstance(json['method'], str) is False:
        return True
    return False


def is_method_not_exist(method: str, rpc_methods: Mapping) -> bool:
    ''' return true if the method is not been registered '''
    return method not in rpc_methods


def is_params_invalid(method, params: Union[dict, list, None]) -> bool:
    ''' return true if arguments if not valid for method '''
    method_args = inspect.getfullargspec(method)
    if isinstance(params, list):
        if method_args.defaults is None:
            return len(params) != len(method_args.args)
        else:
            if len(params) <= len(method_args.args) and \
               len(params) >= len(method_args.args) - len(method_args.defaults):
                return False
            return True
    elif isinstance(params, dict):
        if method_args.defaults is None:
            cant_omit_args = method_args.args
        else:
            cant_omit_args = method_args.args[0:len(method_args.args) - len(method_args.defaults)]
        for arg in cant_omit_args:
            if arg not in params:
                # have not provide required parameter
                return True
        for param in params:
            if param not in method_args.args:
                # the given parameter contains somthing that the function doesn't know
                return True
        return False
    else:
        # don't provide any parameter, so check if the method
        # don't need any parameters
        if len(method_args.args) == 0:
            return False
        if method_args.defaults is not None:
            return len(method_args.args) - len(method_args.defaults) != 0
        return True
