import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(("localhost", 42069))

client.sendall(
    b"GET / HTTP/1.1\r\n"
    b"Host: localhost\r\n"
    b"\r\n"
    b"GET /health HTTP/1.1\r\n"
    b"Host: localhost\r\n"
    b"\r\n"
)

while True:
    data = client.recv(1024)
    if not data:
        break
    print(data)