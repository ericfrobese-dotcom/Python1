# PDF Text Editor

PDF Text Editor lets you edit exiting text areas (or add a new text area) and add styled text sections to a PDF, then save an edited copy.

## Pyinstaller use note: 
pyinstaller --onefile --noconsole --hidden-import PIL._tkinter_finder pdf_text_editor.py

## Requirements and launch

The application requires Python, Tkinter, Pillow, and PyMuPDF. Install the Python packages if needed:

```bash
python3 -m pip install pillow pymupdf
```

Then run it from the project folder:

```bash
python3 pdf_text_editor.py
```

## Edit text

1. Select **Open PDF** and choose a PDF.
2. Select a page from the **Page** list.
3. Click a text area in the page preview. Edit the text in the box that appears. Click elsewhere or press **Ctrl+Enter** to keep the change.
4. Use the text attributes bar to adjust font family, size, bold, italic, or color for the selected text. The bar can be moved by dragging its grip; select **Reset attributes bar** if it is out of the way.
5. Repeat on other pages or text areas.

The editor targets text blocks detected in the PDF. It does not provide general-purpose editing of every PDF object or guarantee that replacement text will fit exactly as the original did.

## Add a text section

1. Select **Add Text Section**.
2. Type into the new text box on the page.
3. Drag the section to move it, or drag its lower-right resize handle to change its size.
4. Set the font and style using the attributes bar, then click elsewhere or press **Ctrl+Enter** to keep the edit.

## Save an edited copy

Select **Save Edited PDF**, choose an output location and filename, and save. The source PDF is not overwritten unless you explicitly choose the same output path and confirm any file-overwrite prompt from your operating system.

**Important:** Saved pages are rendered as page images, with edited text drawn over them. Original page text may no longer be selectable or searchable in the saved copy. Keep the original PDF, especially when accessibility, text extraction, or archival fidelity matters.

## Troubleshooting

- **A page or text area is difficult to reach:** Use the page selector and the preview's horizontal and vertical scrollbars.
- **The attribute controls are missing:** Select **Reset attributes bar**.
- **The PDF did not save:** Check that the destination folder is writable and that the output file is not open or locked by another program.
- **Package import errors:** Install Pillow and PyMuPDF into the same Python environment used to run the application.
