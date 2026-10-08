# SoundBoard

A programmable desktop soundboard written in Python with Tkinter. Assign audio clips to nine buttons, rename the buttons, and play clips through any output device. It can also mix your microphone into the same output so clips and live voice go to one destination.

## Features

- **Nine clip slots** with editable labels (defaults: Applause, Laughter, Failure, Surprise, Gunshot(s), Yell, Custom 1-3)
- **Overlapping playback**: trigger several clips at once and they are mixed together
- **Choose your output device** from any stereo-capable device on the system
- **Optional live microphone monitoring**, mixed with the clips into the same output
- **Separate volume controls** for the soundboard output and the mic monitor
- **Peak level meters** (green / yellow / red) for both the output and the microphone input
- **Stop all sounds** button that silences active clips immediately
- **Saved configuration**: clip paths, labels, devices, and levels persist between sessions
- **Automatic format handling**: mono clips are duplicated to stereo, clips with more than two channels are reduced to the first two, and clips are resampled to 44.1 kHz if needed

## Requirements

- Python 3.9 or newer
- Tkinter (included with most Python installs; on some Linux distributions install it separately, e.g. `sudo apt install python3-tk`)
- Python packages: `numpy`, `sounddevice`, `soundfile`
- On Linux, the PortAudio library for `sounddevice` (e.g. `sudo apt install libportaudio2`)

Install the Python packages with:

```bash
python -m pip install numpy sounddevice soundfile
```

The script's header refers to a `requirements-soundboard.txt` file. If you keep one alongside the script, it should contain:

```text
numpy
sounddevice
soundfile
```

If the audio packages are missing, the app still opens but shows "Audio support not installed" in the status bar and cannot play sound.

## Running

```bash
python SoundBoard.py
```

## Usage

1. **Pick your audio devices.** Choose an **Output destination** and, optionally, a **Microphone source**. Select "No microphone monitoring" if you only want clip playback. Use **Refresh devices** after plugging in new hardware.
2. **Click Apply audio settings.** This starts the audio engine. Clips cannot play until you do this, and you need to click it again after changing devices.
3. **Assign clips.** Click **Choose clip...** under a button and select an audio file. Supported file types in the picker are WAV, FLAC, OGG, MP3, AIFF, and AIF. MP3 and OGG support depends on the installed version of the underlying libsndfile library.
4. **Rename buttons (optional).** Click **Edit Label**, type a new name, and press Enter, Tab, or **Done**.
5. **Play.** Click a clip button. Click it repeatedly to layer the sound over itself, or click different buttons to play several at once.
6. **Stop.** **Stop all sounds** cuts off every active clip. Microphone monitoring is not affected.
7. **Save.** Click **Save configuration** to keep your clips, labels, devices, and levels for next time.

### Level controls

| Control | What it does |
| --- | --- |
| Soundboard level | Master volume for everything sent to the output, including mic monitoring. Default 85%. |
| Mic monitor level | Volume of the microphone in the output mix. Default 100%. Set to 0 to mute the monitor. |
| Output level display | Peak meter for the mixed output signal |
| Microphone level display | Peak meter for the selected microphone |

The microphone stays open even when the monitor level is 0, so the input meter still confirms that the chosen microphone is working.

Level slider changes take effect immediately, without re-applying audio settings.

### Routing tip

To send the soundboard into another program (a chat or recording app, for example), choose a virtual audio device as the **Output destination** and select that same device as the input in the other program. The virtual device software is not part of this project.

## Configuration

Settings are saved to:

```text
~/.digital_soundboard/settings.json
```

The file stores clip file paths (not copies of the audio), button labels, the selected devices, and both level settings. Clips are referenced by their full path, so moving or deleting an audio file means you will need to choose it again. If a clip is missing when you click its button, the app tells you instead of failing silently. If the settings file can't be read, the app starts with defaults.

To reset everything, delete the settings file.

## Building an executable

From the repository root, using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --noconsole SoundBoard.py
```

The executable is written to `dist/`. If you have moved the script into its own folder, adjust the path, e.g. `pyinstaller --onefile --windowed SoundBoard/SoundBoard.py`.

## Tests

The tests in `test_soundboard_audio.py` use the standard library `unittest` module and exercise the audio engine without opening any audio hardware:

```bash
python -m unittest test_soundboard_audio -v
```

They currently verify that:

- microphone input is routed to the output in real time
- **Stop all sounds** silences active clips

Run the tests from the folder containing both files, since the test file imports `SoundBoard` directly. Note that `SoundBoard.py` imports Tkinter at load time, so Tkinter must be installed even to run the tests.

## How it works

- **`AudioEngine`** owns one output stream (stereo, 44.1 kHz, float32) and, when a microphone is selected, one mono input stream. The microphone feeds a short rolling buffer that the output callback mixes with all active clips. The mixed signal is scaled by the output level and clipped to the valid range.
- **`ActiveClip`** tracks a loaded clip and its current playback position, which allows clips to overlap.
- **`LevelMeter`** is a small canvas widget that draws a peak meter with a short decay so brief sounds remain visible.
- **`Soundboard`** is the Tkinter window. Audio callbacks run on separate threads, so they pass meter readings to the UI through a queue and the UI thread draws them.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| "Audio support not installed" in the status bar | `numpy`, `sounddevice`, or `soundfile` is not installed |
| "Click Apply audio settings before playing a sound." | Audio engine hasn't been started; click **Apply audio settings** |
| "Select an output destination." | No output device is chosen in the dropdown |
| Output dropdown is empty | No device with two or more output channels was found; try **Refresh devices** |
| A clip won't play | The file may be unsupported by your libsndfile version, or has been moved or deleted |
| You hear your own voice delayed or doubled | Mic monitoring is on; lower **Mic monitor level** or choose "No microphone monitoring" |
