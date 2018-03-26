''' basic container '''
import functools

from .method import ExtraNeed, RpcMethod
from .typedef import Callable


class _MethodContainer:
    ''' Basic class which contains method maps '''
    def __init__(self):
        self.methods = {}

    def rpc_call(self, func):
        '''
        decorator function to make a function rpc_callable
        Usage example::

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

    def add_method(self, method,
                   restrict=True,
                   need_multiprocessing=False,
                   need_multithreading=False):
        ''' add method to json rpc, to make it rpc callable

        :param method: which method to be rpc callable
        :param restrict: controls the behavior when try to add method which have already
                         been added, if restrict is True, an exception will be raise when
                         user try to add an exist method.  Otherwise the method will be
                         overrided
        :param need_multiprocessing: if the value is True, then when we call the rpc method,
                                     the method will execute in separate process, this argument
                                     is useful for the high-CPU method
        :param need_multithreading: if the value is True, when we call the rpc method,
                                    the method will execute in separate thread, this argument
                                    is useful for the IO-bound method.  When all need_multiprocessing
                                    and need_multithreading are True, the method will be added as
                                    need multiprocessing method
        .. versionadded:: 0.3
           The `need_multiprocessing`, `need_multithreading` parameters were added
        '''
        if need_multiprocessing:
            extra_need = ExtraNeed.PROCESS
        elif need_multithreading:
            extra_need = ExtraNeed.THREAD
        else:
            extra_need = ExtraNeed.NOTHING

        if restrict and method.__name__ in self.methods:
            raise ValueError("The method is existed")
        else:
            self.methods[method.__name__] = RpcMethod(method, extra_need)

    def get_rpc_method(self, method_name: str) -> RpcMethod:
        ''' get and return the instance of RpcMethod which is directly in the Container
        different to get_method, get_rpc_method will return RpcMethod instance '''
        try:
            return self.methods[method_name]
        except KeyError as e:
            raise ValueError(f'The method "{method_name}" is not registered in the Server')

    def get_method(self, method_name: str) -> Callable:
        ''' get and return actual rpc method, which is directly in the Container
        if the method is not existed, a ValueError will occured'''
        return self.get_rpc_method(method_name).func
