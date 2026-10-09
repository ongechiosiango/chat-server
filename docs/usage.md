# Usage Guide

## Start the server

    chat-server --port 6390

Options:

| Flag | Default | Description |
|------|---------|-------------|
| --host | 127.0.0.1 | Bind address |
| --port, -p | 6390 | Listen port |
| --version | | Print version and exit |

## Chat with `nc`

Open two terminals. In the first:

    nc 127.0.0.1 6390

In the second:

    nc 127.0.0.1 6390

The first terminal sees:

    * 127.0.0.1:xxxxx joined the chat

Now type a line in either terminal and press Enter. The other terminal
receives it prefixed with the sender's address:

    [127.0.0.1:xxxxx] hello

Close a terminal (Ctrl+C in nc) and the other sees:

    * 127.0.0.1:xxxxx left the chat

## Protocol

The wire protocol is deliberately minimal:

- Line-delimited UTF-8 (`\n` terminates a line).
- Lines longer than 4096 bytes are rejected.
- Blank lines are ignored.
- Everything a client sends is broadcast to every OTHER connected client.

There is one implicit room. There are no nicknames, no authentication,
no history, and no persistence. Every Commit 1 limitation is a deliberate
choice, not a bug.

## Tests

    pytest -v

The suite starts the server on a random free port and exercises it with
real sockets: join, broadcast, leave, empty-line handling.
