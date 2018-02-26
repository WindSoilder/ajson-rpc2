''' json-rpc2 implementation base on asyncio '''
import json
import logging

from .utils import (
    is_json_invalid, is_method_not_exist,
    is_request_invalid, is_params_invalid
)
from .errors import (
    ParseError, InvalidRequestError,
    MethodNotFoundError, InvalidParamsError,
    InternalError, JsonRPC2Error
)
from .request import Request, Notification
from .response import SuccessResponse, ErrorResponse
from .typedef import Union, Optional


class JsonRPC2:
    '''
    Implementation of json-rpc2 protocol class
    '''
    def __init__(self, loop):
        self.loop = loop
        self.methods = {}

    async def handle_client(self, reader, writer):
        peer = writer.get_extra_info('socket').getpeername()
        logging.info(f'got a connection from {peer}')
        try:
            await self.handle_rpc_call(reader, writer)
        except Exception as e:
            logging.error(f'error {e} from {peer}')
        else:
            logging.info(f'end connection from {peer}')
        finally:
            writer.close()

    async def handle_rpc_call(self, reader, writer):
        while True:
            request_raw = await self.read(reader)
            if not request_raw:
                break   # Client close connection, Clean close
            error = self.check_errors(request_raw)
            if error:
                request_id = self.get_request_id(request_raw)
                if request_id:
                    response = ErrorResponse(error, request_id)
                    self.send_response(writer, response)
            else:
                request_json = json.loads(request_raw)
                if 'id' in request_json:
                    request = Request(request_json['method'],
                                      request_json['params'],
                                      request_json['id'])
                else:
                    request = Notification(request_json['method'],
                                           request_json['params'])

                try:
                    result = await self.invoke_method(request)
                except InternalError as e:
                    # there is an error during the method executing procedure
                    response = ErrorResponse(e, request.id)
                except Exception as e:
                    response = ErrorResponse(e, request.id)
                else:
                    response = SuccessResponse(result, request.id)
                finally:
                    # send response back to client
                    # Note that only send for the client Request, not Notification
                    if isinstance(request, Request):
                        self.send_response(writer, response)

    async def read(self, reader):
        ''' read a request from client '''
        return await reader.readline()

    async def invoke_method(self, request: Union[Request, Notification]):
        ''' invoke a rpc-method according to request,
        assume that the request is always valid
        which means that the request emthod exist, and argument is valid too '''
        method = self.get_method(request.method)
        logging.info(f'going to invoke method {request.method}')
        if isinstance(request.params, dict):
            result = await method(**request.params)
        elif isinstance(request.params, list):
            result = await method(*request.params)
        else:
            # the method have no parameter
            result = await method()
        if isinstance(request, Request):
            return result

    def get_method(self, method_name: str):
        ''' get and return rpc method '''
        return self.methods[method_name]

    def add_method(self, method, restrict=True):
        ''' add method to json rpc, to make it rpc callable
        '''
        if restrict and method.__name__ in self.methods:
            raise ValueError("The method is existed")
        else:
            self.methods[method.__name__] = method

    def send_response(self, writer,
                      response: Union[SuccessResponse, ErrorResponse]):
        ''' send json-rpc2 response back to client '''
        # extract the response object to json-dict
        pass

    def get_request_id(self, request_raw: str):
        ''' try to parse the raw input, and return request id,
        if it's not existed, return None '''
        pass

    def check_errors(self, request_raw: str) -> Optional[JsonRPC2Error]:
        ''' check if there are any errors in the raw of request,
        if so, return an error object, else return None '''
        if is_json_invalid(request_raw):
            return ParseError("Parse Error")
        request_json = json.loads(request_raw)
        if is_request_invalid(request_json):
            return InvalidRequestError("Invalid Request")
        if is_method_not_exist(request_json['method'], self.methods):
            return MethodNotFoundError("Method not found")
        method = self.get_method(request_json['method'])
        if is_params_invalid(method, request_json['params']):
            return InvalidParamsError("Invalid params")
        return None
