# PDF Merge

Combine several PDFs into one file via **PyMuPDF** `Document.insert_pdf`.

## Description

The **PDF Merge** module takes multiple PDF inputs and outputs a single PDF with pages from every source concatenated in list order. The `_run_merge` engine iterates `task.inputs` and calls `Document.insert_pdf(source)` per file.

## How to use

1. Click **Add files** or drop several PDFs onto the window.
2. Reorder via **Remove** and re-add (list order is output order).
3. Click **Select Location** to choose the output PDF path.
4. Click **Add to Queue**.

## Tips & Trick

- **Drag-and-drop** several files at once for a quick batch.
- **Order matters**: the first file becomes pages 1 to N, the second continues from there, and so on.
- **Encrypted PDFs** are rejected: decrypt first in **PDF Tools** Security tab.
- Output is saved with `garbage=4 deflate=True` to minimize size.

## Troubleshooting

**"PDF merge requires at least two input PDFs".** Only one file in the list. Add a second file or use **PDF Tools** for single-file operations.

**"Source PDF is encrypted".** One of the inputs is encrypted. Decrypt first via **PDF Tools** Security tab Decrypt action.

**Output is corrupt or pages are missing.** A source PDF has a corrupt incremental-update structure. Repair the source via **PDF Tools** Compress tab Repair action before merging.
