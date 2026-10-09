"""Asyncio TCP chat server with broadcast messaging.

Design (Commit 1):
    - One TCP port, one implicit room, no nicknames.
    - Clients connect, then send newline-delimited UTF-8 text.
    - When a line arrives, we broadcast it (prefixed with the sender's
      socket peer name) to every OTHER connected client.
    - When a client disconnects, we remove them from the room.

We deliberately chose newline-delimited UTF-8 rather than a length-prefixed
protocol because it is trivial to test with `nc` from the shell.
"""

from __future__ import annotations

import asyncio
from typing import Set

MAX_LINE_BYTES = 4096


class ChatRoom:
    """Tracks connected clients and broadcasts messages between them.

    Thread-safety is not a concern: this is only used from the asyncio
    event loop, which is single-threaded.
    """

    def __init__(self) -> None:
        self._writers: Set[asyncio.StreamWriter] = set()

    @property
    def client_count(self) -> int:
        return len(self._writers)

    def add(self, writer: asyncio.StreamWriter) -> None:
        self._writers.add(writer)

    def remove(self, writer: asyncio.StreamWriter) -> None:
        self._writers.discard(writer)

    async def broadcast(self, message: bytes, exclude: asyncio.StreamWriter = None) -> int:
        """Send `message` to every client except (optionally) `exclude`.

        Returns the number of clients the message was successfully written to.
        Dead writers are removed automatically.
        """
        sent = 0
        dead = []
        for writer in list(self._writers):
            if writer is exclude:
                continue
            try:
                writer.write(message)
                await writer.drain()
                sent += 1
            except (ConnectionError, ConnectionResetError, BrokenPipeError):
                dead.append(writer)
        for writer in dead:
            self._writers.discard(writer)
        return sent


def format_line(peer: str, text: str) -> bytes:
    """Format an incoming line as a broadcast message."""
    return f"[{peer}] {text}\n".encode("utf-8")


async def _handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    room: ChatRoom,
) -> None:
    peer = _peer_name(writer)
    room.add(writer)

    # Announce the join to the rest of the room.
    try:
        await room.broadcast(f"* {peer} joined the chat\n".encode("utf-8"), exclude=writer)
    except Exception:
        pass

    try:
        while True:
            try:
                raw = await reader.readline()
            except (ConnectionResetError, asyncio.IncompleteReadError):
                break
            if not raw:
                break
            if len(raw) > MAX_LINE_BYTES:
                try:
                    writer.write(b"! line too long, ignored\n")
                    await writer.drain()
                except Exception:
                    break
                continue

            text = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if not text:
                continue

            await room.broadcast(format_line(peer, text), exclude=writer)
    finally:
        room.remove(writer)
        try:
            await room.broadcast(f"* {peer} left the chat\n".encode("utf-8"))
        except Exception:
            pass
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


def _peer_name(writer: asyncio.StreamWriter) -> str:
    """Return a short 'host:port' string for a writer."""
    try:
        sockname = writer.get_extra_info("peername")
        if sockname and len(sockname) >= 2:
            return f"{sockname[0]}:{sockname[1]}"
    except Exception:
        pass
    return "unknown"


async def serve(host: str = "127.0.0.1", port: int = 6390, room: ChatRoom = None):
    """Start the chat server. Returns the asyncio.Server object."""
    if room is None:
        room = ChatRoom()

    server = await asyncio.start_server(
        lambda r, w: _handle_client(r, w, room),
        host=host,
        port=port,
    )
    return server
