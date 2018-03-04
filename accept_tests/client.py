''' mock json rpc2 client implementation '''
import socket
import json
import time


class MockJsonRPC2Client:
    def __init__(self, host, port):
        self.socket = socket.socket()
        self.host = host
        self.port = port
        self.is_connected = False

    def connect(self, times=0):
        ''' connect to server, will try to connect 5 times,
        if it still connect failure, then an error will be raised'''
        MAX_TIMES = 5
        if times == MAX_TIMES and self.is_connected is False:
            # if connection refused this time, the error will be raised
            self.socket.connect((self.host, self.port))
            self.is_connected = True
        else:
            if self.is_connected is False:
                try:
                    self.socket.connect((self.host, self.port))
                except ConnectionRefusedError as e:
                    times += 1
                    time.sleep(2**times)
                    self.connect(times)
                else:
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
