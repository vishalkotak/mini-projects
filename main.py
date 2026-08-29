# \n = line feed
def get_lines(f):
    buffer = b""
    while True:
        data = f.read(8)
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

with open("messages.txt", "rb") as f:
    for line in get_lines(f):
        print(line)
