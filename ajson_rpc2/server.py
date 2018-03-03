''' json-rpc2 implementation base on asyncio '''
import json
import logging
import re
import asyncio
import functools

from .utils import (
    is_json_invalid, is_method_not_exist,
    is_request_invalid, is_params_invalid
)

from .models.errors import (
    ParseError, InvalidRequestError,
    MethodNotFoundError, InvalidParamsError,
    InternalError, JsonRPC2Error
)
from .models.request import Request, Notification
from .models.response import SuccessResponse, ErrorResponse
from .typedef import Union, Optional, Any, JSON


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
            loop = asyncio.get_event_loop()
        self.loop = loop

    async def handle_client(self, reader, writer):
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

    async def handle_rpc_call(self, reader, writer):
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
                response = ErrorResponse(ParseError("Parse Error"),
                                         None)
                self.send_response(writer,
                                   response)
            else:
                if isinstance(request_json, list):
                    await self.handle_batched_rpc_call(writer, request_json)
                else:
                    await self.handle_simple_rpc_call(writer, request_json)

    async def handle_simple_rpc_call(self, writer, request_json: JSON):
        error = self.check_errors(request_json)
        peer = writer.get_extra_info('socket').getpeername()
        if error:
            request_id = self.get_request_id(request_json, error)
            response = ErrorResponse(error, request_id)
            self.send_response(writer, response)
        else:
            response = None
            if 'id' in request_json:
                request = Request.from_dict(request_json)
            else:
                request = Notification.from_dict(request_json)

            try:
                logging.info(f"from {peer}: route to method success, going to invoke it")
                result = await self.invoke_method(request)
            except Exception as e:
                # there is an error during the method executing procedure
                # defined by json rpc2, we need to expose it as InternalError
                logging.error(f"from {peer}: invoke method {request.method} failure")
                exc = InternalError(e.args)
                response = ErrorResponse(exc, request.req_id)
                if isinstance(request, Request):
                    self.send_response(writer, response)
            else:
                logging.info(f"from {peer}: invoke method {request.method} success")
                response = SuccessResponse(result, request.req_id)
                if isinstance(request, Request):
                    self.send_response(writer, response)

    async def handle_batched_rpc_call(self, writer, request_json: JSON):
        pass

    async def read(self, reader) -> bytes:
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
            self.methods[method_name]
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

    def send_response(self, writer,
                      response: Union[SuccessResponse, ErrorResponse]):
        ''' send json-rpc2 response back to client '''
        # extract the response object to json-dict
        if isinstance(response, ErrorResponse):
            # if there is an error happened during the rpc-call
            self._send_err_response(writer, response)
        else:
            self._send_response(writer, response)

    def get_request_id(self, request_json: JSON, err: ErrorResponse) -> Union[str, int]:
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
        if is_params_invalid(method, request_json['params']):
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

    def _send_err_response(self, writer, response: ErrorResponse):
        response_body = {}
        response_body["error"] = {
            "code": response.error.err_code,
            "message": response.error.args[0]
        }
        response_body["jsonrpc"] = response.JSONRPC
        response_body["id"] = response.resp_id
        writer.write(json.dumps(response_body).encode())

    def _send_response(self, writer, response: SuccessResponse):
        response_body = response.__dict__
        response_body["jsonrpc"] = response.JSONRPC
        response_body["id"] = response.resp_id
        writer.write(json.dumps(response_body).encode())
