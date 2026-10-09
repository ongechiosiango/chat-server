# Chat Server

[![CI](https://github.com/ongechiosiango/chat-server/actions/workflows/ci.yml/badge.svg)](https://github.com/ongechiosiango/chat-server/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)

A tiny asyncio TCP chat server with broadcast messaging.

## What this is

A ~130-line asyncio TCP server that broadcasts newline-delimited text
between all connected clients. It exists to demonstrate:

- A raw TCP server with concurrent clients
- Broadcast semantics with a tracked set of writers
- Clean handling of joins, leaves, and broken connections
- Line-delimited framing over a byte stream
- Testing an asyncio server end-to-end with real sockets

## Quick start

    python3 -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"

Start the server:

    chat-server --port 6390

In two other terminals, connect with `nc`:

    nc 127.0.0.1 6390

Type a line in either terminal, press Enter, and watch it appear in the
other. Close a terminal and the remaining one sees the leave message.

## Protocol

- Line-delimited UTF-8.
- Maximum line length: 4096 bytes.
- Blank lines are ignored.
- Everything sent by one client is broadcast to all other clients,
  prefixed with the sender's `host:port`.

See docs/usage.md for a full walkthrough.

## Limitations

Commit 1 is deliberately minimal. Not implemented (yet):

- Nicknames / identity
- Rooms / channels
- Chat history / persistence
- Authentication
- WebSocket or browser client

## Development

    pip install -e ".[dev]"
    pytest -v

## Contributing

See CONTRIBUTING.md.

## License

MIT - see LICENSE.
