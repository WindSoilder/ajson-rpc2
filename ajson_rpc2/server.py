''' json-rpc2 implementation base on asyncio '''
import json
import logging
import asyncio
import functools
import re
from asyncio import StreamReader, StreamWriter, Future, AbstractEventLoop
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

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
from .module import Module
from .method import RpcMethod, ExtraNeed
from .container import _MethodContainer
from .typedef import Union, Optional, Any, JSON, List, Callable


class _RequestGroup:
    def __init__(self,
                 simple: List = None,
                 process: List = None,
                 thread: List = None):
        self.simple_requests = simple or []
        self.process_requests = process or []
        self.thread_requests = thread or []


class JsonRPC2(_MethodContainer):
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
    :param process_executor: an instance of concurrent.futures.ProcessPoolExecutor, you can
                             pass it to the server, when server is calling CPU-bound method,
                             it will be executed in another process by this executor.  Defaults
                             is None, which will make Server create a ProcessPoolExecutor with 4
                             max workers
    :param thread_executor: an instance of concurrent.futures.ThreadPoolExecutor, you can
                            pass it to the server, when server is calling IO-bound method,
                            it will be executed in another process by this executor  Defaults
                            is None, which will make Server create a ThreadPoolExecutor with 4
                            max workers
    .. versionadded:: 0.3
       The process_executor and thread_executor parameters were added
    '''
    def __init__(self,
                 loop: AbstractEventLoop = None,
                 process_executor: ProcessPoolExecutor = None,
                 thread_executor: ThreadPoolExecutor = None):
        super(JsonRPC2, self).__init__()
        if loop is None:
            # asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            loop = asyncio.new_event_loop()
        if process_executor is None:
            process_executor = ProcessPoolExecutor(max_workers=4)
        if thread_executor is None:
            thread_executor = ThreadPoolExecutor(max_workers=4)

        self.loop = loop
        self.process_executor = process_executor
        self.thread_executor = thread_executor
        self.modules = {}

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
        ''' handle rpc call async '''
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
                    response = await self.handle_batched_rpc_call(request_json)
                else:
                    response = await self.handle_simple_rpc_call(request_json)

                if response:
                    self.send_response(writer, response)

    async def handle_simple_rpc_call(self, request_json: JSON) -> Optional[_Response]:
        ''' handle for a request, and return a response object(if it need result) '''
        error = self.check_errors(request_json)
        if error:
            return self._generate_error_response(request_json, error)

        request = self._parse_request(request_json)
        try:
            result = await self.invoke_method(request)
        except Exception as e:
            # there is an error during the method executing procedure
            # defined by json rpc2, we need to expose it as InternalError
            response = self._generate_error_response(request_json, InternalError("Internal error"))
        else:
            if isinstance(request, Request):
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

        request_group = self._group_requests(request_json)

        # process requests
        thread_responses = self._handle_thread_requests(request_group.thread_requests)

        # In ProcessPoolExecutor, we can only submit pickle object,
        # which include function but not instance method.  So we have to run only rpc_method
        # in another process.  Which is different to multi thread programming
        # and it's more complicate than ThreadPoolExecutor
        [process_responses, process_errors] = self._handle_process_requests(request_group.process_requests)

        # add errors to batch responses
        for process_error in process_errors:
            batch_response.append(process_error)

        # wait for multi-processing response
        if len(process_responses) > 0:
            rpc_call_results = await asyncio.wait(process_responses)
            rpc_call_responses = self._convert_to_response(rpc_call_results)

            for result in rpc_call_responses:
                batch_response.append(result)

        # wait for multi-threading response
        if len(thread_responses) > 0:
            rpc_call_responses = await asyncio.wait(thread_responses)

            for result in rpc_call_responses[0]:
                batch_response.append(result.result())

        # handle for rpc method which doesn't have special need resource
        # it can be asynchronous function
        for req in request_group.simple_requests:
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

    def _invoke_method_impl(self,
                            request: Union[Request, Notification],
                            need_resource: bool = False) -> Any:
        ''' invoke a rpc-method according to request,
        assume that the request is always valid
        which means that the request method exist, and argument is valid too '''
        method = self.get_method(request.method)
        if need_resource:
            # when need resource, the method will be invoked
            # in another process, then it will return a future
            # object
            if isinstance(request.params, dict):
                result_future = self.loop.run_in_executor(self.process_executor,
                                                          functools.partial(method, **request.params))
            elif isinstance(request.params, list):
                result_future = self.loop.run_in_executor(self.process_executor,
                                                          method,
                                                          *request.params)
            else:
                result_future = self.loop.run_in_executor(self.process_executor,
                                                          method)
            return result_future
        else:
            logging.info(f'going to invoke method {request.method}')
            if isinstance(request.params, dict):
                result = method(**request.params)
            elif isinstance(request.params, list):
                result = method(*request.params)
            else:
                # the method have no parameter
                result = method()
            return result

    async def invoke_method(self, request: Union[Request, Notification]) -> Any:
        result = self._invoke_method_impl(request)

        if asyncio.iscoroutine(result):
            # await the method and extract the result out
            result = await result
        if isinstance(request, Request):
            return result

    def get_method(self, method_name: str) -> Callable:
        ''' get and return actual rpc method, which may in the modules or in the server
        if the method is not existed, a ValueError will occured'''
        method = self._get_method_in_module(method_name)
        if method is None:
            method = super(JsonRPC2, self).get_method(method_name)
        return method

    def _get_method_in_module(self, method_name: str) -> Callable:
        if len(self.modules) == 0:
            return None
        splitters = ['.', '/']
        module_level = 2
        for splitter in splitters:
            method_component = method_name.split(splitter)
            if len(method_component) > module_level:
                return None
            elif len(method_component) == module_level:
                module_name, method_name = method_component
                return self.modules[module_name].get_method(method_name)
        return None

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

    def start(self, port: int = 8080):
        ''' start the server and listen to client '''
        server = asyncio.start_server(self.handle_client, port=port, loop=self.loop)
        server = self.loop.run_until_complete(server)
        try:
            self.loop.run_forever()
        finally:
            self.loop.close()

    def register_module(self, module: Module):
        ''' register module to rpc server

        :param module: the module to add to json rpc2 server
        .. versionadded:: 0.4
        '''
        self.modules[module.name] = module

    def _group_requests(self, request_json: list) -> _RequestGroup:
        result = _RequestGroup()

        for request in request_json:
            if isinstance(request, dict) is False or \
               "method" not in request or \
               request["method"] not in self.methods:
                result.simple_requests.append(request)
            else:
                rpc_method = self.get_rpc_method(request["method"])
                if rpc_method.extra_need == ExtraNeed.NOTHING:
                    result.simple_requests.append(request)
                elif rpc_method.extra_need == ExtraNeed.PROCESS:
                    result.process_requests.append(request)
                else:
                    result.thread_requests.append(request)

        return result

    def _handle_process_requests(self, requests_json: List) -> List:
        ''' handle for requests which need to be execute in other processes '''
        results = []
        errors = []
        for request_json in requests_json:
            error = self.check_errors(request_json)
            if error:
                errors.append(self._generate_error_response(request_json, error))
            else:
                request = self._parse_request(request_json)
                result = self._invoke_method_impl(request, need_resource=True)

                if isinstance(request, Request):
                    # Note: because result returns a future
                    # and we don't want to lose request id information
                    # so we add *req_id* attribute to the future object
                    result.req_id = request.req_id
                    results.append(result)
        return [results, errors]

    def _handle_thread_requests(self, requests_json: List) -> List[Future]:
        ''' handle for requests which need to be execute in other threads '''
        results = self._submit_requests_to_executor(self.thread_executor, requests_json)
        return results

    def _submit_requests_to_executor(self, executor, requests_json: List) -> List[Future]:
        results = []
        for request_json in requests_json:
            result = self.loop.run_in_executor(executor,
                                               self._handle_request,
                                               request_json)
            results.append(result)
        return results

    def _generate_error_response(self,
                                 request_json: JSON,
                                 error: JsonRPC2Error) -> ErrorResponse:
        request_id = self.get_request_id(request_json, error)
        response = ErrorResponse(error, request_id)
        return response

    def _parse_request(self, request_json: JSON) -> Union[Request, Notification]:
        if 'id' in request_json:
            request = Request.from_json(request_json)
        else:
            request = Notification.from_json(request_json)
        return request

    def _handle_request(self, request_json: JSON) -> Union[ErrorResponse, Future]:
        ''' handle rpc call sync '''
        error = self.check_errors(request_json)

        if error:
            return self._generate_error_response(request_json, error)
        request = self._parse_request(request_json)
        try:
            result = self._invoke_method_impl(request)
        except Exception as e:
            response = self._generate_error_response(request_json, InternalError("Internal error"))
        else:
            if isinstance(request, Request):
                response = SuccessResponse(result, request.req_id)

        if isinstance(request, Request):
            return response

    def _convert_to_response(self, rpc_call_results):
        responses = []
        for rpc_call_result in rpc_call_results[0]:
            try:
                response = SuccessResponse(rpc_call_result.result(),
                                           rpc_call_result.req_id)
            except Exception as e:   # there is an error in the rpc call
                response = ErrorResponse(InternalError("Internal error"),
                                         rpc_call_result.req_id)
            responses.append(response)
        return responses
