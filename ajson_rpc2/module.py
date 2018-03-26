from .container import _MethodContainer


class Module(_MethodContainer):
    ''' Module support for json rpc2 server
    when use with Module, you can easily make an rpc
    call with modular structure
    Usage example::

        app = JsonRPC2()
        window_module = Module('window')

        @window_module.rpc_call
        def open():
            pass

        # register the module to server
        # then we can make a rpc call like this
        # {"jsonrpc": 2.0, "method": "window.open"}
        app.register_module(window_module)

    :param name: the name of module, it will be called as rpc prefix name
    .. versionadded:: 0.4
    '''
    def __init__(self, name: str):
        super(Module, self).__init__()
        self.name = name
