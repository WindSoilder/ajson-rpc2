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
from .errors import (
    ParseError, InvalidRequestError,
    MethodNotFoundError, InvalidParamsError,
    InternalError, JsonRPC2Error
)
from .request import Request, Notification
from .response import SuccessResponse, ErrorResponse
from .typedef import Union, Optional, Any


class JsonRPC2:
    '''
    Implementation of json-rpc2 protocol class
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
            error = self.check_errors(request_raw)
            if error:
                request_id = self.get_request_id(request_raw)
                if request_id:
                    response = ErrorResponse(error, request_id)
                    self.send_response(writer, response)
            else:
                response = None
                request_json = json.loads(request_raw)
                if 'id' in request_json:
                    request = Request(request_json['method'],
                                      request_json['params'],
                                      request_json['id'])
                else:
                    request = Notification(request_json['method'],
                                           request_json['params'])

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
        ''' get and return rpc method '''
        return self.methods[method_name]

    def add_method(self, method, restrict=True):
        ''' add method to json rpc, to make it rpc callable
        args:
            - method: which method to be rpc callable
            - restrict: controls the behavior when try to add method which have already
                        been added, if restrict is True, an exception will be raise when
                        user try to add an exist method.  Otherwise the method will be
                        overrided'''
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

    def get_request_id(self, request_raw: str) -> Optional[int]:
        ''' try to parse the raw input, and return request id,
        if it's not existed, return None '''
        search_result = re.search(r'"id"\s*:\s*"{0,1}(\d)+"{0,1}\s*', request_raw)
        id_group_index = 1

        if search_result:
            return search_result.group(id_group_index)
        return None

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
