import fitz
from types import SimpleNamespace

from pdf_text_editor import (
    PDFTextEditorApp,
    apply_pdf_text_edits,
    extract_pdf_text_blocks,
    get_block_style,
    normalize_font_name,
    normalize_insert_text,
)


class _FakeRoot:
    def __init__(self, *, root_x=100, root_y=50, width=500, height=400):
        self.root_x = root_x
        self.root_y = root_y
        self.width = width
        self.height = height
        self.updated = False

    def update_idletasks(self):
        self.updated = True

    def winfo_rootx(self):
        return self.root_x

    def winfo_rooty(self):
        return self.root_y

    def winfo_width(self):
        return self.width

    def winfo_height(self):
        return self.height


class _FakeAttributeBar:
    def __init__(self, *, root_x=250, root_y=100, width=200, height=50):
        self.root_x = root_x
        self.root_y = root_y
        self.width = width
        self.height = height
        self.place_calls = []
        self.lift_count = 0
        self.grabbed = False

    def winfo_rootx(self):
        return self.root_x

    def winfo_rooty(self):
        return self.root_y

    def winfo_width(self):
        return self.width

    def winfo_height(self):
        return self.height

    def place(self, **kwargs):
        self.place_calls.append(kwargs)

    def lift(self):
        self.lift_count += 1

    def grab_set(self):
        self.grabbed = True

    def grab_release(self):
        self.grabbed = False


def test_attribute_bar_drag_stays_visible_and_can_be_reset():
    """The draggable bar must clamp to the window and have a reliable recovery position."""
    app = SimpleNamespace(
        root=_FakeRoot(),
        attribute_bar=_FakeAttributeBar(),
        attribute_drag_offset=None,
    )

    event = SimpleNamespace(x_root=270, y_root=130, widget=app.attribute_bar)
    PDFTextEditorApp._start_attribute_bar_drag(app, event)
    assert app.attribute_drag_offset == (20, 30)
    assert app.attribute_bar.grabbed is True

    # A pointer position far outside the bottom-right must be constrained to
    # the last fully visible position: 500 - 200 by 400 - 50.
    PDFTextEditorApp._drag_attribute_bar(app, SimpleNamespace(x_root=1000, y_root=1000))
    assert app.root.updated is True
    assert app.attribute_bar.place_calls[-1] == {"x": 300, "y": 350, "anchor": "nw"}

    PDFTextEditorApp._finish_attribute_bar_drag(app, event)
    assert app.attribute_drag_offset is None
    assert app.attribute_bar.grabbed is False

    PDFTextEditorApp._reset_attribute_bar(app)
    assert app.attribute_bar.place_calls[-1] == {
        "relx": 0.5,
        "rely": 1.0,
        "x": 0,
        "y": -8,
        "anchor": "s",
    }
    assert app.attribute_bar.lift_count >= 3


def test_normalize_font_name_handles_unknown_fonts():
    assert normalize_font_name("Avenir Next") == "helv"
    assert normalize_font_name("Times New Roman") == "tiro"
    assert normalize_font_name("Courier New") == "cour"
    assert normalize_font_name("") == "helv"


def test_style_and_ligature_handling_for_bold_text():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Conﬁrmation", fontsize=12, fontname="hebo")
    style = get_block_style(doc[0], 0)
    assert style["font"] in {"hebo", "helv"}
    assert normalize_insert_text("Conﬁrmation") == "Confirmation"
    doc.close()


def test_extract_pdf_text_blocks_handles_basic_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "hello world from the pdf editor")
    doc.save(pdf_path)
    doc.close()

    blocks = extract_pdf_text_blocks(pdf_path)
    assert isinstance(blocks, list)
    assert any("hello" in block["text"].lower() for block in blocks)


def test_get_block_style_returns_font_metadata(tmp_path):
    pdf_path = tmp_path / "styled.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "styled text", fontsize=22, fontname="helv")
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    style = get_block_style(doc[0], 0)
    assert style is not None
    assert style["size"] >= 15
    doc.close()


def test_apply_pdf_text_edits_replaces_selected_block(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "edited.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "hello world from the pdf editor")
    doc.save(src)
    doc.close()

    edits = {0: {0: "updated text"}}
    updated = apply_pdf_text_edits(src, edits)
    updated.save(out)

    result = fitz.open(out)
    text = " ".join(page.get_text("text") for page in result)
    assert "updated text" in text.lower()
    result.close()


def test_pdf_text_editor_add_and_resize_custom_sections():
    doc = fitz.open()
    doc.new_page(width=500, height=400)
    app = PDFTextEditorApp.__new__(PDFTextEditorApp)
    app.doc = doc
    app.current_page_index = 0
    app.pending_edits = {0: {}}
    app.selected_custom_section_id = None
    app.custom_section_counter = 0
    app.preview_scale_x = 1.0
    app.preview_scale_y = 1.0
    app._render_page_preview = lambda page: None

    PDFTextEditorApp._add_new_text_section(app, x=100, y=120, width=160, height=40)
    sections = app.pending_edits[0]["__custom_sections__"]
    assert len(sections) == 1
    assert sections[0]["x0"] == 100
    assert sections[0]["y0"] == 120

    PDFTextEditorApp._resize_text_section(app, section_id=sections[0]["id"], x=100, y=120, width=220, height=70)
    section = app.pending_edits[0]["__custom_sections__"][0]
    assert section["x1"] == 320
    assert section["y1"] == 190
    doc.close()


def test_apply_pdf_text_edits_supports_custom_sections(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "edited.pdf"
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    doc.save(src)
    doc.close()

    edits = {
        0: {
            "__custom_sections__": [
                {
                    "id": "custom-1",
                    "x0": 20,
                    "y0": 20,
                    "x1": 120,
                    "y1": 80,
                    "text": "custom note",
                    "style": {"font": "helv", "size": 12, "flags": 0, "color": (0, 0, 0)},
                }
            ]
        }
    }
    updated = apply_pdf_text_edits(src, edits)
    updated.save(out)

    result = fitz.open(out)
    page_text = result[0].get_text("text")
    assert "custom note" in page_text.lower()
    result.close()


def test_apply_pdf_text_edits_preserves_custom_section_run_styles(tmp_path):
    src = tmp_path / "source.pdf"
    out = tmp_path / "edited.pdf"
    doc = fitz.open()
    doc.new_page(width=300, height=200)
    doc.save(src)
    doc.close()

    edits = {
        0: {
            "__custom_sections__": [
                {
                    "id": "custom-styled",
                    "x0": 20,
                    "y0": 20,
                    "x1": 220,
                    "y1": 120,
                    "text": "Red bold text and blue italic text",
                    "runs": [
                        {"text": "Red bold ", "style": {"font": "helv", "size": 12, "flags": fitz.TEXT_FONT_BOLD, "color": (1, 0, 0)}},
                        {"text": "blue italic text", "style": {"font": "tiro", "size": 12, "flags": fitz.TEXT_FONT_ITALIC, "color": (0, 0, 1)}},
                    ],
                    "style": {"font": "helv", "size": 12, "flags": 0, "color": (0, 0, 0)},
                }
            ]
        }
    }

    updated = apply_pdf_text_edits(src, edits)
    updated.save(out)

    result = fitz.open(out)
    blocks = result[0].get_text("dict").get("blocks", [])
    span_colors = []
    span_flags = []
    for block in blocks:
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                span_colors.append(int(span.get("color", 0)))
                span_flags.append(int(span.get("flags", 0)))

    assert len(set(span_colors)) > 1
    assert any(flag & fitz.TEXT_FONT_BOLD for flag in span_flags)
    assert any(flag & fitz.TEXT_FONT_ITALIC for flag in span_flags)
    result.close()
