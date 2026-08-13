#!/usr/bin/env python3
# usbViewer.py
# Requires: pip3 install pyudev

import sys
import os
try:
    import pyudev
except Exception as e:
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Missing dependency", f"pyudev is required: {e}")
    sys.exit(1)

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

USB_IDS_PATH = '/usr/share/hwdata/usb.ids'

vendors = {}
products = {}
interfaces = {}


def load_usb_ids(path):
    v = {}
    p = {}
    i = {}
    try:
        with open(path, 'r', errors='ignore') as f:
            cur_vid = None
            cur_pid = None
            for raw in f:
                line = raw.rstrip('\n')
                if not line or line.startswith('#'):
                    continue
                # count leading tabs
                stripped = line.lstrip('\t')
                depth = len(line) - len(stripped)
                parts = stripped.split(None, 1)
                if not parts:
                    continue
                id_hex = parts[0].lower()
                name = parts[1].strip() if len(parts) > 1 else ''
                if depth == 0:
                    cur_vid = id_hex
                    cur_pid = None
                    v[cur_vid] = name
                elif depth == 1:
                    cur_pid = id_hex
                    if cur_vid:
                        p[f"{cur_vid}:{cur_pid}"] = name
                else:
                    # interface / subid lines — attach to current product if present, else vendor
                    key = f"{cur_vid}:{cur_pid}" if cur_pid else cur_vid
                    i.setdefault(key, []).append(f"{id_hex} {name}")
    except Exception:
        return {}, {}, {}
    return v, p, i

import urllib.request
import urllib.error

LOCAL_CACHE = os.path.join(os.path.expanduser('~'), '.cache', 'usb.ids')
USB_IDS_URL = 'https://www.linux-usb.org/usb.ids'

def fetch_usb_ids(url, dest):
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(data)
        print(f"Fetched usb.ids to {dest}")
        return True
    except Exception as e:
        print(f"Warning: failed to fetch {url}: {e}", file=sys.stderr)
        return False

if os.path.exists(USB_IDS_PATH):
    vendors, products, interfaces = load_usb_ids(USB_IDS_PATH)
elif os.path.exists(LOCAL_CACHE):
    vendors, products, interfaces = load_usb_ids(LOCAL_CACHE)
else:
    # try to fetch into the local cache
    if fetch_usb_ids(USB_IDS_URL, LOCAL_CACHE):
        vendors, products, interfaces = load_usb_ids(LOCAL_CACHE)
    else:
        vendors, products, interfaces = {}, {}, {}


def attr(device, name):
    val = device.attributes.get(name)
    return val.decode(errors='ignore') if val is not None else None


def scan_devices():
    context = pyudev.Context()
    devices = []
    for dev in context.list_devices(subsystem='usb', DEVTYPE='usb_device'):
        vid = (attr(dev, 'idVendor') or '').lower()
        pid = (attr(dev, 'idProduct') or '').lower()
        serial = attr(dev, 'serial') or ''
        manufacturer = attr(dev, 'manufacturer') or ''
        product = attr(dev, 'product') or ''

        # fill from usb.ids when missing
        if not manufacturer and vid:
            manufacturer = vendors.get(vid, '')
        if not product and vid and pid:
            product = products.get(f"{vid}:{pid}", '')

        busnum = dev.attributes.get('busnum')
        devnum = dev.attributes.get('devnum')
        b = busnum.decode() if busnum else ''
        d = devnum.decode() if devnum else ''

        # gather attributes and properties for details
        attrs = {}
        try:
            for k in dev.attributes:
                try:
                    v = dev.attributes.get(k)
                    key = k.decode() if isinstance(k, bytes) else str(k)
                    attrs[key] = v.decode(errors='ignore') if v is not None else ''
                except Exception:
                    attrs[key] = str(v)
        except Exception:
            attrs = {}

        props = {}
        try:
            # dev.properties may be mapping-like
            for k, v in getattr(dev, 'properties', {}).items():
                props[str(k)] = v
        except Exception:
            try:
                for k in getattr(dev, 'properties', {}):
                    props[str(k)] = dev.properties.get(k)
            except Exception:
                props = {}

        # interface info from usb.ids
        iface_key = f"{vid}:{pid}" if vid and pid else vid
        iface_list = []
        if iface_key:
            iface_list = interfaces.get(iface_key, []) + interfaces.get(vid, [])

        devices.append({
            'sys_path': dev.sys_path,
            'vendor': vid,
            'product_id': pid,
            'manufacturer': manufacturer,
            'product': product,
            'serial': serial,
            'bus': b,
            'device': d,
            'attributes': attrs,
            'properties': props,
            'interfaces': iface_list
        })
    return devices


# cache devices so details can reference full info
devices_cache = []


def populate_tree(tree):
    global devices_cache
    devices_cache = scan_devices()
    for i in tree.get_children():
        tree.delete(i)
    for idx, d in enumerate(devices_cache):
        tree.insert('', 'end', iid=str(idx), values=(
            d['sys_path'],
            f"{d['vendor']}:{d['product_id']}",
            d['manufacturer'],
            d['product'],
            d['serial'],
            d['bus'],
            d['device']
        ))
    status_var.set(f"Found {len(devices_cache)} USB device(s)")


def on_refresh():
    populate_tree(tree)


def format_device_details(d):
    lines = []
    lines.append(f"sys_path: {d['sys_path']}")
    lines.append(f"vendor:product: {d['vendor']}:{d['product_id']}")
    if d['manufacturer']:
        lines.append(f"manufacturer: {d['manufacturer']}")
    if d['product']:
        lines.append(f"product: {d['product']}")
    if d['serial']:
        lines.append(f"serial: {d['serial']}")
    if d['bus'] or d['device']:
        lines.append(f"bus {d['bus']} device {d['device']}")

    # usb.ids interface info
    if d.get('interfaces'):
        lines.append('\nInterfaces from usb.ids:')
        for iface in d['interfaces']:
            lines.append(f"  {iface}")

    # additional attributes (commonly useful)
    common_keys = ['bDeviceClass', 'bDeviceSubClass', 'bDeviceProtocol', 'speed', 'version', 'devpath', 'driver']
    found_common = False
    for k in common_keys:
        v = d['attributes'].get(k) or d['properties'].get(k.upper())
        if v:
            if not found_common:
                lines.append('\nAdditional device fields:')
                found_common = True
            lines.append(f"  {k}: {v}")

    # dump all attributes and properties
    if d['attributes']:
        lines.append('\nAll attributes:')
        for k in sorted(d['attributes'].keys()):
            lines.append(f"  {k}: {d['attributes'][k]}")
    if d['properties']:
        lines.append('\nAll properties:')
        for k in sorted(d['properties'].keys()):
            lines.append(f"  {k}: {d['properties'][k]}")

    return '\n'.join(lines)


def on_copy():
    sel = tree.selection()
    if not sel:
        return
    idx = int(sel[0])
    d = devices_cache[idx]
    details = format_device_details(d)
    root.clipboard_clear()
    root.clipboard_append(details)
    status_var.set("Copied device details to clipboard")


def on_show_details(event=None):
    sel = tree.selection()
    if not sel:
        return
    idx = int(sel[0])
    d = devices_cache[idx]
    details = format_device_details(d)
    details_win = tk.Toplevel(root)
    details_win.title("Device details")
    txt = ScrolledText(details_win, width=100, height=25)
    txt.pack(fill='both', expand=True)
    txt.insert('1.0', details)
    txt.configure(state='disabled')


root = tk.Tk()
root.title("USB Devices Viewer")
root.geometry("1000x500")

frame = ttk.Frame(root, padding=8)
frame.pack(fill='both', expand=True)

cols = ("sys_path", "vendor:product", "manufacturer", "product", "serial", "bus", "dev")
tree = ttk.Treeview(frame, columns=cols, show='headings')
for c in cols:
    tree.heading(c, text=c)
# set widths
tree.column("sys_path", width=400)
tree.column("vendor:product", width=140, anchor='center')
tree.column("manufacturer", width=160)
tree.column("product", width=160)
tree.column("serial", width=160)
tree.column("bus", width=60, anchor='center')
tree.column("dev", width=60, anchor='center')

ysb = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
tree.configure(yscroll=ysb.set)
tree.grid(row=0, column=0, sticky='nsew')
ysb.grid(row=0, column=1, sticky='ns')

frame.rowconfigure(0, weight=1)
frame.columnconfigure(0, weight=1)

btn_frame = ttk.Frame(root, padding=4)
btn_frame.pack(fill='x')
refresh_btn = ttk.Button(btn_frame, text="Refresh", command=on_refresh)
refresh_btn.pack(side='left')
copy_btn = ttk.Button(btn_frame, text="Copy Selected", command=on_copy)
copy_btn.pack(side='left', padx=(6,0))
details_btn = ttk.Button(btn_frame, text="Show Details", command=on_show_details)
details_btn.pack(side='left', padx=(6,0))
quit_btn = ttk.Button(btn_frame, text="Quit", command=root.destroy)
quit_btn.pack(side='right')

status_var = tk.StringVar(value='')
status = ttk.Label(root, textvariable=status_var, relief='sunken', anchor='w')
status.pack(fill='x', side='bottom')

tree.bind('<Double-1>', on_show_details)

populate_tree(tree)
root.mainloop()
