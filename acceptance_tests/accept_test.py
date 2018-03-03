''' acceptance tests for json-rpc2,
which will open the real server, and client will
send request to server, then check if server response
it with properly value '''
import socket
import json
from multiprocessing import Process
from ajson_rpc2 import JsonRPC2


class MockJsonRPC2Client:
    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port

    def connect(self):
        self.socket.connect((self.host, self.port))

    def send_data(self, data):
        self.socket.send(data)

    def close(self):
        self.socket.close()

    def recv(self):
        return json.loads(self.socket.recv(1024).decode())


def start_server():
    json_rpc2_server = JsonRPC2()
    json_rpc2_server.start()


def start_server_process():
    server_process = Process(target=start_server)
    server_process.start()


def run_client_tests():
    pass


def main():
    start_server_process()
    run_client_tests()


if __name__ == '__main__':
    main()
