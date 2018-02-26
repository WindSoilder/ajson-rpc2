'''
json-rpc v2.0 defined errors
When a rpc call encounters an error, the Response Object MUST contain the error member with a value that is a Object with the following members:

code
    A Number that indicates the error type that occurred.
    This MUST be an integer.
message
    A String providing a short description of the error.
    The message SHOULD be limited to a concise single sentence.
data
    A Primitive or Structured value that contains additional information about the error.
    This may be omitted.
    The value of this member is defined by the Server (e.g. detailed error information, nested errors etc.).
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
