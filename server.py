#!/usr/bin/env python3
"""Multi-client chat server using threads and sockets."""
import socket, threading

HOST, PORT = "0.0.0.0", 5000
clients, lock = [], threading.Lock()

def broadcast(msg, sender):
    with lock:
        for c in clients:
            if c is not sender:
                try: c.sendall(msg)
                except OSError: pass

def handle(conn, addr):
    print(f"[+] {addr} connected")
    with lock: clients.append(conn)
    try:
        while True:
            data = conn.recv(1024)
            if not data: break
            broadcast(data, conn)
    finally:
        with lock: clients.remove(conn)
        conn.close()

if __name__ == "__main__":
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT)); srv.listen()
    print(f"Listening on {HOST}:{PORT}")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle, args=(conn, addr), daemon=True).start()
