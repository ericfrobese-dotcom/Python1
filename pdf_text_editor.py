#  Special instrctions for creating executable with pyinstaller:
# 
# pyinstaller --onefile --noconsole --hidden-import PIL._tkinter_finder pdf_text_editor.py
# 
#  if --hidden-import is missing executable wont load pdf 
#
from __future__ import annotations
import traceback
import json
import os
import tkinter as tk
from html import escape
from tkinter import font as tkfont
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import Image, ImageTk
import pymupdf as fitz


def _valid_directory(path, fallback=None):
    """Return an existing directory, falling back to the current directory."""
    candidate = Path(path).expanduser() if path else None
    if candidate is not None and candidate.is_dir():
        return candidate
    if fallback is not None:
        fallback = Path(fallback).expanduser()
        if fallback.is_dir():
            return fallback
    return Path.cwd()


def _preferences_path():
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return config_home / "pdf_text_editor" / "directories.json"


def load_directory_preferences():
    """Load remembered dialog directories, ignoring stale or malformed settings."""
    default = _valid_directory(None)
    try:
        with _preferences_path().open(encoding="utf-8") as settings_file:
            preferences = json.load(settings_file)
    except (OSError, ValueError, TypeError):
        preferences = {}
    return (
        _valid_directory(preferences.get("load_directory"), default),
        _valid_directory(preferences.get("save_directory"), default),
    )


def save_directory_preferences(load_directory, save_directory):
    """Persist only existing directories; a failure must not block PDF editing."""
    try:
        settings_path = _preferences_path()
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with settings_path.open("w", encoding="utf-8") as settings_file:
            json.dump(
                {
                    "load_directory": str(_valid_directory(load_directory)),
                    "save_directory": str(_valid_directory(save_directory)),
                },
                settings_file,
            )
    except OSError:
        pass


def normalize_insert_text(text):
    if text is None:
        return ""

    mapping = {
        "ﬁ": "fi",
        "ﬂ": "fl",
        "ﬀ": "ff",
        "ﬃ": "ffi",
        "ﬄ": "ffl",
        "ﬅ": "st",
        "ﬆ": "st",
    }
    normalized = str(text)
    for source, target in sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True):
        normalized = normalized.replace(source, target)
    return normalized


def normalize_font_name(font_name, flags=0):
    if not font_name:
        name = ""
    else:
        name = str(font_name).strip()

    lowered = name.lower().replace(" ", "-")
    candidate_names = [lowered, name.lower(), name]

    if any(token in lowered for token in ("helvetica", "helv")):
        if flags & fitz.TEXT_FONT_BOLD and flags & fitz.TEXT_FONT_ITALIC:
            return "hebi"
        if flags & fitz.TEXT_FONT_BOLD:
            return "hebo"
        if flags & fitz.TEXT_FONT_ITALIC:
            return "heit"
        if any(token in lowered for token in ("boldoblique", "oblique", "italic")):
            return "hebi" if "bold" in lowered else "heit"
        return "helv"

    if any(token in lowered for token in ("times", "tiro")):
        if flags & fitz.TEXT_FONT_BOLD and flags & fitz.TEXT_FONT_ITALIC:
            return "tibi"
        if flags & fitz.TEXT_FONT_BOLD:
            return "tibo"
        if flags & fitz.TEXT_FONT_ITALIC:
            return "tiit"
        if any(token in lowered for token in ("bolditalic", "italic", "oblique")):
            return "tibi" if "bold" in lowered else "tiit"
        return "tiro"

    if any(token in lowered for token in ("courier", "cour")):
        if flags & fitz.TEXT_FONT_BOLD and flags & fitz.TEXT_FONT_ITALIC:
            return "cobi"
        if flags & fitz.TEXT_FONT_BOLD:
            return "cobo"
        if flags & fitz.TEXT_FONT_ITALIC:
            return "coit"
        if any(token in lowered for token in ("bolditalic", "italic", "oblique")):
            return "cobi" if "bold" in lowered else "coit"
        return "cour"

    if any(token in lowered for token in ("symbol", "zapf")):
        return "symb"

    if "hebo" in candidate_names or "bold" in lowered:
        return "hebo"

    return "helv"


def color_int_to_rgb(color):
    """Convert PyMuPDF's packed span colour to an RGB tuple."""
    color = int(color or 0)
    return ((color >> 16 & 255) / 255, (color >> 8 & 255) / 255, (color & 255) / 255)


def rgb_to_hex(color):
    red, green, blue = color
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


def edit_value_and_style(value, original_style):
    """Accept legacy string edits as well as styled editor edit dictionaries."""
    if isinstance(value, dict):
        style = dict(original_style)
        style.update({key: value[key] for key in ("font", "size", "flags", "color") if key in value})
        return str(value.get("text", "")), style
    return str(value), dict(original_style)


def style_to_css(style):
    family = {"helv": "Helvetica", "tiro": "Times New Roman", "cour": "Courier New"}
    font = style["font"]
    if font.startswith("ti"):
        font_family = family["tiro"]
    elif font.startswith("co"):
        font_family = family["cour"]
    else:
        font_family = family["helv"]
    return (
        f"font-family: {font_family}; font-size: {float(style['size']):g}pt; "
        f"font-weight: {'bold' if style['flags'] & fitz.TEXT_FONT_BOLD else 'normal'}; "
        f"font-style: {'italic' if style['flags'] & fitz.TEXT_FONT_ITALIC else 'normal'}; "
        f"color: {rgb_to_hex(style['color'])};"
    )


def styled_runs_to_html(runs, fallback_style):
    fragments = []
    for run in runs:
        style = dict(fallback_style)
        style.update(run.get("style", {}))
        text = escape(str(run.get("text", ""))).replace("\n", "<br>")
        fragments.append(f'<span style="{style_to_css(style)}">{text}</span>')
    return "<div>" + "".join(fragments) + "</div>"


def get_block_style(page, block_index):
    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])
    if block_index >= len(blocks):
        return {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}

    block = blocks[block_index]
    if block.get("type") != 0:
        return {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}

    for line in block.get("lines", []):
        for span in line.get("spans", []):
            flags = int(span.get("flags", 0))
            font = normalize_font_name(span.get("font", "helv"), flags=flags)
            return {
                "font": font,
                "size": float(span.get("size", 11)),
                "flags": flags,
                "color": color_int_to_rgb(span.get("color", 0)),
            }

    return {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}


def apply_pdf_text_edits(pdf_path, edits_by_page):
    """Return a new PDF document with the selected text blocks replaced.

    Each edit overlays a white rectangle over the original text area and then
    writes the replacement text using the original font/size metadata whenever
    available.
    """
    if not pdf_path:
        raise ValueError("A PDF path is required.")

    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(pdf_path)

    source_doc = fitz.open(str(path))
    edited_doc = fitz.open()

    for page_index in range(len(source_doc)):
        source_page = source_doc[page_index]
        page_rect = source_page.rect
        target_page = edited_doc.new_page(width=page_rect.width, height=page_rect.height)

        pix = source_page.get_pixmap(alpha=False)
        target_page.insert_image(target_page.rect, pixmap=pix)

        page_edits = edits_by_page.get(page_index, {})
        if not page_edits:
            continue

        custom_sections = page_edits.get("__custom_sections__", [])
        for section in custom_sections:
            rect = fitz.Rect(
                float(section["x0"]),
                float(section["y0"]),
                float(section["x1"]),
                float(section["y1"]),
            )
            style = dict(section.get("style", {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}))
            target_page.draw_rect(rect, fill=(1, 1, 1), color=(1, 1, 1), overlay=True)
            runs = section.get("runs")
            if isinstance(runs, list) and runs:
                html = styled_runs_to_html(runs, style)
                spare_height, scale = target_page.insert_htmlbox(
                    rect,
                    html,
                    css="body { margin: 0; padding: 0; line-height: 1.15; }",
                    scale_low=0,
                )
                if spare_height < 0 or scale == 0:
                    raise ValueError(
                        f"The custom text section on page {page_index + 1} does not fit within its bounding box."
                    )
                continue
            text = str(section.get("text", ""))
            font_size = float(style["size"])
            result = target_page.insert_textbox(
                rect,
                normalize_insert_text(text),
                fontsize=font_size,
                fontname=style["font"],
                color=tuple(style["color"]),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            while result < 0 and font_size > 4:
                font_size -= 0.5
                result = target_page.insert_textbox(
                    rect,
                    normalize_insert_text(text),
                    fontsize=font_size,
                    fontname=style["font"],
                    color=tuple(style["color"]),
                    align=fitz.TEXT_ALIGN_LEFT,
                )
            if result < 0:
                raise ValueError(
                    f"The custom text section on page {page_index + 1} does not fit within its bounding box."
                )

        blocks = source_page.get_text("blocks")
        for block_index, edit in page_edits.items():
            if block_index == "__custom_sections__":
                continue
            if not isinstance(block_index, int) or block_index >= len(blocks):
                continue

            x0, y0, x1, y1 = blocks[block_index][:4]
            original_style = get_block_style(source_page, block_index)
            new_text, style = edit_value_and_style(edit, original_style)
            rect = fitz.Rect(float(x0) - 2, float(y0) - 2, float(x1) + 2, float(y1) + 2)
            target_page.draw_rect(rect, fill=(1, 1, 1), color=(1, 1, 1), overlay=True)
            if isinstance(edit, dict) and edit.get("runs") is not None:
                spare_height, scale = target_page.insert_htmlbox(
                    rect,
                    styled_runs_to_html(edit["runs"], style),
                    css="body { margin: 0; padding: 0; line-height: 1.15; }",
                    scale_low=0,
                )
                if spare_height < 0 or scale == 0:
                    raise ValueError(
                        f"The edited text in page {page_index + 1}, block {block_index + 1} does not fit its original area."
                    )
                continue
            font_size = float(style["size"])
            result = target_page.insert_textbox(
                rect,
                normalize_insert_text(new_text),
                fontsize=font_size,
                fontname=style["font"],
                color=tuple(style["color"]),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            while result < 0 and font_size > 4:
                font_size -= 0.5
                result = target_page.insert_textbox(
                    rect,
                    normalize_insert_text(new_text),
                    fontsize=font_size,
                    fontname=style["font"],
                    color=tuple(style["color"]),
                    align=fitz.TEXT_ALIGN_LEFT,
                )
            if result < 0:
                raise ValueError(
                    f"The edited text in page {page_index + 1}, block {block_index + 1} does not fit its original area."
                )

    source_doc.close()
    return edited_doc


def save_pdf_with_edits(pdf_path, edits_by_page, output_path=None):
    """Save a PDF with edits to output_path or overwrite the original file."""
    input_path = Path(pdf_path)
    if output_path is None:
        output_path = input_path
    else:
        output_path = Path(output_path)

    edited_doc = apply_pdf_text_edits(str(input_path), edits_by_page)

    if output_path == input_path:
        temp_path = input_path.with_suffix(".tmp_edit.pdf")
        edited_doc.save(str(temp_path), garbage=4, deflate=True)
        edited_doc.close()
        os.replace(str(temp_path), str(input_path))
        return str(input_path)

    edited_doc.save(str(output_path), garbage=4, deflate=True)
    edited_doc.close()
    return str(output_path)


def extract_pdf_text_blocks(pdf_path):
    """Return text blocks from a PDF as a list of dictionaries.

    Each item contains the page number, original block index, text content,
    and the bounding rectangle.
    """
    if not pdf_path:
        return []

    path = Path(pdf_path)
    if not path.exists() or path.suffix.lower() != ".pdf":
        return []

    try:
        doc = fitz.open(str(path))
    except Exception:
        return []

    blocks = []
    for page_no in range(len(doc)):
        page = doc[page_no]
        for block_index, block in enumerate(page.get_text("blocks")):
            if len(block) < 6:
                continue
            x0, y0, x1, y1, text = block[:5]
            clean_text = str(text).strip()
            if not clean_text:
                continue
            blocks.append(
                {
                    "page": page_no + 1,
                    "block_index": block_index,
                    "text": clean_text,
                    "x0": float(x0),
                    "y0": float(y0),
                    "x1": float(x1),
                    "y1": float(y1),
                }
            )
    doc.close()
    return blocks


class PDFTextEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Text Editor")
        self.root.geometry("1200x760")
        self.root.minsize(960, 600)

        self.doc = None
        self.current_page_index = 0
        self.selected_block_index = None
        self.page_blocks = []
        self.pending_edits = {}
        self.page_image = None
        self.preview_scale_x = 1.0
        self.preview_scale_y = 1.0
        self.selected_custom_section_id = None
        self.custom_section_counter = 0
        self.section_drag_state = None
        self.section_resize_state = None
        self.inline_editor = None
        self.inline_editor_window = None
        self.inline_editor_frame = None
        self.font_family_var = None
        self.font_size_var = None
        self.bold_var = None
        self.italic_var = None
        self.text_color = "#000000"
        self.style_tags = {}
        self.next_style_tag = 0
        self.inline_changed = False
        self.attribute_controls = []
        self.attribute_drag_offset = None
        self.last_load_directory, self.last_save_directory = load_directory_preferences()

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self.root, padding=(10, 10, 10, 6))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(side="left")
        ttk.Button(toolbar, text="Add Text Section", command=self.add_custom_text_section).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Save Edited PDF", command=self.save_edited_pdf).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Reset attributes bar", command=self._reset_attribute_bar).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Open a PDF, then click text on the page to edit it in place.")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="left", padx=(18, 0))

        document = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        document.pack(fill="both", expand=True)

        page_controls = ttk.Frame(document)
        page_controls.pack(fill="x")
        ttk.Label(page_controls, text="Page:").pack(side="left")
        self.page_selector = ttk.Combobox(page_controls, state="readonly", width=12)
        self.page_selector.pack(side="left", padx=(6, 0))
        self.page_selector.bind("<<ComboboxSelected>>", self.on_page_selected)
        ttk.Label(
            page_controls,
            text="Click a text area to edit it. Click elsewhere or press Ctrl+Enter to keep the change.",
        ).pack(side="left", padx=(16, 0))

        preview = ttk.Frame(document)
        preview.pack(fill="both", expand=True, pady=(8, 0))
        preview.rowconfigure(0, weight=1)
        preview.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(
            preview,
            width=900,
            height=680,
            bg="#e6e6e6",
            highlightthickness=1,
            highlightbackground="#7a7a7a",
        )
        vertical_scroll = ttk.Scrollbar(preview, orient="vertical", command=self.canvas.yview)
        horizontal_scroll = ttk.Scrollbar(preview, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=horizontal_scroll.set, yscrollcommand=vertical_scroll.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vertical_scroll.grid(row=0, column=1, sticky="ns")
        horizontal_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas.bind("<Button-1>", self.on_canvas_clicked)
        self.canvas.bind("<B1-Motion>", self._handle_custom_section_drag)
        self.canvas.bind("<ButtonRelease-1>", self._finish_custom_section_drag)
        self._build_attribute_bar()

    def _build_attribute_bar(self):
        """Create a floating, draggable bar for styling selected editor text."""
        self.attribute_bar = ttk.Frame(self.root, padding=4, relief="raised", borderwidth=1)
        grip = ttk.Label(self.attribute_bar, text="Text attributes  ⠿", cursor="fleur")
        grip.pack(side="left", padx=(0, 6))
        grip.bind("<ButtonPress-1>", self._start_attribute_bar_drag)
        grip.bind("<B1-Motion>", self._drag_attribute_bar)
        grip.bind("<ButtonRelease-1>", self._finish_attribute_bar_drag)
        self.root.bind("<Configure>", lambda _event: self.attribute_bar.lift(), add="+")

        self.font_family_var = tk.StringVar(value="Helvetica")
        self.font_size_var = tk.StringVar(value="11")
        self.bold_var = tk.BooleanVar(value=False)
        self.italic_var = tk.BooleanVar(value=False)
        self.font_selector = ttk.Combobox(self.attribute_bar, textvariable=self.font_family_var,
                                          values=("Helvetica", "Times", "Courier"), state="readonly", width=10)
        self.font_selector.pack(side="left")
        self.size_entry = ttk.Spinbox(self.attribute_bar, from_=4, to=144, textvariable=self.font_size_var, width=4)
        self.size_entry.pack(side="left", padx=(4, 0))
        self.bold_button = ttk.Checkbutton(self.attribute_bar, text="B", variable=self.bold_var,
                                           command=self._apply_style_to_selection)
        self.bold_button.pack(side="left", padx=(5, 0))
        self.italic_button = ttk.Checkbutton(self.attribute_bar, text="I", variable=self.italic_var,
                                             command=self._apply_style_to_selection)
        self.italic_button.pack(side="left")
        self.color_button = tk.Button(self.attribute_bar, text="Color", command=self._choose_text_color, width=6)
        self.color_button.pack(side="left", padx=(4, 0))
        self.attribute_controls = [self.font_selector, self.size_entry, self.bold_button, self.italic_button, self.color_button]
        self.font_selector.bind("<<ComboboxSelected>>", self._apply_style_to_selection)
        self.size_entry.configure(command=self._apply_style_to_selection)
        self.size_entry.bind("<Return>", self._apply_style_to_selection)
        self.size_entry.bind("<FocusOut>", self._apply_style_to_selection)
        self._reset_attribute_bar()
        self._set_attribute_bar_enabled(False)

    def _start_attribute_bar_drag(self, event):
        self.attribute_drag_offset = (event.x_root - self.attribute_bar.winfo_rootx(), event.y_root - self.attribute_bar.winfo_rooty())
        self.attribute_bar.lift()
        event.widget.grab_set()

    def _drag_attribute_bar(self, event):
        if self.attribute_drag_offset is None:
            return
        offset_x, offset_y = self.attribute_drag_offset
        self.root.update_idletasks()
        x = event.x_root - self.root.winfo_rootx() - offset_x
        y = event.y_root - self.root.winfo_rooty() - offset_y
        x = max(0, min(x, max(0, self.root.winfo_width() - self.attribute_bar.winfo_width())))
        y = max(0, min(y, max(0, self.root.winfo_height() - self.attribute_bar.winfo_height())))
        # Clear the reset position's relative coordinates.  Otherwise a drag
        # offsets from the bottom-centre and can hide the bar off-screen.
        self.attribute_bar.place(relx=0, rely=0)
        self.attribute_bar.place(x=x, y=y, anchor="nw")
        self.attribute_bar.lift()

    def _finish_attribute_bar_drag(self, event=None):
        self.attribute_drag_offset = None
        if event is not None:
            event.widget.grab_release()

    def _reset_attribute_bar(self):
        """Return the floating bar to its visible default position."""
        self.attribute_bar.place(relx=0.5, rely=1.0, x=0, y=-8, anchor="s")
        self.attribute_bar.lift()

    def _set_attribute_bar_enabled(self, enabled):
        state = "normal" if enabled else "disabled"
        for control in self.attribute_controls:
            control.configure(state=state)

    def _next_custom_section_id(self):
        self.custom_section_counter += 1
        return f"custom-section-{self.custom_section_counter}"

    def _add_new_text_section(self, x=None, y=None, width=180, height=46, text="New text"):
        if self.doc is None:
            return None

        page = self.doc[self.current_page_index]
        rect = page.rect
        left = float(x if x is not None else rect.width * 0.12)
        top = float(y if y is not None else rect.height * 0.12)
        width = float(width)
        height = float(height)

        self.commit_inline_edit()

        page_edits = self.pending_edits.setdefault(self.current_page_index, {})
        sections = page_edits.setdefault("__custom_sections__", [])
        offset_x = 0.0
        offset_y = 0.0
        style = {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}
        for _ in range(150):
            candidate = {
                "id": self._next_custom_section_id(),
                "x0": left + offset_x,
                "y0": top + offset_y,
                "x1": left + width + offset_x,
                "y1": top + height + offset_y,
                "text": text,
                "runs": [{"text": str(text), "style": dict(style)}],
                "style": dict(style),
            }
            if not any(
                candidate["x0"] < existing["x1"] and candidate["x1"] > existing["x0"]
                and candidate["y0"] < existing["y1"] and candidate["y1"] > existing["y0"]
                for existing in sections
            ):
                sections.append(candidate)
                self.selected_custom_section_id = candidate["id"]
                self._render_page_preview(page)
                return candidate
            offset_x += 18
            if offset_x > rect.width:
                offset_x = 0
                offset_y += 18
        candidate = {
            "id": self._next_custom_section_id(),
            "x0": left,
            "y0": top,
            "x1": left + width,
            "y1": top + height,
            "text": text,
            "runs": [{"text": str(text), "style": {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}}],
            "style": {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)},
        }
        sections.append(candidate)
        self.selected_custom_section_id = candidate["id"]
        self._render_page_preview(page)
        return candidate

    def _resize_text_section(self, section_id, x=None, y=None, width=None, height=None):
        page_edits = self.pending_edits.get(self.current_page_index, {})
        for section in page_edits.get("__custom_sections__", []):
            if section.get("id") != section_id:
                continue
            left = float(x if x is not None else section["x0"])
            top = float(y if y is not None else section["y0"])
            new_width = float(width if width is not None else section["x1"] - section["x0"])
            new_height = float(height if height is not None else section["y1"] - section["y0"])
            section["x0"] = left
            section["y0"] = top
            section["x1"] = left + new_width
            section["y1"] = top + new_height
            if self.doc is not None:
                self._render_page_preview(self.doc[self.current_page_index])
            return section
        return None

    def add_custom_text_section(self):
        if self.doc is None:
            self.status_var.set("Open a PDF before adding a text section.")
            return
        page = self.doc[self.current_page_index]
        section = self._add_new_text_section(
            x=page.rect.width * 0.18,
            y=page.rect.height * 0.18,
            width=180,
            height=44,
        )
        if section is not None:
            self.status_var.set(f"Added text section {section['id']} on page {self.current_page_index + 1}.")
            self._show_inline_editor_for_custom_section(section["id"])

    def _custom_section_at_canvas_position(self, x, y):
        for section in self.pending_edits.get(self.current_page_index, {}).get("__custom_sections__", []):
            if (
                section["x0"] * self.preview_scale_x <= x <= section["x1"] * self.preview_scale_x
                and section["y0"] * self.preview_scale_y <= y <= section["y1"] * self.preview_scale_y
            ):
                return section
        return None

    def _show_inline_editor_for_custom_section(self, section_id):
        section = None
        for candidate in self.pending_edits.get(self.current_page_index, {}).get("__custom_sections__", []):
            if candidate.get("id") == section_id:
                section = candidate
                break
        if section is None:
            return

        self.selected_block_index = None
        self.selected_custom_section_id = section_id
        style = dict(section.get("style", {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}))
        self._set_attribute_bar_style(style)
        self.inline_editor_frame = tk.Frame(
            self.canvas, bg="#f5f8ff", highlightthickness=1, highlightbackground="#2b78e4"
        )
        self.inline_editor = tk.Text(
            self.inline_editor_frame,
            wrap="word",
            undo=True,
            exportselection=False,
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            font=self._tk_font_tuple(style),
            foreground=rgb_to_hex(style["color"]),
        )
        self.inline_editor.pack(fill="both", expand=True)
        displayed_text = str(section.get("text", ""))
        self.inline_editor.insert("1.0", displayed_text)
        self.inline_editor.bind("<Control-Return>", self.commit_inline_edit)
        self.inline_editor.bind("<<Modified>>", self._mark_inline_text_changed)
        self.inline_editor.bind("<ButtonRelease-1>", self._sync_attribute_bar_to_selection)
        self.inline_editor.bind("<KeyRelease>", self._on_editor_key_release)
        self.style_tags = {}
        self.next_style_tag = 0
        self.inline_changed = False
        initial_runs = section.get("runs") if isinstance(section.get("runs"), list) else []
        offset = 0
        for run in initial_runs:
            run_text = str(run.get("text", ""))
            if not run_text:
                continue
            run_style = dict(style)
            run_style.update(run.get("style", {}))
            self._apply_style_tag(f"1.0+{offset}c", f"1.0+{offset + len(run_text)}c", run_style)
            offset += len(run_text)
        if offset != len(displayed_text):
            self._apply_style_tag("1.0", "end-1c", style)
        self._set_attribute_bar_enabled(True)
        width = max(90, (section["x1"] - section["x0"]) * self.preview_scale_x + 8)
        height = max(30, (section["y1"] - section["y0"]) * self.preview_scale_y + 8)
        self.inline_editor_window = self.canvas.create_window(
            section["x0"] * self.preview_scale_x,
            section["y0"] * self.preview_scale_y,
            anchor="nw",
            width=width,
            height=height,
            window=self.inline_editor_frame,
        )
        self.inline_editor.focus_set()
        self.inline_editor.edit_modified(False)
        self.status_var.set("Edit the custom text section, then click elsewhere or press Ctrl+Enter to keep it.")

    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")],
            initialdir=str(_valid_directory(self.last_load_directory)),
        )
        if not pdf_path:
            return

        self.last_load_directory = _valid_directory(Path(pdf_path).parent, self.last_load_directory)
        save_directory_preferences(self.last_load_directory, self.last_save_directory)

        self.commit_inline_edit()
        if self.doc is not None:
            self.doc.close()
        self.doc = fitz.open(pdf_path)
        self.page_selector.config(values=[f"Page {i+1}" for i in range(len(self.doc))])
        self.page_selector.current(0)
        self.pending_edits.clear()
        self.load_page(0)
        self.status_var.set(f"Loaded {Path(pdf_path).name} ({len(self.doc)} pages)")

    def on_page_selected(self, _event):
        if not self.doc:
            return
        try:
            selected_index = self.page_selector.current()
            self.load_page(selected_index)
        except Exception:
            self.status_var.set("Unable to switch pages.")

    def load_page(self, page_index):
        if not self.doc:
            return

        self.commit_inline_edit()
        self.current_page_index = page_index
        page = self.doc[page_index]
        self.page_blocks = self._collect_blocks(page)
        self.selected_block_index = None

        self._render_page_preview(page)
        if self.page_blocks:
            self.status_var.set(f"Page {page_index + 1}: click a text area to edit it in place.")
        else:
            self.status_var.set(f"Page {page_index + 1} has no text blocks.")

    def _collect_blocks(self, page):
        blocks = []
        text_dict_blocks = page.get_text("dict").get("blocks", [])
        for block_index, block in enumerate(page.get_text("blocks")):
            if len(block) < 6:
                continue
            x0, y0, x1, y1, text = block[:5]
            clean_text = str(text).strip()
            if not clean_text:
                continue
            runs = []
            dict_block = text_dict_blocks[block_index] if block_index < len(text_dict_blocks) else {}
            if dict_block.get("type") == 0:
                lines = dict_block.get("lines", [])
                for line_number, line in enumerate(lines):
                    for span in line.get("spans", []):
                        span_text = str(span.get("text", ""))
                        if not span_text:
                            continue
                        flags = int(span.get("flags", 0))
                        runs.append(
                            {
                                "text": span_text,
                                "style": {
                                    "font": normalize_font_name(span.get("font", "helv"), flags),
                                    "size": float(span.get("size", 11)),
                                    "flags": flags,
                                    "color": color_int_to_rgb(span.get("color", 0)),
                                },
                            }
                        )
                    if line_number < len(lines) - 1:
                        runs.append({"text": "\n", "style": runs[-1]["style"] if runs else get_block_style(page, block_index)})
            if "".join(run["text"] for run in runs).strip() != clean_text:
                runs = []
            blocks.append(
                {
                    "page": self.current_page_index + 1,
                    "block_index": block_index,
                    "text": clean_text,
                    "x0": float(x0),
                    "y0": float(y0),
                    "x1": float(x1),
                    "y1": float(y1),
                    "runs": runs,
                }
            )
        return blocks

    def _custom_section_resize_handle(self, section, canvas_x, canvas_y):
        handle_x = section["x1"] * self.preview_scale_x
        handle_y = section["y1"] * self.preview_scale_y
        return abs(canvas_x - handle_x) <= 10 and abs(canvas_y - handle_y) <= 10

    def _start_custom_section_drag(self, section_id, canvas_x, canvas_y, *, mode):
        for section in self.pending_edits.get(self.current_page_index, {}).get("__custom_sections__", []):
            if section.get("id") != section_id:
                continue
            if mode == "resize":
                self.section_resize_state = {
                    "section_id": section_id,
                    "start_canvas_x": canvas_x,
                    "start_canvas_y": canvas_y,
                    "initial_x0": section["x0"],
                    "initial_y0": section["y0"],
                    "initial_x1": section["x1"],
                    "initial_y1": section["y1"],
                }
            else:
                self.section_drag_state = {
                    "section_id": section_id,
                    "start_canvas_x": canvas_x,
                    "start_canvas_y": canvas_y,
                    "initial_x0": section["x0"],
                    "initial_y0": section["y0"],
                    "initial_x1": section["x1"],
                    "initial_y1": section["y1"],
                }
            break

    def _handle_custom_section_drag(self, event):
        if self.section_drag_state is None and self.section_resize_state is None:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        if self.section_resize_state is not None:
            state = self.section_resize_state
            section = next(
                (
                    item
                    for item in self.pending_edits.get(self.current_page_index, {}).get("__custom_sections__", [])
                    if item.get("id") == state["section_id"]
                ),
                None,
            )
            if section is None:
                return
            dx = (canvas_x - state["start_canvas_x"]) / self.preview_scale_x
            dy = (canvas_y - state["start_canvas_y"]) / self.preview_scale_y
            section["x1"] = max(state["initial_x1"] + dx, state["initial_x0"] + 30)
            section["y1"] = max(state["initial_y1"] + dy, state["initial_y0"] + 18)
            self._render_page_preview(self.doc[self.current_page_index])
            return

        state = self.section_drag_state
        section = next(
            (
                item
                for item in self.pending_edits.get(self.current_page_index, {}).get("__custom_sections__", [])
                if item.get("id") == state["section_id"]
            ),
            None,
        )
        if section is None:
            return
        dx = (canvas_x - state["start_canvas_x"]) / self.preview_scale_x
        dy = (canvas_y - state["start_canvas_y"]) / self.preview_scale_y
        width = state["initial_x1"] - state["initial_x0"]
        height = state["initial_y1"] - state["initial_y0"]
        section["x0"] = max(0, state["initial_x0"] + dx)
        section["y0"] = max(0, state["initial_y0"] + dy)
        section["x1"] = section["x0"] + width
        section["y1"] = section["y0"] + height
        self._render_page_preview(self.doc[self.current_page_index])

    def _finish_custom_section_drag(self, event=None):
        if self.section_drag_state is not None:
            state = self.section_drag_state
            if self.selected_custom_section_id == state["section_id"] and self.inline_editor is None:
                self._show_inline_editor_for_custom_section(state["section_id"])
        self.section_drag_state = None
        self.section_resize_state = None

    def _begin_custom_section_drag_from_editor(self, event):
        if self.selected_custom_section_id is None or self.doc is None:
            return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        section = next(
            (
                item
                for item in self.pending_edits.get(self.current_page_index, {}).get("__custom_sections__", [])
                if item.get("id") == self.selected_custom_section_id
            ),
            None,
        )
        if section is None:
            return
        if self._custom_section_resize_handle(section, canvas_x, canvas_y):
            self._start_custom_section_drag(section["id"], canvas_x, canvas_y, mode="resize")
            return
        self._start_custom_section_drag(section["id"], canvas_x, canvas_y, mode="move")

    def on_canvas_clicked(self, event):
        """Open an editor over the text block or custom section clicked in the page preview."""
        if not self.doc:
            return

        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        custom_section = self._custom_section_at_canvas_position(canvas_x, canvas_y)
        if custom_section is not None:
            if self._custom_section_resize_handle(custom_section, canvas_x, canvas_y):
                self.commit_inline_edit()
                self.selected_custom_section_id = custom_section["id"]
                self.selected_block_index = None
                self._start_custom_section_drag(custom_section["id"], canvas_x, canvas_y, mode="resize")
                self._render_page_preview(self.doc[self.current_page_index])
                return

            self.selected_custom_section_id = custom_section["id"]
            self.selected_block_index = None
            self.section_drag_state = {
                "section_id": custom_section["id"],
                "start_canvas_x": canvas_x,
                "start_canvas_y": canvas_y,
                "initial_x0": custom_section["x0"],
                "initial_y0": custom_section["y0"],
                "initial_x1": custom_section["x1"],
                "initial_y1": custom_section["y1"],
            }
            return

        clicked_index = self._block_at_canvas_position(canvas_x, canvas_y)
        if clicked_index is None:
            self.commit_inline_edit()
            self.selected_block_index = None
            self.selected_custom_section_id = None
            self._render_page_preview(self.doc[self.current_page_index])
            return

        if clicked_index == self.selected_block_index and self.inline_editor is not None:
            self.inline_editor.focus_set()
            return

        self.commit_inline_edit()
        self.selected_block_index = clicked_index
        self.selected_custom_section_id = None
        self._render_page_preview(self.doc[self.current_page_index])
        self._show_inline_editor(clicked_index)

    def _block_at_canvas_position(self, x, y):
        for index, block in enumerate(self.page_blocks):
            if (
                block["x0"] * self.preview_scale_x <= x <= block["x1"] * self.preview_scale_x
                and block["y0"] * self.preview_scale_y <= y <= block["y1"] * self.preview_scale_y
            ):
                return index
        return None

    def _show_inline_editor(self, index):
        block = self.page_blocks[index]
        current_page_edits = self.pending_edits.get(self.current_page_index, {})
        original_style = get_block_style(self.doc[self.current_page_index], block["block_index"])
        pending_edit = current_page_edits.get(block["block_index"], block["text"])
        displayed_text, style = edit_value_and_style(
            pending_edit, original_style
        )
        width = max(90, (block["x1"] - block["x0"]) * self.preview_scale_x + 8)
        height = max(30, (block["y1"] - block["y0"]) * self.preview_scale_y + 8)
        # A Text widget's untagged characters use its base style.  Set it
        # before creating the widget so the first keystroke in a newly opened
        # section never flashes the attributes from the last section.
        self._set_attribute_bar_style(style)

        self.inline_editor_frame = tk.Frame(
            self.canvas, bg="#f5f8ff", highlightthickness=1, highlightbackground="#2b78e4"
        )

        self.inline_editor = tk.Text(
            self.inline_editor_frame,
            wrap="word",
            undo=True,
            # Keep ``sel`` while an attribute control receives focus.
            exportselection=False,
            relief="solid",
            borderwidth=1,
            highlightthickness=0,
            font=self._tk_font_tuple(style),
            foreground=rgb_to_hex(style["color"]),
        )
        self.inline_editor.pack(fill="both", expand=True)
        self.inline_editor.insert("1.0", displayed_text)
        self.inline_editor.bind("<Control-Return>", self.commit_inline_edit)
        self.inline_editor.bind("<<Modified>>", self._mark_inline_text_changed)
        self.inline_editor.bind("<ButtonRelease-1>", self._sync_attribute_bar_to_selection)
        self.inline_editor.bind("<KeyRelease>", self._on_editor_key_release)
        self.style_tags = {}
        self.next_style_tag = 0
        self.inline_changed = False
        if isinstance(pending_edit, dict) and pending_edit.get("runs"):
            initial_runs = pending_edit["runs"]
        else:
            initial_runs = block["runs"] or [{"text": displayed_text, "style": style}]
        offset = 0
        for run in initial_runs:
            run_text = str(run.get("text", ""))
            if not run_text:
                continue
            self._apply_style_tag(f"1.0+{offset}c", f"1.0+{offset + len(run_text)}c", run.get("style", style))
            offset += len(run_text)
        if offset != len(displayed_text):
            self._apply_style_tag("1.0", "end-1c", style)
        self._set_attribute_bar_enabled(True)
        self.inline_editor_window = self.canvas.create_window(
            block["x0"] * self.preview_scale_x,
            block["y0"] * self.preview_scale_y,
            anchor="nw",
            width=width,
            height=height,
            window=self.inline_editor_frame,
        )
        self.inline_editor.focus_set()
        self.inline_editor.edit_modified(False)
        self.status_var.set("Select text, then use the floating Text attributes bar. Click elsewhere or press Ctrl+Enter to keep the change.")

    @staticmethod
    def _font_family_label(font_name):
        if font_name.startswith("ti"):
            return "Times"
        if font_name.startswith("co"):
            return "Courier"
        return "Helvetica"

    def _tk_font_tuple(self, style):
        """Return a Tk font matching a PDF style at the current preview scale."""
        if style["font"].startswith("ti"):
            family = "Times"
        elif style["font"].startswith("co"):
            family = "Courier"
        else:
            family = "Helvetica"
        weight = "bold" if style["flags"] & fitz.TEXT_FONT_BOLD else "normal"
        slant = "italic" if style["flags"] & fitz.TEXT_FONT_ITALIC else "roman"
        return (
            family,
            -max(1, round(style["size"] * self.preview_scale_y)),
            weight,
            slant,
        )

    def _selected_pdf_font(self):
        family = self.font_family_var.get()
        bold = self.bold_var.get()
        italic = self.italic_var.get()
        base = {"Helvetica": "helv", "Times": "tiro", "Courier": "cour"}[family]
        variants = {
            "helv": ("helv", "hebo", "heit", "hebi"),
            "tiro": ("tiro", "tibo", "tiit", "tibi"),
            "cour": ("cour", "cobo", "coit", "cobi"),
        }
        if bold and italic:
            return variants[base][3]
        if bold:
            return variants[base][1]
        if italic:
            return variants[base][2]
        return variants[base][0]

    def _current_editor_style(self):
        try:
            size = max(4.0, float(self.font_size_var.get()))
        except (TypeError, ValueError):
            size = 11.0
        flags = 0
        if self.bold_var.get():
            flags |= fitz.TEXT_FONT_BOLD
        if self.italic_var.get():
            flags |= fitz.TEXT_FONT_ITALIC
        return {"font": self._selected_pdf_font(), "size": size, "flags": flags, "color": self._hex_to_rgb(self.text_color)}

    @staticmethod
    def _hex_to_rgb(color):
        color = color.lstrip("#")
        return tuple(int(color[index : index + 2], 16) / 255 for index in (0, 2, 4))

    def _style_tag_name(self, style):
        tag = f"pdf_style_{self.next_style_tag}"
        self.next_style_tag += 1
        self.style_tags[tag] = dict(style)
        return tag

    def _apply_style_tag(self, start, end, style):
        tag = self._style_tag_name(style)
        self.inline_editor.tag_configure(
            tag,
            font=self._tk_font_tuple(style),
            foreground=rgb_to_hex(style["color"]),
        )
        self.inline_editor.tag_add(tag, start, end)
        self.inline_editor.tag_raise(tag)

    def _apply_style_to_selection(self, _event=None):
        if self.inline_editor is None:
            return "break" if _event else None
        try:
            start, end = self.inline_editor.index("sel.first"), self.inline_editor.index("sel.last")
        except tk.TclError:
            self.status_var.set("Select text in the active editor before changing its attributes.")
            return "break" if _event else None
        style = self._current_editor_style()
        self._apply_style_tag(start, end, style)
        self.inline_changed = True
        self.status_var.set("Applied attributes to the selected text only.")
        return "break" if _event else None

    def _set_attribute_bar_style(self, style):
        self.font_family_var.set(self._font_family_label(style["font"]))
        self.font_size_var.set(f"{style['size']:g}")
        self.bold_var.set(bool(style["flags"] & fitz.TEXT_FONT_BOLD))
        self.italic_var.set(bool(style["flags"] & fitz.TEXT_FONT_ITALIC))
        self.text_color = rgb_to_hex(style["color"])
        self.color_button.configure(background=self.text_color, activebackground=self.text_color)

    def _sync_attribute_bar_to_selection(self, _event=None):
        if self.inline_editor is None:
            return
        try:
            tags = self.inline_editor.tag_names("sel.first")
        except tk.TclError:
            return
        for tag in reversed(tags):
            if tag in self.style_tags:
                self._set_attribute_bar_style(self.style_tags[tag])
                return

    def _on_editor_key_release(self, event):
        if event.char and event.char.isprintable() and not event.char.isspace():
            self._inherit_style_for_typed_character()
        self._sync_attribute_bar_to_selection()

    def _style_at_index(self, index):
        for tag in reversed(self.inline_editor.tag_names(index)):
            if tag in self.style_tags:
                return self.style_tags[tag]
        return None

    def _nearest_printable_style(self, index, direction):
        """Find the next styled printable character in the requested direction."""
        while self.inline_editor.compare(index, ">=", "1.0") and self.inline_editor.compare(index, "<=", "end-1c"):
            character = self.inline_editor.get(index)
            if character.isprintable() and not character.isspace():
                return self._style_at_index(index)
            index = self.inline_editor.index(f"{index} {direction}1c")
        return None

    def _inherit_style_for_typed_character(self):
        """Give new text the previous printable style, or the next at block start."""
        if self.inline_editor is None:
            return
        inserted_start = self.inline_editor.index("insert -1c")
        previous = self._nearest_printable_style(f"{inserted_start} -1c", "-")
        following = self._nearest_printable_style("insert", "+")
        inherited_style = previous if previous is not None else following
        if inherited_style is not None:
            self._apply_style_tag(inserted_start, "insert", inherited_style)

    def _mark_inline_text_changed(self, _event=None):
        if self.inline_editor.edit_modified():
            self.inline_changed = True
            self.inline_editor.edit_modified(False)

    def _editor_runs(self, fallback_style):
        """Return contiguous text runs using the highest-priority style tag."""
        text = self.inline_editor.get("1.0", "end-1c")
        runs = []
        for offset, character in enumerate(text):
            index = f"1.0+{offset}c"
            style = fallback_style
            for tag in reversed(self.inline_editor.tag_names(index)):
                if tag in self.style_tags:
                    style = self.style_tags[tag]
                    break
            if runs and runs[-1]["style"] == style:
                runs[-1]["text"] += character
            else:
                runs.append({"text": character, "style": dict(style)})
        return runs

    def _choose_text_color(self):
        selected, hex_color = colorchooser.askcolor(color=self.text_color, parent=self.root, title="Text color")
        if hex_color:
            self.text_color = hex_color
            self.color_button.configure(background=hex_color, activebackground=hex_color)
            self._apply_style_to_selection()

    def commit_inline_edit(self, _event=None):
        if self.inline_editor is None:
            if self.selected_block_index is None and self.selected_custom_section_id is None:
                return "break" if _event else None
            return "break" if _event else None

        if self.selected_custom_section_id is not None:
            page_edits = self.pending_edits.setdefault(self.current_page_index, {})
            sections = page_edits.setdefault("__custom_sections__", [])
            for section in sections:
                if section.get("id") != self.selected_custom_section_id:
                    continue
                updated_text = self.inline_editor.get("1.0", "end-1c")
                style = dict(section.get("style", {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}))
                style.update({
                    "font": self._selected_pdf_font(),
                    "size": max(4.0, float(self.font_size_var.get())),
                    "flags": 0,
                    "color": self._hex_to_rgb(self.text_color),
                })
                if self.bold_var.get():
                    style["flags"] |= fitz.TEXT_FONT_BOLD
                if self.italic_var.get():
                    style["flags"] |= fitz.TEXT_FONT_ITALIC
                section["text"] = updated_text
                section["runs"] = self._editor_runs(style)
                section["style"] = style
                break
            self.selected_custom_section_id = None
        else:
            if self.selected_block_index is None:
                return "break" if _event else None
            block = self.page_blocks[self.selected_block_index]
            updated_text = self.inline_editor.get("1.0", "end-1c")
            page_edits = self.pending_edits.setdefault(self.current_page_index, {})
            original_style = get_block_style(self.doc[self.current_page_index], block["block_index"])
            if updated_text == block["text"] and not self.inline_changed:
                page_edits.pop(block["block_index"], None)
                if not page_edits:
                    self.pending_edits.pop(self.current_page_index, None)
            else:
                page_edits[block["block_index"]] = {
                    "text": updated_text,
                    "runs": self._editor_runs(original_style),
                    **original_style,
                }

        self.canvas.delete(self.inline_editor_window)
        self.inline_editor_frame.destroy()
        self.inline_editor = None
        self.inline_editor_window = None
        self.inline_editor_frame = None
        self._set_attribute_bar_enabled(False)
        self._render_page_preview(self.doc[self.current_page_index])
        self.status_var.set(f"Edit saved for page {self.current_page_index + 1}. Save the PDF when ready.")
        return "break" if _event else None

    def _render_page_preview(self, page):
        if self.doc is None:
            return

        scale = 1.2
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.page_image = ImageTk.PhotoImage(image)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.page_image)
        self.canvas.configure(scrollregion=(0, 0, pix.width, pix.height))
        self.preview_scale_x = pix.width / page.rect.width
        self.preview_scale_y = pix.height / page.rect.height
        self._draw_pending_edit_overlays(page)

        if self.page_blocks and self.selected_block_index is not None:
            block = self.page_blocks[self.selected_block_index]
            x0 = block["x0"] * self.preview_scale_x
            y0 = block["y0"] * self.preview_scale_y
            x1 = block["x1"] * self.preview_scale_x
            y1 = block["y1"] * self.preview_scale_y
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#ff4a4a", width=3)

    def _draw_pending_edit_overlays(self, page):
        """Keep committed edits visible while the user continues editing the page."""
        page_edits = self.pending_edits.get(self.current_page_index, {})
        if not page_edits:
            return

        blocks_by_index = {block["block_index"]: block for block in self.page_blocks}
        for block_index, replacement in page_edits.items():
            if block_index == "__custom_sections__":
                continue
            block = blocks_by_index.get(block_index)
            if block is None:
                continue

            x0 = block["x0"] * self.preview_scale_x
            y0 = block["y0"] * self.preview_scale_y
            x1 = block["x1"] * self.preview_scale_x
            y1 = block["y1"] * self.preview_scale_y
            style = get_block_style(page, block_index)
            self.canvas.create_rectangle(x0 - 2, y0 - 2, x1 + 2, y1 + 2, fill="white", outline="")
            if isinstance(replacement, dict) and replacement.get("runs"):
                self._draw_canvas_runs(x0, y0, replacement["runs"], style)
                continue
            replacement, style = edit_value_and_style(replacement, style)
            font_size = -max(1, round(style["size"] * self.preview_scale_y))
            if style["font"].startswith("ti"):
                family = "Times"
            elif style["font"].startswith("co"):
                family = "Courier"
            else:
                family = "Helvetica"
            weight = "bold" if style["flags"] & fitz.TEXT_FONT_BOLD else "normal"
            slant = "italic" if style["flags"] & fitz.TEXT_FONT_ITALIC else "roman"
            self.canvas.create_text(
                x0,
                y0,
                anchor="nw",
                text=replacement,
                width=max(1, x1 - x0),
                font=(family, font_size, weight, slant),
                fill=rgb_to_hex(style["color"]),
            )

        for section in page_edits.get("__custom_sections__", []):
            x0 = section["x0"] * self.preview_scale_x
            y0 = section["y0"] * self.preview_scale_y
            x1 = section["x1"] * self.preview_scale_x
            y1 = section["y1"] * self.preview_scale_y
            fill = "#d9ebff" if section.get("id") == self.selected_custom_section_id else "#f2f7ff"
            self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#4f8ef7", width=2)
            self.canvas.create_line(x1 - 8, y1 - 8, x1 + 8, y1 + 8, fill="#4f8ef7", width=2)
            self.canvas.create_line(x1 - 8, y1 + 8, x1 + 8, y1 - 8, fill="#4f8ef7", width=2)
            runs = section.get("runs") if isinstance(section.get("runs"), list) else []
            fallback_style = dict(section.get("style", {"font": "helv", "size": 11, "flags": 0, "color": (0, 0, 0)}))
            if runs:
                self._draw_canvas_runs(x0 + 6, y0 + 4, runs, fallback_style)
            else:
                self.canvas.create_text(
                    x0 + 6,
                    y0 + 4,
                    anchor="nw",
                    text=str(section.get("text", "")),
                    width=max(1, x1 - x0 - 12),
                    font=("Helvetica", -max(1, round(fallback_style["size"] * self.preview_scale_y))),
                    fill=rgb_to_hex(fallback_style["color"]),
                )

    def _draw_canvas_runs(self, x, y, runs, fallback_style):
        """Render the saved rich-text runs in the preview without flattening them."""
        cursor_x, cursor_y = x, y
        line_height = 0
        for run in runs:
            style = dict(fallback_style)
            style.update(run.get("style", {}))
            if style["font"].startswith("ti"):
                family = "Times"
            elif style["font"].startswith("co"):
                family = "Courier"
            else:
                family = "Helvetica"
            weight = "bold" if style["flags"] & fitz.TEXT_FONT_BOLD else "normal"
            slant = "italic" if style["flags"] & fitz.TEXT_FONT_ITALIC else "roman"
            font = tkfont.Font(
                family=family,
                size=-max(1, round(style["size"] * self.preview_scale_y)),
                weight=weight,
                slant=slant,
            )
            line_height = max(line_height, font.metrics("linespace"))
            for part in str(run.get("text", "")).splitlines(keepends=True):
                visible_text = part.rstrip("\n")
                if visible_text:
                    self.canvas.create_text(cursor_x, cursor_y, anchor="nw", text=visible_text, font=font, fill=rgb_to_hex(style["color"]))
                    cursor_x += font.measure(visible_text)
                if part.endswith("\n"):
                    cursor_x = x
                    cursor_y += line_height

    def save_edited_pdf(self):
        if self.doc is None:
            self.status_var.set("Open a PDF first.")
            return

        self.commit_inline_edit()
        if not self.pending_edits:
            messagebox.showinfo("No edits made", "Make a text change in the document before saving.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            title="Save edited PDF",
            filetypes=[("PDF files", "*.pdf")],
            initialdir=str(_valid_directory(self.last_save_directory, self.last_load_directory)),
        )
        if not output_path:
            return

        output_path = str(Path(output_path).with_suffix(".pdf"))
        self.last_save_directory = _valid_directory(Path(output_path).parent, self.last_save_directory)
        save_directory_preferences(self.last_load_directory, self.last_save_directory)

        try:
            save_pdf_with_edits(self.doc.name, self.pending_edits, output_path=output_path)
            self.status_var.set(f"Saved edited PDF: {output_path}")
            messagebox.showinfo("Saved", f"The PDF was saved here:\n{output_path}")
        except Exception as exc:
            self.status_var.set("Failed to save PDF: " + str(exc))
            messagebox.showerror("Save failed", str(exc))


def main():
    root = tk.Tk()
    root.report_callback_exception = lambda exc, val, tb: messagebox.showerror(
        "Error", "".join(traceback.format_exception(exc, val, tb)))
    app = PDFTextEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
