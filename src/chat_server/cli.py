"""Command-line entry point for chat-server."""

from __future__ import annotations

import argparse
import asyncio
import sys

from . import __version__
from .server import serve


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chat-server",
        description="A tiny asyncio TCP chat server with broadcast messaging.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", "-p", type=int, default=6390, help="Port (default: 6390)")
    parser.add_argument("--version", action="version", version=f"chat-server {__version__}")
    return parser


async def _run(host: str, port: int) -> None:
    server = await serve(host=host, port=port)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"chat-server {__version__} listening on {addrs}", flush=True)
    print("Connect with: nc <host> <port>", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        async with server:
            await server.serve_forever()
    except asyncio.CancelledError:
        pass


def main() -> int:
    args = build_parser().parse_args()
    try:
        asyncio.run(_run(args.host, args.port))
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
