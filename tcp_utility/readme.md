# TCP/IP & REST Testing Utility

A GUI-based network testing and debugging tool built in Python. Designed to inspect socket connections, transfer text files across machines, manage HL7/MLLP framing, and test REST endpoints.

---

## Key Features

- **Multithreaded Listener:** The server listener runs on a background thread, keeping the GUI fully responsive while waiting for incoming connections or file transfers.
- **REST API Capabilities:** Send GET/POST requests directly from the client interface to test REST endpoints alongside standard raw TCP socket testing.
- **HL7 & MLLP Support:** Automatically detects HL7 message formats, applies MLLP framing wrappers, and handles automated or manual ACK responses.
- **File & Message Transfer:** Load local text or source code files, auto-pass target filenames to the receiver, and edit message payloads before sending.
- **Profile Management:** Save and load IP addresses, ports, and configuration profiles for quick access.
- **Visual Status & Error Handling:** Color-coded status banners for warnings (orange) and connection/socket errors (red).

---

## Interface Overview

+-----------------------------------------------------------------------+
|  Send to IP: [ 192.168.15.103 ]  Port: [ 4433 ]  Profile: [ Default ] |
|  [ Load Profile ] [ Save Profile ]                                     |
|                                                                       |
|  Load Msg: [ C:/path/to/file.txt ]                     [ Browse ]     |
|  +-----------------------------------------------------------------+  |
|  | Editable Message / Payload Text Area                            |  |
|  +-----------------------------------------------------------------+  |
|  [x] Add File Name   [ ] Read ACK                      [ Send ]       |
|                                                                       |
|  Listen Port: [ 5005 ]   Status: [ LISTENING (Background) ]            |
|  +-----------------------------------------------------------------+  |
|  | Inbound Message Display                                         |  |
|  +-----------------------------------------------------------------+  |
|  [x] Read File Name  [x] Send ACK   Save Dir: [ C:/output/ ]          |
|  [ Start Listener ]  [ Stop Listener ]    [ Save Inbound File ]      |
+-----------------------------------------------------------------------+


---

## Usage Instructions

### 1. Sending TCP Messages / Files
1. Enter the target **Send to IP** and **Port**.
2. (Optional) Click **Browse** to select a file payload or type directly into the top text box.
3. Check **Add File Name** if you want the receiving instance to automatically adopt the incoming filename.
4. Click **Send**.

### 2. Starting the Background Listener
1. Set your **Listen Port** (default: `5005`).
2. Click **Start Listener**. The socket server opens on a separate background thread without locking up the UI.
3. When a message arrives, it populates the lower text box. If **Send ACK** is enabled and an HL7 payload is detected, an acknowledgment message is generated automatically.

### 3. REST API Testing
1. Select the **REST** tab/mode.
2. Enter the target URL and select the HTTP Method (`GET`, `POST`, `PUT`, `DELETE`).
3. Add headers or body JSON payloads in the request box and click **Execute**.

---

## Requirements & Setup

### System Prerequisites
- Python 3.8+
- Tkinter (`python3-tk` on Linux)

### Installation
Install dependencies via `pip`:

```bash
pip install -r requirements.txt