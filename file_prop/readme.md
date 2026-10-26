# File Propagator Utility (`file_prop.py`)

A lightweight Python 3 graphical sync utility designed to propagate files and directories across local paths, network drives, and mounted SMB shares. It ensures target directories stay updated by comparing file existence and timestamps before performing copy or overwrite operations.

---

## Key Features

- **Source Selection (Files & Directories):** Select individual files or target an entire source directory to sync across target destinations.
- **Timestamp-Based Sync Engine:** 
  - **New Files:** Automatically copied if they do not exist in the destination directory.
  - **Modified Files:** Replaced only if the source file timestamp is newer than the existing destination file.
  - **Up-to-Date Files:** Skipped if the destination file is equal to or newer than the source.
- **Live Progress GUI:** Real-time progress bar and status feedback during active propagation tasks.
- **Final Results Reporting:** Visual summary dashboard showing job statistics upon completion:
  - **Copied:** New files created in destination paths.
  - **Updated:** Existing files overwritten with newer versions.
  - **Not Old:** Up-to-date files left untouched.
  - **Errors:** Issues encountered during file operations.
- **Profile Management:** Save and load common source/destination directory configurations to profiles for quick execution.
- **Nightly Sync:** Schedule selected source directories to sync into each configured destination. New files and folders are created, and newer source files update destination copies in place. Existing destination-only files are left untouched; no dated or duplicate snapshot folders are created.
- **Console & GUI Logging:** Live stdout logging for terminal sessions alongside embedded GUI indicators.

---

## Direcory Synch Prgress UI (progress bar while working) totals shown after completion.

+-----------------------------------------------------------------------+
| Progress: [===============================>--------] 78%              |
| Status: Copying file_prop.py -> Office2/backups/                      |
| [ Copied: 12 | Updated: 3 | Not Old: 45 | Errors: 0 ]               |
|                                                                       |
|                          [ Start Propagation ]                        |
+-----------------------------------------------------------------------+


---

## How It Works

1. **Add Sources:** Click **Add Source File** or **Add Source Directory** to select the files/folders you want to distribute.
2. **Add Destinations:** Click **Add Destination Dir** to add one or more target folder paths (local drives, USB devices, or mounted SMB network paths). On Linux with Nemo/GVFS, you can paste a share location such as `smb://10.0.0.36/Office2`; the utility asks GVFS to mount it if needed, then resolves the URI to its filesystem path.
3. **Save Profile (Optional):** Save your source/destination setup to a named profile for future one-click loading.
4. **Run Propagation:** Click **Start Propagation**. The progress bar tracks execution, and the summary bar updates metrics live.
5. **Schedule Nightly Sync:** Add source directories and a destination, enter a 24-hour time such as `02:00`, then enable **Nightly backups while this app is running**. Keep the utility open for the scheduled run. The sync creates new files and folders in the destination and updates files when the source is newer; it does not delete destination-only files. Use **Tools → Run Nightly Backup Now** to sync immediately. The time and enabled state are saved with the profile.

---

## Technical Details & Logic

When propagation starts, the script iterates through each source file across every configured destination directory:

```text
       [ Check Destination Path ]
                   |
         Does File Exist?
          /            \
        NO              YES
        /                \
 [ Copy File ]     Compare Modification Timestamps
 (Copied +1)             /                  \
                  Source Newer?       Source Equal/Older
                       /                      \
               [ Overwrite File ]            [ Skip File ]
                  (Updated +1)               (Not Old +1)

Requirements & Execution
Prerequisites

    Python 3.8+

    Tkinter (python3-tk on Linux)

    Pillow (Pillow)

Running the Utility
Bash

python file_prop.py

License & Author

Created by EJF. Distributed under the MIT License. Contributions and feedback are welcome!
