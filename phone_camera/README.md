# Phone Camera

Stream an Android phone's camera and microphone to a PC over Wi-Fi, then use the feed in OBS Studio. The phone and PC browser exchange audio/video directly with WebRTC. Python serves the pages and relays signaling; it does not decode or relay the media.

## Requirements

- Python 3.9 or newer
- OpenSSL, used once to create a local HTTPS certificate
- A current Android browser with camera and microphone access
- OBS Studio with Browser Source support
- Both devices on the same Wi-Fi network, with device-to-device traffic allowed

Install the Python package from this folder:

```bash
python3 -m pip install -r requirements.txt
```

When building with PyInstaller, bundle the `web` folder so the executable can serve the HTML pages. Run the command from this folder:

```bash
# Linux / macOS
pyinstaller --onefile --add-data "phone_camera/web:web" --noconsole phone_camera/phone_camera.py

# Windows
pyinstaller --onefile --add-data "phone_camera/web;web" --noconsole phone_camera/phone.camera.py
```

For a `.spec` build, include the page files as data with destination `web`.

## Start

From this folder, run:

```bash
python3 phone_camera.py
```

The program opens a window showing the phone sender URL, OBS viewer URL, server and device connection status, and recent page access activity. The URLs are also printed in the terminal. On the phone, open a listed `https://.../sender` address, accept the local certificate warning, allow camera and microphone access, then tap **Start streaming**. Keep that browser tab open while using the camera.

In OBS, add a **Browser** source and use the printed `http://127.0.0.1:8766/obs` URL. The page waits for the phone and renegotiates when either browser reconnects. The preview starts muted so autoplay restrictions do not block video. To hear the phone in a regular browser, click **Enable audio**. In OBS, use the Browser Source's **Interact** window to click **Enable audio**, then check OBS's audio mixer; enable **Control Audio via OBS** if you need the feed as a separately controlled audio source.

Close the Phone Camera window to stop the program. HTTPS uses port 8765 by default and OBS's local page uses the next port, 8766. A different HTTPS port can be selected with `--port`; the local OBS page will use the next port. Allow the HTTPS port through the PC firewall on the private Wi-Fi network if the phone cannot connect.

## Notes and limitations

- The initial certificate is self-signed and stored in `~/.phone_camera/`. The phone browser may show a warning before allowing camera access. This is intended for trusted home or studio Wi-Fi networks; do not expose the receiver to the public internet.
- The receiver binds the HTTPS endpoint to all network interfaces so the phone can reach it. The OBS page binds only to the PC's loopback interface.
- Media goes directly between the phone and the PC browser using local WebRTC ICE candidates. The current prototype does not use a STUN/TURN service. Router Wi-Fi client isolation, VPNs, or firewall rules that block peer-to-peer traffic can prevent the media connection even when both pages connect to the signaling server.
- The phone browser must remain open and awake. Android may pause capture when the browser is backgrounded or the screen is locked.
- Latency and quality depend on the phone, Wi-Fi, browser, and PC. This is an experimental local-network prototype.
- The current receiver is designed for one phone sender and one OBS viewer at a time.
