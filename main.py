import socket
import threading
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

@dataclass
class Response:
    status_code: int
    reason: bytes
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
        raise ValueError("malformed request line")
    return RequestLine(*parts)

def parse_header(line):
    line = line.rstrip(b"\r")
    parts = line.split(b":", 1)
    if len(parts) != 2:
        raise ValueError("malformed header")
    return (parts[0], parts[1].strip())

def parse_request(reader: BufferedReader):
    request = Request()
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


def serialize_response(response: Response) -> bytes:
    result = (
        b"HTTP/1.1 "
        + str(response.status_code).encode()
        + b" "
        + response.reason
        + b"\r\n"
    )
    for key, value in response.headers.items():
        if key.lower() in (b"content-length", b"connection"):
            continue
        result += key + b": " + value + b"\r\n"
    result += (
        b"Content-Length: "
        + str(len(response.body)).encode()
        + b"\r\n"
    )
    result += (
        b"Connection: "
        + b"keep-alive"
        + b"\r\n"
        + b"\r\n"
    )
    result += response.body
    return result


def handle_request(request: Request) -> Response:
    method = request.request_line.method
    target = request.request_line.target
    if method == b"GET" and target == b"/":
        return Response(
                status_code=200,
                reason=b"OK",
                headers={b"Content-Type": b"text/plain"},
                body=b"hello",
            )
    elif method == b"GET" and target == b"/health":
        return Response(
                status_code=200,
                reason=b"OK",
                headers={b"Content-Type": b"text/plain"},
                body=b"healthy",
            )
    else:
        return Response(
                status_code=404,
                reason=b"Not Found",
            )


def handle_connection(connection):
    reader = BufferedReader(connection)
    try:
        while True:
            try:
                request = parse_request(reader)
                response = handle_request(request)
                connection.sendall(serialize_response(response))
            except EOFError:
                break
            except ValueError:
                response = Response(
                        status_code=400,
                        reason=b"Bad Request",
                    )
                connection.sendall(serialize_response(response))
    finally:
        connection.close()

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 42069))
server.listen()

while True:
    connection, address = server.accept()
    thread = threading.Thread(
        target=handle_connection,
        args=(connection,),
    )
    thread.start()