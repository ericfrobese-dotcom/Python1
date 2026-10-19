#!/usr/bin/env python3
"""Signal a direct browser-to-browser phone camera WebRTC connection."""

import argparse
import asyncio
import ipaddress
import json
import shutil
import socket
import ssl
import subprocess
from pathlib import Path

from aiohttp import WSMsgType, web

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
signal_sockets = {}
session = {"offer": None, "answer": None}


def local_addresses():
    found = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = info[4][0]
            if not address.startswith("127."):
                found.add(address)
    except OSError:
        pass
    return sorted(found)


def make_certificate(cert_path, key_path, addresses):
    if cert_path.exists() and key_path.exists():
        return
    if not shutil.which("openssl"):
        raise RuntimeError("OpenSSL is required to create the local HTTPS certificate.")
    sans = ["DNS:localhost", "IP:127.0.0.1"]
    for address in addresses:
        try:
            ipaddress.ip_address(address)
            sans.append(f"IP:{address}")
        except ValueError:
            continue
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-sha256", "-nodes",
        "-keyout", str(key_path), "-out", str(cert_path), "-days", "365",
        "-subj", "/CN=Phone Camera Local", "-addext", f"subjectAltName={','.join(sans)}",
    ], check=True, stdout=subprocess.DEVNULL)


async def send_to(role, message):
    websocket = signal_sockets.get(role)
    if websocket is not None and not websocket.closed:
        await websocket.send_str(json.dumps(message))


async def signaling(request):
    role = request.query.get("role")
    if role not in ("sender", "viewer"):
        raise web.HTTPBadRequest(text="role must be sender or viewer")

    websocket = web.WebSocketResponse(heartbeat=25, max_msg_size=2 * 1024 * 1024)
    await websocket.prepare(request)

    previous = signal_sockets.get(role)
    if previous is not None and not previous.closed:
        await previous.close(message=b"Replaced by a new connection")
    signal_sockets[role] = websocket

    # Every new viewer needs a fresh offer/answer pair. Ask an active phone to
    # renegotiate instead of replaying a stale SDP answer from an old viewer.
    if role == "viewer":
        session["offer"] = None
        session["answer"] = None
        await send_to("sender", {"type": "peer-reset"})
    else:
        session["offer"] = None
        session["answer"] = None
        await send_to("viewer", {"type": "bye"})

    print(f"{role.capitalize()} signaling client connected", flush=True)
    try:
        async for message in websocket:
            if message.type == WSMsgType.TEXT:
                try:
                    payload = json.loads(message.data)
                except json.JSONDecodeError:
                    await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                    continue
                kind = payload.get("type")
                if role == "sender" and kind == "offer":
                    session["offer"] = payload
                    session["answer"] = None
                    await send_to("viewer", payload)
                elif role == "viewer" and kind == "answer":
                    session["answer"] = payload
                    await send_to("sender", payload)
                elif kind == "bye":
                    session["offer"] = None
                    session["answer"] = None
                    await send_to("viewer" if role == "sender" else "sender", payload)
                else:
                    await websocket.send_json({"type": "error", "message": f"Unexpected {kind!r} from {role}"})
            elif message.type == WSMsgType.ERROR:
                print(f"{role.capitalize()} signaling error: {websocket.exception()}", flush=True)
    finally:
        if signal_sockets.get(role) is websocket:
            signal_sockets.pop(role, None)
            session["offer"] = None
            session["answer"] = None
            await send_to("viewer" if role == "sender" else "sender", {"type": "bye"})
        print(f"{role.capitalize()} signaling client disconnected", flush=True)
    return websocket


async def page(request):
    name = "sender.html" if request.path == "/sender" else "obs.html"
    return web.FileResponse(WEB_DIR / name)


async def status(request):
    return web.json_response({
        "sender_connected": bool(signal_sockets.get("sender") and not signal_sockets["sender"].closed),
        "viewer_connected": bool(signal_sockets.get("viewer") and not signal_sockets["viewer"].closed),
        "offer_available": session["offer"] is not None,
        "answer_available": session["answer"] is not None,
    })


async def start_servers(app, tls, port):
    runner = web.AppRunner(app)
    await runner.setup()
    https_site = web.TCPSite(runner, "0.0.0.0", port, ssl_context=tls)
    http_site = web.TCPSite(runner, "127.0.0.1", port + 1)
    await https_site.start()
    await http_site.start()
    print("Phone camera signaling server is running", flush=True)
    print(f"OBS Browser Source URL: http://127.0.0.1:{port + 1}/obs", flush=True)
    for address in local_addresses():
        print(f"On the phone, open: https://{address}:{port}/sender", flush=True)
    print("Accept the local certificate warning in the phone browser, then allow camera and microphone access.", flush=True)
    await asyncio.Event().wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="HTTPS port (default: 8765)")
    args = parser.parse_args()
    addresses = local_addresses()
    cert_dir = Path.home() / ".phone_camera"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cert_path, key_path = cert_dir / "cert.pem", cert_dir / "key.pem"
    make_certificate(cert_path, key_path, addresses)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.load_cert_chain(cert_path, key_path)

    app = web.Application()
    app.router.add_get("/sender", page)
    app.router.add_get("/obs", page)
    app.router.add_get("/status", status)
    app.router.add_get("/signal", signaling)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_servers(app, tls, args.port))
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
