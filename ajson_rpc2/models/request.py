''' request module for json-rpc2, which contains Request(need server response) and Notification(doesn't need server response) '''
from ..typedef import List, Mapping, Union


class _BaseRequest:
    ''' base class for the request object, which contains the jsonrpc version '''
    JSONRPC = "2.0"

    @classmethod
    def from_dict(cls, req_json: Mapping):
        ''' method to convert from json object to request class,
        which should be implement by the sub class'''
        raise NotImplementedError()


class Request(_BaseRequest):
    '''
    A rpc call is represented by sending a Request object to a Server. The Request object has the following members:

    jsonrpc:
        A String specifying the version of the JSON-RPC protocol. MUST be exactly "2.0".
    method:
        A String containing the name of the method to be invoked. Method names that begin with the word rpc followed by a period character (U+002E or ASCII 46) are
        reserved for rpc-internal methods and extensions and MUST NOT be used for anything else.
    params:
        A Structured value that holds the parameter values to be used during the invocation of the method. This member MAY be omitted.
    id:
        An identifier established by the Client that MUST contain a String, Number, or NULL value if included. If it is not included it is assumed to be a notification.
        The value SHOULD normally not be Null [1] and Numbers SHOULD NOT contain fractional parts.

    The Server MUST reply with the same value in the Response object if included. This member is used to correlate the context between the two objects.'''

    def __init__(self, method: str, params: Union[List, Mapping], id: Union[int, str]):
        super(Request, self).__init__()
        self.method = method
        self.params = params
        self.req_id = id

    @classmethod
    def from_dict(cls, req_json: Mapping):
        if isinstance(req_json, dict) is False:
            raise TypeError(f'should use a dict object to convert to Request object')
        return cls(req_json['method'],
                   req_json.get('params', None),
                   req_json['id'])


class Notification(_BaseRequest):
    '''
    A Notification is a Request object without an "id" member. A Request object that is a Notification signifies the Client's lack of interest in the corresponding Response object, 
    and as such no Response object needs to be returned to the client. The Server MUST NOT reply to a Notification, including those that are within a batch request.

    Notifications are not confirmable by definition, since they do not have a Response object to be returned.
    As such, the Client would not be aware of any errors (like e.g. "Invalid params","Internal rror").'''

    def __init__(self, method: str, params: Union[List, Mapping]):
        super(Notification, self).__init__()
        self.method = method
        self.params = params

    @classmethod
    def from_dict(cls, req_json: Mapping):
        if isinstance(req_json, dict) is False:
            raise TypeError(f'should use a dict object to convert to Notification object')
        return cls(req_json['method'],
                   req_json.get('params', None))
