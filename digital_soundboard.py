"""A programmable desktop soundboard.

Install the optional audio dependencies before running:
    python -m pip install -r requirements-soundboard.txt
"""

from __future__ import annotations

import json
import queue
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    import numpy as np
    import sounddevice as sd
    import soundfile as sf
    AUDIO_IMPORT_ERROR: Optional[Exception] = None
except ImportError as error:
    np = sd = sf = None  # type: ignore[assignment]
    AUDIO_IMPORT_ERROR = error


SLOTS = [
    "Applause", "Laughter", "Failure", "Surprise", "Gunshot(s)", "Yell",
    "Custom 1", "Custom 2", "Custom 3",
]
APP_DIR = Path.home() / ".digital_soundboard"
SETTINGS_FILE = APP_DIR / "settings.json"


@dataclass
class ActiveClip:
    samples: object
    position: int = 0


class AudioEngine:
    """Mixes clip playback and optional microphone monitoring into one output."""

    def __init__(self, status_callback, level_callback):
        self.status_callback = status_callback
        self.level_callback = level_callback
        self.sample_rate = 44100
        self.output_device = None
        self.input_device = None
        self.output_level = 0.85
        self.microphone_level = 0.0
        self._clips: list[ActiveClip] = []
        self._mic_buffer = np.empty((0, 2), dtype="float32") if np else None
        self._lock = threading.Lock()
        self._output_stream = None
        self._input_stream = None

    @property
    def available(self) -> bool:
        return AUDIO_IMPORT_ERROR is None

    def start(self, output_device, input_device, output_level, microphone_level):
        if not self.available:
            raise RuntimeError(f"Audio packages are unavailable: {AUDIO_IMPORT_ERROR}")
        self.stop()
        self.output_device = output_device
        self.input_device = input_device
        self.output_level = output_level
        self.microphone_level = microphone_level
        self._output_stream = sd.OutputStream(
            device=output_device, samplerate=self.sample_rate, channels=2,
            dtype="float32", callback=self._output_callback,
        )
        self._output_stream.start()
        # Keep the selected input open even at zero monitor volume: the input
        # meter remains useful for confirming that the chosen microphone works.
        if input_device is not None:
            self._input_stream = sd.InputStream(
                device=input_device, samplerate=self.sample_rate, channels=1,
                dtype="float32", callback=self._input_callback,
            )
            self._input_stream.start()
        self.status_callback("Audio engine ready")

    def stop(self):
        for stream_name in ("_input_stream", "_output_stream"):
            stream = getattr(self, stream_name)
            if stream is not None:
                try:
                    stream.stop()
                    stream.close()
                except Exception:
                    pass
                setattr(self, stream_name, None)
        with self._lock:
            self._clips.clear()
            self._mic_buffer = np.empty((0, 2), dtype="float32")

    def set_levels(self, output_level, microphone_level):
        self.output_level = output_level
        self.microphone_level = microphone_level

    def play(self, filename: str):
        if self._output_stream is None:
            raise RuntimeError("Click Apply audio settings before playing a sound.")
        samples, rate = sf.read(filename, dtype="float32", always_2d=True)
        if samples.shape[1] == 1:
            samples = np.repeat(samples, 2, axis=1)
        elif samples.shape[1] > 2:
            samples = samples[:, :2]
        if rate != self.sample_rate:
            source_frames = samples.shape[0]
            target_frames = max(1, round(source_frames * self.sample_rate / rate))
            old_positions = np.linspace(0, source_frames - 1, target_frames)
            samples = np.column_stack([
                np.interp(old_positions, np.arange(source_frames), samples[:, channel])
                for channel in range(2)
            ]).astype("float32")
        with self._lock:
            self._clips.append(ActiveClip(samples))

    def stop_sounds(self):
        with self._lock:
            self._clips.clear()

    def _input_callback(self, indata, frames, time_info, status):
        if status:
            self.status_callback(f"Microphone warning: {status}")
        with self._lock:
            stereo_input = np.repeat(indata, 2, axis=1)
            self._mic_buffer = np.concatenate((self._mic_buffer, stereo_input))[-self.sample_rate * 2:]
        self.level_callback("input", float(np.max(np.abs(indata))))

    def _output_callback(self, outdata, frames, time_info, status):
        mixed = np.zeros((frames, 2), dtype="float32")
        with self._lock:
            if self.microphone_level > 0 and len(self._mic_buffer):
                mic = self._mic_buffer[:frames]
                self._mic_buffer = self._mic_buffer[len(mic):]
                mixed[:len(mic)] += mic * self.microphone_level
            remaining = []
            for clip in self._clips:
                end = min(clip.position + frames, len(clip.samples))
                clip_frames = end - clip.position
                mixed[:clip_frames] += clip.samples[clip.position:end]
                clip.position = end
                if clip.position < len(clip.samples):
                    remaining.append(clip)
            self._clips = remaining
        outdata[:] = np.clip(mixed * self.output_level, -1.0, 1.0)
        self.level_callback("output", float(np.max(np.abs(outdata))))
        if status:
            self.status_callback(f"Output warning: {status}")


class LevelMeter(tk.Canvas):
    """A simple peak meter with green, yellow, and red ranges."""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=18, highlightthickness=0, background="#20242a", **kwargs)
        self._value = 0.0
        self.bind("<Configure>", lambda event: self._draw())

    def set_level(self, value: float):
        # A short decay makes momentary sounds easy to see.
        self._value = max(value, self._value * 0.78)
        self._draw()

    def _draw(self):
        width, height = self.winfo_width(), self.winfo_height()
        self.delete("all")
        if width <= 1:
            return
        level_width = int(min(1.0, self._value) * width)
        green_end, yellow_end = int(width * .70), int(width * .90)
        if level_width:
            self.create_rectangle(0, 0, min(level_width, green_end), height, fill="#36bd65", outline="")
        if level_width > green_end:
            self.create_rectangle(green_end, 0, min(level_width, yellow_end), height, fill="#f2c94c", outline="")
        if level_width > yellow_end:
            self.create_rectangle(yellow_end, 0, level_width, height, fill="#eb5757", outline="")
        for mark in (green_end, yellow_end):
            self.create_line(mark, 0, mark, height, fill="#20242a")


class Soundboard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Digital Programmable Soundboard")
        self.minsize(850, 560)
        self._meter_events: queue.SimpleQueue[tuple[str, float]] = queue.SimpleQueue()
        self.engine = AudioEngine(self._set_status_threadsafe, self._queue_level)
        self.files = {slot: "" for slot in SLOTS}
        self.file_labels: dict[str, ttk.Label] = {}
        self.output_var = tk.StringVar()
        self.input_var = tk.StringVar()
        self.output_level = tk.DoubleVar(value=85)
        self.microphone_level = tk.DoubleVar(value=0)
        self.status_var = tk.StringVar(value="Choose audio devices, then click Apply audio settings.")
        self._build_ui()
        self._load_settings()
        self._refresh_devices()
        self.after(40, self._update_meters)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self):
        root = ttk.Frame(self, padding=14)
        root.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)

        controls = ttk.LabelFrame(root, text="Audio routing", padding=10)
        controls.grid(row=0, column=0, sticky="ew")
        controls.columnconfigure(1, weight=1)
        ttk.Label(controls, text="Output destination").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.output_box = ttk.Combobox(controls, textvariable=self.output_var, state="readonly")
        self.output_box.grid(row=0, column=1, sticky="ew")
        ttk.Label(controls, text="Microphone source").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.input_box = ttk.Combobox(controls, textvariable=self.input_var, state="readonly")
        self.input_box.grid(row=1, column=1, sticky="ew", pady=(8, 0))
        ttk.Button(controls, text="Refresh devices", command=self._refresh_devices).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(controls, text="Apply audio settings", command=self._apply_audio).grid(row=1, column=2, padx=(8, 0), pady=(8, 0))
        ttk.Label(controls, text="Soundboard level").grid(row=2, column=0, sticky="w", pady=(10, 0))
        ttk.Scale(controls, from_=0, to=100, variable=self.output_level, command=self._levels_changed).grid(row=2, column=1, sticky="ew", pady=(10, 0))
        self.output_meter = LevelMeter(controls)
        self.output_meter.grid(row=3, column=1, sticky="ew", pady=(3, 0))
        ttk.Label(controls, text="Output level display").grid(row=3, column=0, sticky="w", pady=(3, 0))
        ttk.Label(controls, text="Mic monitor level").grid(row=4, column=0, sticky="w", pady=(8, 0))
        ttk.Scale(controls, from_=0, to=100, variable=self.microphone_level, command=self._levels_changed).grid(row=4, column=1, sticky="ew", pady=(8, 0))
        self.input_meter = LevelMeter(controls)
        self.input_meter.grid(row=5, column=1, sticky="ew", pady=(3, 0))
        ttk.Label(controls, text="Microphone level display").grid(row=5, column=0, sticky="w", pady=(3, 0))

        board = ttk.LabelFrame(root, text="Sound clips", padding=10)
        board.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        root.rowconfigure(1, weight=1)
        for index, slot in enumerate(SLOTS):
            row, column = divmod(index, 3)
            cell = ttk.Frame(board, padding=5)
            cell.grid(row=row, column=column, sticky="nsew")
            board.columnconfigure(column, weight=1)
            ttk.Button(cell, text=slot, command=lambda name=slot: self._play_slot(name), width=20).grid(row=0, column=0, sticky="ew")
            ttk.Button(cell, text="Choose clip…", command=lambda name=slot: self._choose_clip(name)).grid(row=1, column=0, sticky="ew", pady=(4, 0))
            label = ttk.Label(cell, text="No clip selected", foreground="#666666", wraplength=215)
            label.grid(row=2, column=0, sticky="ew", pady=(3, 0))
            self.file_labels[slot] = label

        footer = ttk.Frame(root)
        footer.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(footer, text="Stop all sounds", command=self.engine.stop_sounds).pack(side="left")
        ttk.Button(footer, text="Save configuration", command=self._save_settings).pack(side="left", padx=8)
        ttk.Label(footer, textvariable=self.status_var).pack(side="right")

    def _refresh_devices(self):
        if not self.engine.available:
            self.status_var.set("Audio support not installed — see requirements-soundboard.txt")
            return
        try:
            devices = sd.query_devices()
            output = [f"{i}: {d['name']}" for i, d in enumerate(devices) if d["max_output_channels"] >= 2]
            inputs = ["No microphone monitoring"] + [f"{i}: {d['name']}" for i, d in enumerate(devices) if d["max_input_channels"] >= 1]
            self.output_box["values"] = output
            self.input_box["values"] = inputs
            if not self.output_var.get() and output:
                self.output_var.set(output[0])
            if not self.input_var.get():
                self.input_var.set(inputs[0])
            self.status_var.set("Audio devices refreshed")
        except Exception as error:
            self.status_var.set(f"Could not list audio devices: {error}")

    @staticmethod
    def _device_number(value: str):
        return None if not value or value == "No microphone monitoring" else int(value.split(":", 1)[0])

    def _apply_audio(self):
        try:
            output = self._device_number(self.output_var.get())
            if output is None:
                raise ValueError("Select an output destination.")
            self.engine.start(output, self._device_number(self.input_var.get()), self.output_level.get() / 100, self.microphone_level.get() / 100)
        except Exception as error:
            messagebox.showerror("Audio setup", str(error))
            self.status_var.set("Audio setup failed")

    def _levels_changed(self, unused=None):
        self.engine.set_levels(self.output_level.get() / 100, self.microphone_level.get() / 100)

    def _choose_clip(self, slot: str):
        filename = filedialog.askopenfilename(title=f"Choose {slot} sound", filetypes=[("Audio files", "*.wav *.flac *.ogg *.mp3 *.aiff *.aif"), ("All files", "*.*")])
        if filename:
            self.files[slot] = filename
            self.file_labels[slot].config(text=Path(filename).name, foreground="#222222")

    def _play_slot(self, slot: str):
        filename = self.files[slot]
        if not filename:
            messagebox.showinfo("Choose a clip", f"Choose an audio file for {slot} first.")
            return
        if not Path(filename).is_file():
            messagebox.showerror("Missing clip", f"This audio file no longer exists:\n{filename}")
            return
        try:
            self.engine.play(filename)
            self.status_var.set(f"Playing {slot}")
        except Exception as error:
            messagebox.showerror("Could not play sound", str(error))

    def _save_settings(self):
        try:
            APP_DIR.mkdir(exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps({"files": self.files, "output": self.output_var.get(), "input": self.input_var.get(), "output_level": self.output_level.get(), "microphone_level": self.microphone_level.get()}, indent=2), encoding="utf-8")
            self.status_var.set("Configuration saved")
        except OSError as error:
            messagebox.showerror("Save configuration", str(error))

    def _load_settings(self):
        if not SETTINGS_FILE.is_file():
            return
        try:
            settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            self.files.update({slot: settings.get("files", {}).get(slot, "") for slot in SLOTS})
            for slot, filename in self.files.items():
                if filename:
                    self.file_labels[slot].config(text=Path(filename).name, foreground="#222222")
            self.output_var.set(settings.get("output", ""))
            self.input_var.set(settings.get("input", ""))
            self.output_level.set(settings.get("output_level", 85))
            self.microphone_level.set(settings.get("microphone_level", 0))
        except (OSError, json.JSONDecodeError):
            self.status_var.set("Saved configuration could not be read")

    def _set_status_threadsafe(self, message: str):
        self.after(0, self.status_var.set, message)

    def _queue_level(self, device: str, level: float):
        """Audio callbacks enqueue readings; Tk draws meters on its own thread."""
        self._meter_events.put((device, level))

    def _update_meters(self):
        readings: dict[str, float] = {}
        while True:
            try:
                device, level = self._meter_events.get_nowait()
                readings[device] = max(readings.get(device, 0.0), level)
            except queue.Empty:
                break
        if "input" in readings:
            self.input_meter.set_level(readings["input"])
        else:
            self.input_meter.set_level(0.0)
        if "output" in readings:
            self.output_meter.set_level(readings["output"])
        else:
            self.output_meter.set_level(0.0)
        self.after(40, self._update_meters)

    def _close(self):
        self.engine.stop()
        self.destroy()


if __name__ == "__main__":
    Soundboard().mainloop()
