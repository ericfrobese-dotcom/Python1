# USB Device Viewer

USB Device Viewer lists connected USB devices and displays their identifiers and available system details. The `usbViewer.py` version documented here uses Linux's udev device information and does not modify devices.

## Requirements and launch

This version requires Linux, Python, Tkinter, and `pyudev`. Install `pyudev` in the Python environment used to run the app:

```bash
python3 -m pip install pyudev
```

Then run:

```bash
python3 usbViewer.py
```

## Inspect devices

- The main list shows the system path, vendor and product IDs, manufacturer, product name, serial number, bus, and device number when available.
- Select **Refresh** to scan again after connecting or disconnecting a device.
- Select a row and choose **Show Details**, or double-click the row, to open the full attributes and properties.
- Select **Copy Selected** to copy the selected device's details to the clipboard.
- Select **Quit** to close the application.

Device names may come from the system's `usb.ids` data. If it is not installed locally or in the app's cache, the program attempts to download it; if that is unavailable, some names or interface descriptions may be blank. USB IDs and system attributes can still be shown.

## Troubleshooting and privacy

- **`pyudev` is missing:** Install it with the command above and launch the app with that same Python environment.
- **No devices appear:** Connect the device, wait for Linux to detect it, and select **Refresh**.
- **Names are blank:** Check that the computer is online for the initial USB ID lookup or that local `usb.ids` data is available.
- **Sharing copied details:** Device details can include serial numbers and system paths. Review the copied text before sending it to someone else.

This guide covers `usbViewer.py`, the Linux implementation. The repository also contains a separate Windows-oriented script.
