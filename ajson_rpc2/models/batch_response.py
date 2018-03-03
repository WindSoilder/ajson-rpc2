''' When server receive batch requests from client
The Server should respond with an Array containing the corresponding Response objects, 
after all of the batch Request objects have been processed.
A Response object SHOULD exist for each Request object, except that there SHOULD NOT be any Response objects for notifications.

If the batch rpc call itself fails to be recognized as an valid JSON or as an Array with at least one value,
the response from the Server MUST be a single Response object.
If there are no Response objects contained within the Response array as it is to be sent to the client,
the server MUST NOT return an empty Array and should return nothing at all.
'''
from ..typedef import Union, List
from .response import SuccessResponse, ErrorResponse
from .fixed_list import FixedList


class BatchResponse:
    '''
    BatchResponse represent the response
    to several rpc-call at the same time
    '''
    def __init__(self):
        self.successes = FixedList(SuccessResponse)
        self.errors = FixedList(ErrorResponse)

    def to_json(self) -> List:
        result_list = []
        for success in self.successes:
            result_list.append(success.to_json())
        for error in self.errors:
            result_list.append(error.to_json())
        return result_list

    def append(self, resp: Union[SuccessResponse, ErrorResponse]):
        if isinstance(resp, SuccessResponse):
            self.successes.append(resp)
        else:
            self.errors.append(resp)
