'''
json-rpc v2.0 defined errors
'''


class JsonRPC2Error(Exception):
    err_code = None


class ParseError(JsonRPC2Error):
    ''' Invalid JSON was received by the server
    This error occurred on the server while parsing the JSON text '''
    err_code = -32700


class InvalidRequestError(JsonRPC2Error):
    ''' The JSON sent is not a valid Request object '''
    err_code = -32600


class MethodNotFoundError(JsonRPC2Error):
    ''' The method does not exist / is not available '''
    err_code = -32601


class InvalidParamsError(JsonRPC2Error):
    ''' Invalid method parameter(s) '''
    err_code = -32602


class InternalError(JsonRPC2Error):
    ''' Internal JSON-RPC error '''
    err_code = -32603
