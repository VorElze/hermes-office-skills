---
name: markdown-pdf-pipeline
description: "Use when rendering a tutorial or report PDF from Markdown."
version: 1.0.0
author: amanda
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [pdf, pandoc, documentation, xelatex, tutorial]
---

# Markdown → Polished PDF Pipeline

When the owner asks for a PDF document (tutorial, installation guide, report),
render a prose-quality PDF from Markdown via pandoc+xelatex and QA it visually.
Library-level PDF operations (forms, merge, OCR) belong to the `pdf` skill;
this skill is the render-and-QA loop for multi-page prose documents.

## When to Use

Use when the user asks for a tutorial, installation guide, report, or any
multi-page prose deliverable as a PDF — e.g. "buatkan tutorial PDF" or
"dokumentasi dalam PDF". Not for form fill/merge/OCR/encrypt (those go to the
`pdf` skill) and not for spec-driven one-shot stubs unless layout polish is
requested.

## Procedure

1. **Read the source of truth first.** Pull content from the project's real
   docs (README, spec, brief) — never write an installation guide from memory.
   `read_file` the whole README before drafting.
2. **Draft Markdown** into the scratch dir. Structure: title block → numbered
   sections → tables for config/mappings → fenced blocks for commands.
   Keep commands short enough to fit an A4 line (see Pitfalls).
3. **Render** (tools present on this host: pandoc, xelatex, lmodern,
   poppler-utils):
   ```bash
   pandoc doc.md -o out.pdf --pdf-engine=xelatex \
     -V geometry:a4paper,margin=2.2cm \
     -V mainfont='DejaVu Sans' -V monofont='DejaVu Sans Mono' \
     -V fontsize=11pt -V colorlinks=true -V linkcolor=NavyBlue \
     --toc --toc-depth=2 -V toc-title='Daftar Isi' \
     -V classoption=oneside \
     -V header-includes='\usepackage{fancyhdr}\pagestyle{fancy}\fancyhead[L]{<judul singkat>}\fancyhead[R]{\thepage}\fancyfoot{}' \
     --metadata title='...' --metadata author='...'
   ```
4. **Verify structurally:** `pdfinfo out.pdf` (Pages > 0, A4) and
   `pdftotext out.pdf - | head` (content present, no mojibake).
5. **Verify VISUALLY — mandatory:** `pdftoppm -png -r 90 -f 1 -l 1 out.pdf p1`
   (plus 1-2 interior pages incl. any wide table/code page), then
   `vision_analyze` each PNG asking specifically about: text running off the
   right margin, duplicate TOCs, overlapping tables, garbled glyphs, and raw
   Markdown markers (e.g. `**bold**`) visibly leaking into the PDF. Asterisks
   inside expressions such as `COUNT(*)` can break Markdown bold parsing; rewrite
   as plain wording or code spans. Fix source, re-render, re-check — iterate
   until clean. Text extraction cannot show overflow, so step 4 does not
   substitute for this.
6. **Deliver** the finished document as `MEDIA:<abs path>` (never a file:/// link)
   when the user asks for an attachment; include a concise conclusion and material
   caveats in chat, but avoid duplicating the entire report in the message. Only
   report that the PDF was created after checking file existence, page count,
   A4 size, extracted text, and visual legibility.

## Pitfalls

- **`--toc-title` does not exist in this pandoc** — it aborts with exit 6
  ("Unknown option"). Title the TOC with the variable form `-V toc-title='...'`
  instead; same meaning, valid flag.
- **`--toc` generates its own TOC.** If the Markdown also has a handwritten
  "Daftar Isi" section, the PDF ships TWO tables of contents — delete the
  manual one from the source before rendering.
- **xelatex does not wrap long code lines.** URLs/commands in fenced blocks
  silently run off the right page edge (visible only in the rendered PNG).
  Wrap them in source with `\` line continuation or split the string.
- **Build LaTeX-heavy commands as raw strings/concatenation, never Python
  f-strings** — `$`, `\u`, and backslash sequences get mangled before reaching
  the shell and corrupt flags invisibly.
- **First run may fail on missing `lmodern.sty`** — `apt-get install -y
  lmodern` once.
- **Read the source README's honest caveats into the guide.** If the package's
  own docs warn that a feature is metadata-only or untested, the tutorial must
  repeat the caveat — do not let a clean layout oversell the product.
