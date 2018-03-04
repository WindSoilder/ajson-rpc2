''' acceptance tests for json-rpc2,

which will open the real server, and client will
send request to server, then check if server response
it with properly value '''
import sys
import os
import inspect
import logging
import accept_test_cases
from multiprocessing import Process
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ajson_rpc2 import JsonRPC2


def start_server():
    json_rpc2_server = JsonRPC2()

    @json_rpc2_server.rpc_call
    def subtract(minuend, subtrahend):
        return minuend - subtrahend

    @json_rpc2_server.rpc_call
    def have_error_method(arg):
        raise ValueError('error')

    json_rpc2_server.start()


def start_server_process():
    server_process = Process(target=start_server)
    server_process.start()
    return server_process


def run_client_tests():
    # detect all test cases
    test_members = inspect.getmembers(accept_test_cases,
                                      predicate=lambda x: inspect.isfunction(x) and x.__name__.startswith('test'))
    test_funcs = map(lambda x: x[1], test_members)
    error_dict = {}

    for test_func in test_funcs:
        try:
            test_func()
        except Exception as e:
            error_dict[test_func.__name__] = e

    return error_dict


def close_server_process(process: Process):
    process.terminate()


def main():
    process = start_server_process()
    fails = run_client_tests()
    if len(fails) == 0:
        print("all tests run complete with no errors")
    else:
        for test_name, error in fails.items():
            logging.error(f'{test_name} runs failed\nErrorMessage: {error}\n')
    close_server_process(process)
    assert len(fails) == 0, "There are failures in running acceptance tests"


if __name__ == '__main__':
    main()
