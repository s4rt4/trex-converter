# Ebook

Ebook and markup format conversion via **Pandoc** (138-pair format matrix).

## Description

The **Ebook** module wraps `pandoc --from F --to T --output OUT IN` with 9 bidirectional formats plus txt as an output-only target:

- epub, docx, odt, html, markdown (md), rst, latex (tex), org, fb2.
- Output txt via Pandoc's `plain` writer.

Aliases collapsed: md to markdown, latex to tex, html to htm. 138 valid pairs total.

Options panel: title, author, language, publisher, date metadata fields, plus **Generate table of contents** (`--toc`) and **Embed resources** (`--embed-resources` for self-contained HTML).

## How to use

1. Click **Browse** to pick an input file (md, docx, epub, etc.).
2. Pick an **Output format**.
3. (Optional) Fill in metadata fields (title, author, lang) for EPUB/DOCX that has a metadata block.
4. (Optional) Tick **TOC** to auto-generate a table of contents.
5. (Optional) Tick **Embed resources** for self-contained HTML output.
6. Click **Add to Queue**.

## Tips & Trick

- **md to epub** is the most common flow: write your ebook in markdown, generate an EPUB with TOC. Set title and author so reader apps show metadata.
- **html to pdf** isn't supported directly by Pandoc (it needs a LaTeX engine). Use the **Document** module for html to pdf via LibreOffice instead.
- **Embed resources** inlines images and CSS into a single HTML file. Great for archive or email.
- **org to markdown** for migrating from Emacs Org-mode to Obsidian, etc.
- **Pandoc extra args** option (advanced): set a list of flags for advanced Pandoc features (`--mathjax`, `--ascii`, etc.).

## Troubleshooting

**"pandoc exited with code N".** Check the task log for the Pandoc error message. Common: input format doesn't match the extension (such as a `.md` file that's actually RST).

**EPUB output has no cover.** Pandoc doesn't embed a cover image automatically. Use **Pandoc extra args** with `--epub-cover-image=cover.jpg`.

**MOBI conversion not supported.** Pandoc doesn't handle MOBI. Convert to EPUB first, then use external Calibre `ebook-convert` for EPUB to MOBI.
