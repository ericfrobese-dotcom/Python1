import fitz

from pdf_text_editor import (
    apply_pdf_text_edits,
    extract_pdf_text_blocks,
    get_block_style,
    normalize_font_name,
    normalize_insert_text,
)


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
