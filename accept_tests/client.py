''' mock json rpc2 client implementation '''
import socket
import json


class MockJsonRPC2Client:
    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.is_connected = False

    def connect(self):
        if self.is_connected is False:
            self.socket.connect((self.host, self.port))
            self.is_connected = True

    def send_data(self, data):
        data_bytes = json.dumps(data).encode()
        self.socket.send(data_bytes + b"\n")

    def send_raw_data(self, data):
        self.socket.send(data + b"\n")

    def close(self):
        if self.is_connected:
            self.socket.close()
            self.is_connected = False

    def recv(self):
        return json.loads(self.socket.recv(1024).decode())
