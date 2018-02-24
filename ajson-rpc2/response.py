''' response module for json-rpc2 '''
from .errors import JsonRPC2Error


class _Response:
    ''' base response class from json-rpc2 server '''
    JSONRPC = "2.0"

    def __init__(self, id: int):
        self.resp_id = id


class SuccessResponse(_Response):
    ''' response object for no errors '''

    def __init__(self, result: str, id: int):
        super(SuccessResponse, self).__init__(id)
        self.result = result


class ErrorResponse(_Response):
    ''' response object for errors '''

    def __init__(self, error: JsonRPC2Error, id: int):
        super(ErrorResponse, self).__init__(id)
        self.error = error
