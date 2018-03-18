import enum
import asyncio
from typing import Callable, Any


class ExtraNeed(enum.Enum):
    "extra resource information for the rpc method"
    NOTHING = 0   # no special need for the method
    PROCESS = 1   # the relative method should be called in another process
    THREAD = 2    # the relative method should be called in another thread


class RpcMethod:
    ''' wrap for rpc function, which includes more informations
    it contains which way we need to invoke the rpc method
    like run it in separate process, or run it in separate thread '''
    def __init__(self, func: Callable[..., Any], extra_need: ExtraNeed):
        self.func = func
        self.name = func.__name__
        if asyncio.iscoroutinefunction(func):
            self.extra_need = ExtraNeed.NOTHING
        else:
            self.extra_need = extra_need
