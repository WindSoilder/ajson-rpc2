''' utils for json-rpc2 '''
import json
import inspect
from .typedef import JSON, Mapping, Optional


def is_json_invalid(json_str: str) -> bool:
    ''' return true if input is invalid JSON object '''
    try:
        json.loads(json_str)
    except json.decoder.JSONDecodeError as e:
        return True
    return False


def is_request_invalid(json: JSON) -> bool:
    ''' return true if input is invalid json-rpc2 request object '''
    REQUIRED_MEMBERS = set(["jsonrpc", "method"])
    VALID_MEMBERS = set(["jsonrpc", "method", "id", "params"])

    if not REQUIRED_MEMBERS.issubset(json.keys()):
        return True
    for key in json.keys():
        if key not in VALID_MEMBERS:
            return True
    return False


def is_method_not_exist(method: str, rpc_methods: Mapping) -> bool:
    ''' return true if the method is not exist '''
    return method not in rpc_methods


def is_params_invalid(method, params: Optional[dict, list]) -> bool:
    ''' return true if arguments if not valid for method '''
    return False
