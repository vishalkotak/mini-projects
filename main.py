import socket
from dataclasses import dataclass, field

@dataclass
class RequestLine:
    method: bytes
    target: bytes
    version: bytes

@dataclass
class Request:
    request_line: RequestLine | None = None
    headers: dict[bytes, bytes] = field(default_factory=dict)
    body: bytes = b""

class BufferedReader:
    def __init__(self, connection):
        self.connection = connection
        self.buffer = b""

    def read_line(self):
        while b"\n" not in self.buffer:
            data = self.connection.recv(8)
            if not data:
                raise EOFError("connection closed before line completed")
            self.buffer += data
        new_line_index = self.buffer.index(b"\n")
        line = self.buffer[:new_line_index]
        self.buffer = self.buffer[new_line_index + 1:]
        return line

    def read_exact(self, n: int):
        while len(self.buffer) < n:
            data = self.connection.recv(8)
            if not data:
                raise EOFError("connection closed before line completed")
            self.buffer += data
        result = self.buffer[:n]
        self.buffer = self.buffer[n:]
        return result
        

"""
\r meant “move the cursor back to the beginning of the line,” 
and \n meant “move down to the next line.”
So an HTTP request is encoded like:
GET / HTTP/1.1\r\n
The final \r\n on its own marks the end of the headers.
The important rule is: HTTP/1.x line endings are CRLF, not just LF.
"""
def parse_request_line(line):
    line = line.rstrip(b"\r")
    parts = line.split(b" ")
    if len(parts) != 3:
        raise ValueError
    return RequestLine(*parts)

def parse_header(line):
    line = line.rstrip(b"\r")
    parts = line.split(b":", 1)
    if len(parts) != 2:
        raise ValueError("malformed header")
    return (parts[0], parts[1].strip())

def parse_request(connection):
    request = Request()
    reader = BufferedReader(connection)
    line = reader.read_line()
    request.request_line = parse_request_line(line)
    while True:
        line = reader.read_line()
        if line == b"\r":
            break
        header = parse_header(line)
        request.headers[header[0]] = header[1]

    content_length = request.headers.get(b"Content-Length")
    if content_length is not None:
        request.body = reader.read_exact(int(content_length))
    return request

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 42069))
server.listen()

connection, address = server.accept()
print(parse_request(connection))

response = (
    b"HTTP/1.1 200 OK\r\n"
    b"Content-Length: 5\r\n"
    b"Content-Type: text/plain\r\n"
    b"\r\n"
    b"hello"
)
connection.sendall(response)