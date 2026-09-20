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


def test_attribute_bar_drag_stays_visible_and_can_be_reset():
    """The draggable bar must clamp to the window and have a reliable recovery position."""
    app = SimpleNamespace(
        root=_FakeRoot(),
        attribute_bar=_FakeAttributeBar(),
        attribute_drag_offset=None,
    )

    PDFTextEditorApp._start_attribute_bar_drag(app, SimpleNamespace(x_root=270, y_root=130))
    assert app.attribute_drag_offset == (20, 30)

    # A pointer position far outside the bottom-right must be constrained to
    # the last fully visible position: 500 - 200 by 400 - 50.
    PDFTextEditorApp._drag_attribute_bar(app, SimpleNamespace(x_root=1000, y_root=1000))
    assert app.root.updated is True
    assert app.attribute_bar.place_calls[-1] == {"x": 300, "y": 350, "anchor": "nw"}

    PDFTextEditorApp._finish_attribute_bar_drag(app)
    assert app.attribute_drag_offset is None

    PDFTextEditorApp._reset_attribute_bar(app)
    assert app.attribute_bar.place_calls[-1] == {
        "relx": 0.5,
        "rely": 1.0,
        "x": 0,
        "y": -8,
        "anchor": "s",
    }


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
