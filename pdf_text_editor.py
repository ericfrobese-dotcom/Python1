# /usr/bin/python3 /home/eric/Python1/pdf_text_editor.py
# eric@eric-OptiPlex-980:~/Python1$ /usr/bin/python3 /home/eric/Python1/pdf_text_editor.py
# warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
#
from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk
import pymupdf as fitz


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
        if any(token in lowered for token in ("boldoblique", "oblique", "italic")):
            return "hebi"
        return "helv"

    if any(token in lowered for token in ("times", "tiro")):
        if flags & fitz.TEXT_FONT_BOLD and flags & fitz.TEXT_FONT_ITALIC:
            return "tibi"
        if flags & fitz.TEXT_FONT_BOLD:
            return "tibo"
        if any(token in lowered for token in ("bolditalic", "italic", "oblique")):
            return "tibi"
        return "tiro"

    if any(token in lowered for token in ("courier", "cour")):
        if flags & fitz.TEXT_FONT_BOLD and flags & fitz.TEXT_FONT_ITALIC:
            return "cobi"
        if flags & fitz.TEXT_FONT_BOLD:
            return "cobo"
        if any(token in lowered for token in ("bolditalic", "italic", "oblique")):
            return "cobi"
        return "cour"

    if any(token in lowered for token in ("symbol", "zapf")):
        return "symb"

    if "hebo" in candidate_names or "bold" in lowered:
        return "hebo"

    return "helv"


def get_block_style(page, block_index):
    text_dict = page.get_text("dict")
    blocks = text_dict.get("blocks", [])
    if block_index >= len(blocks):
        return {"font": "helv", "size": 11, "flags": 0}

    block = blocks[block_index]
    if block.get("type") != 0:
        return {"font": "helv", "size": 11, "flags": 0}

    for line in block.get("lines", []):
        for span in line.get("spans", []):
            flags = int(span.get("flags", 0))
            font = normalize_font_name(span.get("font", "helv"), flags=flags)
            return {
                "font": font,
                "size": float(span.get("size", 11)),
                "flags": flags,
            }

    return {"font": "helv", "size": 11, "flags": 0}


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

        blocks = source_page.get_text("blocks")
        for block_index, new_text in page_edits.items():
            if block_index >= len(blocks):
                continue

            x0, y0, x1, y1 = blocks[block_index][:4]
            style = get_block_style(source_page, block_index)
            rect = fitz.Rect(float(x0) - 2, float(y0) - 2, float(x1) + 2, float(y1) + 2)
            target_page.draw_rect(rect, fill=(1, 1, 1), color=(1, 1, 1), overlay=True)
            target_page.insert_text(
                (float(x0), float(y0)),
                normalize_insert_text(new_text),
                fontsize=float(style["size"]),
                fontname=style["font"],
                color=(0, 0, 0),
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

        self._build_ui()

    def _build_ui(self):
        toolbar = ttk.Frame(self.root, padding=(10, 10, 10, 6))
        toolbar.pack(fill="x")

        ttk.Button(toolbar, text="Open PDF", command=self.open_pdf).pack(side="left")
        ttk.Button(toolbar, text="Apply Edit", command=self.apply_current_edit).pack(side="left", padx=(8, 0))
        ttk.Button(toolbar, text="Save Edited PDF", command=self.save_edited_pdf).pack(side="left", padx=(8, 0))

        self.status_var = tk.StringVar(value="Open a PDF to begin.")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side="left", padx=(18, 0))

        main = ttk.PanedWindow(self.root, orient="horizontal")
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        left = ttk.Frame(main, padding=6)
        main.add(left, weight=1)

        page_controls = ttk.Frame(left)
        page_controls.pack(fill="x")
        ttk.Label(page_controls, text="Page:").pack(side="left")
        self.page_selector = ttk.Combobox(page_controls, state="readonly", width=12)
        self.page_selector.pack(side="left", padx=(6, 0))
        self.page_selector.bind("<<ComboboxSelected>>", self.on_page_selected)

        self.canvas = tk.Canvas(left, width=500, height=680, bg="#e6e6e6", highlightthickness=1, highlightbackground="#7a7a7a")
        self.canvas.pack(fill="both", expand=True, pady=(8, 0))

        right = ttk.Frame(main, padding=6)
        main.add(right, weight=1)

        ttk.Label(right, text="Text blocks on this page").pack(anchor="w")
        self.block_listbox = tk.Listbox(right, exportselection=False)
        self.block_listbox.pack(fill="both", expand=True)
        self.block_listbox.bind("<<ListboxSelect>>", self.on_block_selected)

        ttk.Label(right, text="Edit selected text").pack(anchor="w", pady=(12, 4))
        self.edit_text = tk.Text(right, height=12, wrap="word")
        self.edit_text.pack(fill="both", expand=True)

    def open_pdf(self):
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_path:
            return

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

        self.current_page_index = page_index
        page = self.doc[page_index]
        self.page_blocks = self._collect_blocks(page)
        self.selected_block_index = 0 if self.page_blocks else None

        self.block_listbox.delete(0, tk.END)
        for block in self.page_blocks:
            preview = block["text"][:60]
            self.block_listbox.insert(tk.END, f"{block['page']}.{block['block_index'] + 1}: {preview}")

        self._render_page_preview(page)
        if self.page_blocks:
            self._populate_editor_from_selection(0)
        else:
            self.edit_text.delete("1.0", tk.END)
            self.edit_text.insert("1.0", "This page has no selectable text.")
            self.status_var.set(f"Page {page_index + 1} has no text blocks.")

    def _collect_blocks(self, page):
        blocks = []
        for block_index, block in enumerate(page.get_text("blocks")):
            if len(block) < 6:
                continue
            x0, y0, x1, y1, text = block[:5]
            clean_text = str(text).strip()
            if not clean_text:
                continue
            blocks.append(
                {
                    "page": self.current_page_index + 1,
                    "block_index": block_index,
                    "text": clean_text,
                    "x0": float(x0),
                    "y0": float(y0),
                    "x1": float(x1),
                    "y1": float(y1),
                }
            )
        return blocks

    def on_block_selected(self, _event):
        if self.block_listbox.curselection():
            index = self.block_listbox.curselection()[0]
            self._populate_editor_from_selection(index)

    def _populate_editor_from_selection(self, index):
        self.selected_block_index = index
        if not self.page_blocks or index >= len(self.page_blocks):
            self.edit_text.delete("1.0", tk.END)
            return

        block = self.page_blocks[index]
        current_page_edits = self.pending_edits.get(self.current_page_index, {})
        displayed_text = current_page_edits.get(block["block_index"], block["text"])

        self.edit_text.delete("1.0", tk.END)
        self.edit_text.insert("1.0", displayed_text)
        self._render_page_preview(self.doc[self.current_page_index])

    def _render_page_preview(self, page):
        if self.doc is None:
            return

        scale = 1.2
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        self.page_image = ImageTk.PhotoImage(image)

        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.page_image)

        if self.page_blocks and self.selected_block_index is not None:
            block = self.page_blocks[self.selected_block_index]
            scale_x = pix.width / page.rect.width
            scale_y = pix.height / page.rect.height
            x0 = block["x0"] * scale_x
            y0 = block["y0"] * scale_y
            x1 = block["x1"] * scale_x
            y1 = block["y1"] * scale_y
            self.canvas.create_rectangle(x0, y0, x1, y1, outline="#ff4a4a", width=3)

    def apply_current_edit(self):
        if not self.page_blocks or self.selected_block_index is None:
            self.status_var.set("Select a text block before applying an edit.")
            return

        updated_text = self.edit_text.get("1.0", "end-1c").strip()
        if not updated_text:
            self.status_var.set("Text cannot be empty.")
            return

        block = self.page_blocks[self.selected_block_index]
        page_key = self.current_page_index
        self.pending_edits.setdefault(page_key, {})[block["block_index"]] = updated_text
        self.status_var.set(f"Queued edit for page {page_key + 1}.")

    def save_edited_pdf(self):
        if self.doc is None:
            self.status_var.set("Open a PDF first.")
            return

        if not self.pending_edits:
            messagebox.showinfo("No edits queued", "Apply a text change before saving.")
            return

        output_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            title="Save edited PDF",
            filetypes=[("PDF files", "*.pdf")],
        )
        if not output_path:
            return

        output_path = str(Path(output_path).with_suffix(".pdf"))

        try:
            save_pdf_with_edits(self.doc.name, self.pending_edits, output_path=output_path)
            self.status_var.set(f"Saved edited PDF: {output_path}")
            messagebox.showinfo("Saved", f"The PDF was saved here:\n{output_path}")
        except Exception as exc:
            self.status_var.set("Failed to save PDF: " + str(exc))
            messagebox.showerror("Save failed", str(exc))


def main():
    root = tk.Tk()
    app = PDFTextEditorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
