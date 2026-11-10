#!/usr/bin/env python3

import argparse
import socket
import struct
import sys


AUTH = 3
EXEC = 2


def recv_exact(sock, size):
    data = b""

    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            raise ConnectionError("server closed connection")
        data += chunk

    return data


def make_packet(req_id, packet_type, body=""):
    body = body.encode("utf-8")
    size = len(body) + 10
    return struct.pack("<iii", size, req_id, packet_type) + body + b"\0\0"


def read_packet(sock):
    size = struct.unpack("<i", recv_exact(sock, 4))[0]
    data = recv_exact(sock, size)

    req_id, packet_type = struct.unpack("<ii", data[:8])
    body = data[8:-2].decode("utf-8", errors="replace")

    return req_id, packet_type, body


def run_rcon(host, port, password, command, timeout):
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)

        sock.sendall(make_packet(1, AUTH, password))

        auth_id, _, _ = read_packet(sock)

        if auth_id == -1:
            raise RuntimeError("RCON authentication failed")

        sock.sendall(make_packet(2, EXEC, command))

        while True:
            req_id, _, body = read_packet(sock)

            if req_id == 2 and body:
                return body.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Minimal Project Zomboid RCON client"
    )

    parser.add_argument("host", help="RCON host, e.g. 127.0.0.1")
    parser.add_argument("port", type=int, help="RCON port, e.g. 27019")
    parser.add_argument("password", help="RCON password")
    parser.add_argument("command", nargs="+", help="Command to run, e.g. players")

    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=5.0,
        help="Socket timeout in seconds, default: 5",
    )

    args = parser.parse_args()

    command = " ".join(args.command)

    try:
        result = run_rcon(
            args.host,
            args.port,
            args.password,
            command,
            args.timeout,
        )
        print(result)
        return 0

    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())