#!/usr/bin/env python3
"""Signal a direct browser-to-browser phone camera WebRTC connection."""

import argparse
import asyncio
import ipaddress
import json
import queue
import struct
import shutil
import socket
import ssl
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

from aiohttp import WSMsgType, web

# PyInstaller extracts bundled data under _MEIPASS (one-file builds) or
# places it beside the executable (one-folder builds). In source runs, use
# the script directory as usual.
BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
WEB_DIR = BASE_DIR / "web"
signal_sockets = {}
session = {"offer": None, "answer": None}
ui_events = None


def local_addresses():
    found = set()
    # getaddrinfo(hostname) often returns only a loopback alias on Linux.
    # Query each interface directly so multiple active LANs are all shown.
    try:
        import fcntl

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            for _, interface in socket.if_nameindex():
                encoded_name = interface.encode("utf-8")[:15]
                request = struct.pack("256s", encoded_name)
                try:
                    flags = struct.unpack("H", fcntl.ioctl(sock.fileno(), 0x8913, request)[16:18])[0]
                    if not flags & 0x1:  # IFF_UP
                        continue
                    address = socket.inet_ntoa(fcntl.ioctl(sock.fileno(), 0x8915, request)[20:24])
                    parsed = ipaddress.ip_address(address)
                    if not parsed.is_loopback and not parsed.is_link_local:
                        found.add(address)
                except OSError:
                    # Interfaces without an IPv4 address are normal (for
                    # example, loopback or IPv6-only interfaces).
                    continue
    except (ImportError, OSError, AttributeError):
        pass

    # Windows does not provide fcntl; retain hostname resolution as a
    # portable fallback there and for unusual platforms.
    if not found:
        try:
            for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
                address = info[4][0]
                parsed = ipaddress.ip_address(address)
                if not parsed.is_loopback and not parsed.is_link_local:
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
    if ui_events:
        ui_events.put(("activity", f"{role.capitalize()} connected from {request.remote or 'unknown device'}"))
        ui_events.put(("status", role, True))

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
        if ui_events:
            ui_events.put(("activity", f"{role.capitalize()} disconnected"))
            ui_events.put(("status", role, False))
    return websocket


async def page(request):
    name = "sender.html" if request.path == "/sender" else "obs.html"
    file_path = WEB_DIR / name
    if ui_events:
        ui_events.put(("activity", f"{request.path} opened by {request.remote or 'unknown device'}"))
    if not file_path.is_file():
        message = f"Page file not found: {file_path}. Include the web folder when building the executable."
        if ui_events:
            ui_events.put(("activity", message))
        raise web.HTTPInternalServerError(text=message)
    return web.FileResponse(file_path)


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
    obs_url = f"http://127.0.0.1:{port + 1}/obs"
    sender_urls = [f"https://{address}:{port}/sender" for address in local_addresses()]
    if ui_events:
        ui_events.put(("ready", sender_urls, obs_url))
    print("Phone camera signaling server is running", flush=True)
    print(f"OBS Browser Source URL: {obs_url}", flush=True)
    for url in sender_urls:
        print(f"On the phone, open: {url}", flush=True)
    print("Accept the local certificate warning in the phone browser, then allow camera and microphone access.", flush=True)
    await asyncio.Event().wait()


def run_server(port, event_queue):
    global ui_events
    ui_events = event_queue
    try:
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
        loop.run_until_complete(start_servers(app, tls, port))
    except Exception as exc:
        event_queue.put(("error", str(exc)))


class CameraWindow:
    def __init__(self, root, port):
        self.root = root
        self.root.title("Phone Camera")
        self.root.geometry("720x520")
        self.events = queue.Queue()
        self.states = {"sender": "Waiting", "viewer": "Waiting"}

        frame = ttk.Frame(root, padding=12)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Phone Camera Connection", font=("TkDefaultFont", 14, "bold")).pack(anchor="w")
        self.state_label = ttk.Label(frame, text="Server starting…")
        self.state_label.pack(anchor="w", pady=(8, 12))
        self.urls = ttk.LabelFrame(frame, text="Connection URLs", padding=8)
        self.urls.pack(fill="x", pady=(0, 12))
        self.sender_label = ttk.Label(self.urls, text="Phone sender: preparing…", justify="left", wraplength=660)
        self.sender_label.pack(anchor="w", fill="x")
        self.viewer_label = ttk.Label(self.urls, text="OBS viewer: preparing…", justify="left", wraplength=660)
        self.viewer_label.pack(anchor="w", fill="x", pady=(6, 0))
        ttk.Label(frame, text="Recent activity").pack(anchor="w")
        self.activity = ScrolledText(frame, height=16, state="disabled", wrap="word")
        self.activity.pack(fill="both", expand=True, pady=(4, 0))
        threading.Thread(target=run_server, args=(port, self.events), daemon=True).start()
        self.root.after(150, self.process_events)
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)

    def process_events(self):
        while not self.events.empty():
            event = self.events.get_nowait()
            if event[0] == "ready":
                _, sender_urls, viewer_url = event
                self.sender_label.config(text="Phone sender:\n" + ("\n".join(sender_urls) or "No LAN address found"))
                self.viewer_label.config(text="OBS viewer:\n" + viewer_url)
                self.state_label.config(text="Server running")
                self.add_activity("Server started")
            elif event[0] == "status":
                _, role, connected = event
                self.states[role] = "Connected" if connected else "Waiting"
                self.state_label.config(text=f"Server running  |  Phone: {self.states['sender']}  |  Viewer: {self.states['viewer']}")
            elif event[0] == "activity":
                self.add_activity(event[1])
            elif event[0] == "error":
                self.state_label.config(text="Server error: " + event[1])
                self.add_activity("Server error: " + event[1])
        self.root.after(150, self.process_events)

    def add_activity(self, message):
        from datetime import datetime
        self.activity.configure(state="normal")
        self.activity.insert("end", f"{datetime.now().strftime('%H:%M:%S')}  {message}\n")
        self.activity.see("end")
        self.activity.configure(state="disabled")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="HTTPS port (default: 8765)")
    args = parser.parse_args()
    root = tk.Tk()
    CameraWindow(root, args.port)
    root.mainloop()


if __name__ == "__main__":
    main()
