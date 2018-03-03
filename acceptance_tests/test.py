from accept_test import MockJsonRPC2Client

client = MockJsonRPC2Client('localhost', 8080)
client.connect()
client.send_data(b'"{"jsonrpc": "2.0", "method": "subtract", "params": [42, 23], "id": 1}')
print(client.recv())
