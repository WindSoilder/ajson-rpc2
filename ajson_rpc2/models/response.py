''' response module for json-rpc2
When a rpc call is made, the Server MUST reply with a Response, except for in the case of Notifications.
The Response is expressed as a single JSON Object, with the following members:

jsonrpc
    A String specifying the version of the JSON-RPC protocol. MUST be exactly "2.0".

result
    This member is REQUIRED on success.
    This member MUST NOT exist if there was an error invoking the method.
    The value of this member is determined by the method invoked on the Server.

error
    This member is REQUIRED on error.
    This member MUST NOT exist if there was no error triggered during invocation.
    The value for this member MUST be an Object as defined in section 5.1.

id
    This member is REQUIRED.
    It MUST be the same as the value of the id member in the Request Object.
    If there was an error in detecting the id in the Request object (e.g. Parse error/Invalid Request), it MUST be Null.

Either the result member or error member MUST be included, but both members MUST NOT be included.
'''
from .errors import JsonRPC2Error


class _Response:
    ''' base class for the json rpc2 response object '''
    JSONRPC = "2.0"

    def __init__(self, id: int):
        self.resp_id = id

    def to_json(self):
        ''' convert the response object to a dict '''
        raise NotImplementedError()


class SuccessResponse(_Response):
    ''' response object for no errors '''

    def __init__(self, result: str, id: int):
        super(SuccessResponse, self).__init__(id)
        self.result = result

    def to_json(self) -> dict:
        return {
            "jsonrpc": self.JSONRPC,
            "id": self.resp_id or "null",
            "result": self.result
        }


class ErrorResponse(_Response):
    ''' response object for errors '''

    def __init__(self, error: JsonRPC2Error, id: int):
        super(ErrorResponse, self).__init__(id)
        self.error = error

    def to_json(self) -> dict:
        return {
            "jsonrpc": self.JSONRPC,
            "id": self.resp_id or "null",
            "error": self.error.to_dict()
        }
