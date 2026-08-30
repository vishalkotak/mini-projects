# HTTP from TCP

A minimal HTTP/1.1 server written directly on top of a TCP socket, built to
understand what a web framework is actually doing underneath.

Nothing here imports `http` or `socketserver`. The only stdlib pieces used are
`socket` (raw bytes in and out) and `threading` (one thread per connection).
Everything between those two — framing, parsing, routing, serializing — is
written out by hand.

## The idea

TCP gives you a *byte stream*, not messages. `recv()` returns whatever bytes
happen to have arrived: half a line, three lines, a line plus the first few
bytes of the next one. HTTP is a protocol layered on top of that stream, and
the whole job of this code is deciding where one message ends and the next
begins.

HTTP/1.1 solves that with exactly two framing rules, and this server implements
both:

- **The head is delimiter-framed** — read until `\r\n`, and a bare `\r\n` ends
  the header block.
- **The body is length-framed** — read exactly `Content-Length` bytes.

Because every response is length-framed, the connection can be reused: once
`Content-Length` bytes are consumed the next request starts immediately, with
no ambiguity about where the previous one ended. That is what makes
keep-alive and pipelining possible, and why `BufferedReader` is created once
per *connection* rather than once per request.

## Files

| File | What it is |
|------|------------|
| `main.py` | The whole server: reader, parser, router, serializer, accept loop. |
| `messages.txt` | A small fixture used early on to exercise line-splitting against a file before pointing it at a socket. |
| `client.py` | A tiny raw-socket client that sends one request with `Connection: close`, to watch the server close the connection. |

## How it fits together

`BufferedReader` wraps a connection and owns the leftover bytes:

- `read_line()` keeps calling `recv(8)` until it finds a `\n`, returns the line,
  and **keeps the remainder** in `self.buffer`.
- `read_exact(n)` keeps reading until `n` bytes are available, then splits them
  off the front.

Holding the remainder on the instance is the part that matters. The last
`recv()` of the header block usually drags in the first bytes of the body too;
because they stay in the buffer, `read_exact()` can consume them instead of
losing them.

The deliberately tiny `recv(8)` is a teaching choice — it guarantees that
almost every line spans multiple reads, so the buffering logic is actually
exercised rather than accidentally working.

From there:

- `parse_request()` reads the request line, loops headers until the bare `\r\n`,
  then reads the body if `Content-Length` is present.
- `handle_request()` maps target, then method, to a `Response`.
- `should_close()` reads the request's `Connection` header to decide whether
  this is the last exchange on the socket.
- `serialize_response()` renders a `Response` back to bytes, computing
  `Content-Length` from `len(body)` so the two cannot disagree.
- The accept loop hands each connection to its own thread.

`Request` and `Response` are symmetric dataclasses, so the semantic types live
in the model (`status_code` is an `int`) and the bytes conversion happens only
at the parse/serialize boundary.

## Routes

| Request | Response |
|---------|----------|
| `GET /` | `200 OK`, `text/plain`, `hello` |
| `GET /health` | `200 OK`, `text/plain`, `healthy` |
| known path, wrong method | `405 Method Not Allowed`, empty body |
| unknown path | `404 Not Found`, empty body |
| unparseable request | `400 Bad Request`, empty body |

Target is matched first, then method, so a known path with an unsupported
method gets `405` rather than `404` — `POST /` is "that resource exists, not
that verb", which is different from `GET /nope`.

The connection is reused by default and closed when the request carries
`Connection: close`, which the response then echoes back.

## Running it

```bash
python3 main.py          # listens on localhost:42069
python3 client.py        # one request with Connection: close
```

`client.py` sends `Connection: close`, so the server closes after responding
and the client's `recv()` loop ends on its own. Drop that header and send two
requests back to back instead, and the same script exercises pipelining — but
it will then block, because neither side closes first.

```bash
curl -i http://localhost:42069/
curl -i http://localhost:42069/health
curl -i http://localhost:42069/nope

# watch the raw bytes, CRLFs and all
curl -s -i http://localhost:42069/ | od -c
```

## Known bug

The `except ValueError` branch in `handle_connection()` sends its `400` but
does not `continue`, so control falls through to `handle_request(request)`
below it. If the malformed request is the first on the connection, `request`
is unbound and the thread dies with `UnboundLocalError`. If a valid request
came first, `request` still holds the *previous* one, so the server replays
the previous response after the `400` and keeps doing so on every subsequent
bad line. Adding `continue` after the `sendall` fixes both.

## Known limitations

Deliberate — this is a learning build, not a production server.

- **No `SO_REUSEADDR`**, so restarting fails with `Address already in use`
  until the socket leaves `TIME_WAIT`.
- **A `400` does not close the connection.** The loop keeps reading from a
  stream whose position is now unknown, so one malformed line can produce
  several `400`s before it resynchronizes by luck. RFC 9112 says to close
  after a parse error precisely because recovery is not generally possible.
- **`400` responses always advertise `keep-alive`**, since the close decision
  is derived from a request that failed to parse.
- **No chunked transfer encoding**, so a request without `Content-Length` is
  assumed to have no body.
- **Threads are non-daemon**, so Ctrl-C won't exit cleanly while a connection
  is open.
- **No timeouts** — a client that opens a connection and never sends a
  complete line ties up a thread indefinitely. A truncated request only
  becomes a `400` once the client actually closes; a client that just
  stops writing blocks in `recv()` forever.
