''' request module for json-rpc2, which contains Request(need server response) and Notification(doesn't need server response) '''
from .typedef import List, Mapping, Union


class _BaseRequest:
    ''' base class for the request object, which contains the jsonrpc version '''
    JSONRPC = "2.0"


class Request(_BaseRequest):
    ''' Represented a rpc call '''
    def __init__(self, method: str, params: Union[List, Mapping], id: Union[int, str]):
        super(Request, self).__init__()
        self.method = method
        self.params = params
        self.req_id = id


class Notification(_BaseRequest):
    ''' A Notification is a Request object without an "id" member.
    A Request object that is a Notification signifies the Client's lack of interest in the corresponding Response object,
    and as such no Response object needs to be returned to the client. '''
    def __init__(self, method: str, params: Union[List, Mapping]):
        super(Request, self).__init__()
        self.method = method
        self.params = params
