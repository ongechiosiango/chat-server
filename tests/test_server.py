"""End-to-end tests: start the server on a random port and connect with sockets."""

import asyncio
import socket

import pytest

from chat_server.server import ChatRoom, format_line, serve


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


async def _connect(port: int):
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    return reader, writer


async def _read_line(reader, timeout: float = 2.0) -> str:
    data = await asyncio.wait_for(reader.readline(), timeout=timeout)
    return data.decode("utf-8").rstrip("\r\n")


# --- Pure-function tests -------------------------------------------------


def test_format_line():
    assert format_line("1.2.3.4:5000", "hello") == b"[1.2.3.4:5000] hello\n"


def test_chat_room_client_count():
    room = ChatRoom()
    assert room.client_count == 0


# --- Broadcast behavior --------------------------------------------------


@pytest.mark.asyncio
async def test_broadcast_reaches_all_but_sender():
    """Three clients; one sends; the other two receive."""
    port = _free_port()
    server = await serve(host="127.0.0.1", port=port, room=ChatRoom())
    try:
        async with server:
            r1, w1 = await _connect(port)
            r2, w2 = await _connect(port)
            r3, w3 = await _connect(port)

            # Each new client triggers a "* joined" announcement.
            # Drain those so our assertions are clean.
            await asyncio.sleep(0.1)
            for r in (r1, r2, r3):
                while True:
                    try:
                        await asyncio.wait_for(r.readline(), timeout=0.05)
                    except asyncio.TimeoutError:
                        break

            w1.write(b"hello everyone\n")
            await w1.drain()

            msg2 = await _read_line(r2)
            msg3 = await _read_line(r3)

            assert "hello everyone" in msg2
            assert "hello everyone" in msg3

            for w in (w1, w2, w3):
                w.close()
                try:
                    await w.wait_closed()
                except Exception:
                    pass
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_join_announcement():
    """When a second client joins, the first sees an announcement."""
    port = _free_port()
    server = await serve(host="127.0.0.1", port=port, room=ChatRoom())
    try:
        async with server:
            r1, w1 = await _connect(port)
            await asyncio.sleep(0.05)

            r2, w2 = await _connect(port)
            await asyncio.sleep(0.1)

            msg = await _read_line(r1)
            assert "joined" in msg

            for w in (w1, w2):
                w.close()
                try:
                    await w.wait_closed()
                except Exception:
                    pass
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_leave_announcement():
    """When a client disconnects, remaining clients see a leave announcement."""
    port = _free_port()
    server = await serve(host="127.0.0.1", port=port, room=ChatRoom())
    try:
        async with server:
            r1, w1 = await _connect(port)
            r2, w2 = await _connect(port)
            await asyncio.sleep(0.1)

            # Drain join announcements
            for r in (r1,):
                while True:
                    try:
                        await asyncio.wait_for(r.readline(), timeout=0.05)
                    except asyncio.TimeoutError:
                        break

            w2.close()
            try:
                await w2.wait_closed()
            except Exception:
                pass
            await asyncio.sleep(0.2)

            msg = await _read_line(r1)
            assert "left" in msg

            w1.close()
            try:
                await w1.wait_closed()
            except Exception:
                pass
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_empty_lines_ignored():
    """Blank lines should not be broadcast."""
    port = _free_port()
    server = await serve(host="127.0.0.1", port=port, room=ChatRoom())
    try:
        async with server:
            r1, w1 = await _connect(port)
            r2, w2 = await _connect(port)
            await asyncio.sleep(0.1)

            # Drain join announcements
            for r in (r2,):
                while True:
                    try:
                        await asyncio.wait_for(r.readline(), timeout=0.05)
                    except asyncio.TimeoutError:
                        break

            w1.write(b"\n")
            await w1.drain()

            # r2 should receive nothing
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(r2.readline(), timeout=0.3)

            for w in (w1, w2):
                w.close()
                try:
                    await w.wait_closed()
                except Exception:
                    pass
    finally:
        server.close()
        await server.wait_closed()
