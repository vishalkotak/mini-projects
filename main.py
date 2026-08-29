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

# \n = line feed
def get_lines(connection):
    buffer = b""
    while True:
        data = connection.recv(8)
        if not data:
            break
        while b"\n" in data:
            new_line_index = data.index(b"\n")
            buffer += data[:new_line_index]
            yield buffer
            buffer = b""
            data = data[new_line_index+1:]
        buffer += data

    if buffer:
        yield buffer

# with open("messages.txt", "rb") as f:
#     for line in get_lines(f):
#         print(line)

# \r = carriage return
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
    index = 0
    request = Request()
    for line in get_lines(connection):
        if index == 0:
            request_line = parse_request_line(line)
            request.request_line = request_line
        else:
            if line == b"\r":
                break
            request_header = parse_header(line)
            request.headers[request_header[0]] = request_header[1]
        index += 1
    return request

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("localhost", 42069))
server.listen()

connection, address = server.accept()
print(parse_request(connection))