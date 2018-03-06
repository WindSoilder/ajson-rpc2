''' json-rpc2 implementation base on asyncio '''
import json
import logging
import asyncio
import functools
from asyncio import StreamReader, StreamWriter

from .utils import (
    is_method_not_exist,
    is_request_invalid, is_params_invalid
)

from .models.errors import (
    ParseError, InvalidRequestError,
    MethodNotFoundError, InvalidParamsError,
    InternalError, JsonRPC2Error
)
from .models.request import Request, Notification
from .models.response import SuccessResponse, ErrorResponse, _Response
from .models.batch_response import BatchResponse
from .typedef import Union, Optional, Any, JSON, List


class JsonRPC2:
    '''
    Implementation of json-rpc2 protocol class
    Usage example::

        from ajson_rpc2 import JsonRPC2

        server = JsonRPC2()

        # make one function to be rpc called
        @server.rpc_call
        def substract(num1, num2):
            return num1 - num2

        # also support for the async rpc call
        @server.rpc_call
        async def io_bound_call(num1):
            await asyncio.sleep(3)
            return num1

        server.start(port=9999)

    :param loop: an instance of asyncio event loop, if the loop is None, the JsonRPC2 will
                 use default loop provided by asyncio, we can provide more powerful event
                 loop to the JsonRPC2 (like uvloop)
    '''
    def __init__(self, loop=None):
        self.methods = {}
        if loop is None:
            loop = asyncio.new_event_loop()
        self.loop = loop

    async def handle_client(self, reader: StreamReader, writer: StreamWriter):
        ''' main handler for each client connection '''
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

    async def handle_rpc_call(self, reader: StreamReader, writer: StreamWriter):
        while True:
            peer = writer.get_extra_info('socket').getpeername()
            request_raw = await self.read(reader)
            logging.info(f"get data from {peer}")
            if not request_raw:
                break   # Client close connection, Clean close
            request_raw = request_raw.decode()

            # check for invalid json first
            request_json = None
            try:
                request_json = json.loads(request_raw)
            except (json.JSONDecodeError, TypeError) as e:
                response = ErrorResponse(ParseError("Parse error"),
                                         None)
                self.send_response(writer,
                                   response)
            else:
                if isinstance(request_json, list):
                    response = await self.handle_batched_rpc_call(writer, request_json)
                else:
                    response = await self.handle_simple_rpc_call(writer, request_json)

                if response:
                    self.send_response(writer, response)

    async def handle_simple_rpc_call(self, request_json: JSON) -> Optional[_Response]:
        ''' handle for a request, and return a response object(if it need result) '''
        error = self.check_errors(request_json)

        if error:
            request_id = self.get_request_id(request_json, error)
            response = ErrorResponse(error, request_id)
            return response
        else:
            response = None
            if 'id' in request_json:
                request = Request.from_dict(request_json)
            else:
                request = Notification.from_dict(request_json)

            try:
                result = await self.invoke_method(request)
            except Exception as e:
                # there is an error during the method executing procedure
                # defined by json rpc2, we need to expose it as InternalError
                exc = InternalError("Internal error")
                response = ErrorResponse(exc, request.req_id)
                if isinstance(request, Request):
                    return response
            else:
                response = SuccessResponse(result, request.req_id)
                if isinstance(request, Request):
                    return response

    async def handle_batched_rpc_call(self, request_json: List) -> Union[ErrorResponse, BatchResponse, None]:
        ''' handle for batched request, but there are something to noted:
        1. When receive an empty array, server will return a Response
        2. When receive array with one element, but the request is Invalid Request,
           server will return a BatchResponse with one element
        3. if all requests are Notifications, server will response nothing'''
        # handle for empty array
        if len(request_json) == 0:
            response = ErrorResponse(InvalidRequestError("Invalid Request"),
                                     None)
            return response
        batch_response = BatchResponse()
        for req in request_json:
            response = await self.handle_simple_rpc_call(req)
            if response:
                batch_response.append(response)
        if len(batch_response) != 0:
            return batch_response
        return None

    async def read(self, reader: StreamReader) -> bytes:
        ''' read a request from client
        it's needed to return the content of json body'''
        return await reader.readline()

    async def invoke_method(self, request: Union[Request, Notification]) -> Any:
        ''' invoke a rpc-method according to request,
        assume that the request is always valid
        which means that the request emthod exist, and argument is valid too '''
        method = self.get_method(request.method)
        logging.info(f'going to invoke method {request.method}')
        if isinstance(request.params, dict):
            result = method(**request.params)
        elif isinstance(request.params, list):
            result = method(*request.params)
        else:
            # the method have no parameter
            result = method()

        if asyncio.iscoroutine(result):
            # await the method and extract the result out
            result = await result
        if isinstance(request, Request):
            return result

    def get_method(self, method_name: str):
        ''' get and return rpc method,
        if the method is not existed, a ValueError will occured'''
        try:
            return self.methods[method_name]
        except KeyError as e:
            raise ValueError(f'The method "{method_name}" is not registered in the Server')

    def add_method(self, method, restrict=True):
        ''' add method to json rpc, to make it rpc callable

        :param method: which method to be rpc callable
        :param restrict: controls the behavior when try to add method which have already
                         been added, if restrict is True, an exception will be raise when
                         user try to add an exist method.  Otherwise the method will be
                         overrided
        '''
        if restrict and method.__name__ in self.methods:
            raise ValueError("The method is existed")
        else:
            self.methods[method.__name__] = method

    def send_response(self, writer: StreamWriter,
                      response: Union[SuccessResponse, ErrorResponse, BatchResponse]):
        ''' send json-rpc2 response back to client '''
        # extract the response object to json-dict
        logging.info(response)
        resp_body = response.to_json()
        logging.info(resp_body)
        writer.write(json.dumps(resp_body).encode() + b'\n')

    def get_request_id(self, request_json: JSON, err: JsonRPC2Error) -> Union[str, int]:
        ''' when an error is detected,
        try to parse the json input, and return request id,
        if the error is ParseError or InvalidRequest, it should return None'''
        if isinstance(err, ParseError) or \
           isinstance(err, InvalidRequestError):
            return None
        return request_json['id']

    def check_errors(self, request_json: JSON) -> Optional[JsonRPC2Error]:
        ''' check if there are any errors in the raw of request,
        if so, return an error object, else return None '''
        if is_request_invalid(request_json):
            return InvalidRequestError("Invalid Request")
        if is_method_not_exist(request_json['method'], self.methods):
            return MethodNotFoundError("Method not found")
        method = self.get_method(request_json['method'])

        if is_params_invalid(method, request_json.get('params', None)):
            return InvalidParamsError("Invalid params")
        return None

    def rpc_call(self, func):
        '''
        decorator function to make a function rpc_callable
        examples:
            # make one function to be rpc called
            @server.rpc_call
            def substract(num1, num2):
                return num1 - num2

            # also support for the async rpc call
            @server.rpc_call
            async def io_bound_call(num1):
                await asyncio.sleep(3)
                return num1
        '''
        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)
        self.add_method(func)
        return wrapped

    def start(self, port: int = 8080):
        ''' start the server and listen to client '''
        server = asyncio.start_server(self.handle_client, port=port, loop=self.loop)
        server = self.loop.run_until_complete(server)
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()
