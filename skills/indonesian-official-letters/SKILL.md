---
name: indonesian-official-letters
description: Draft Indonesian official letters (surat dinas) as PDFs.
version: 0.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [indonesia, surat, letter, reportlab, pdf, asn]
    related_skills: [pdf, google-workspace]
---

# Indonesian Official Letters (Surat Dinas)

Draft formal Indonesian institutional letters — surat permohonan izin, surat
keterangan sakit, surat keterangan domisili, and similar ASN/sekolah documents —
as a multi-page PDF with a right-half signature block and an attachment page
when the user supplies evidence (clinic record, receipt, screenshot).

The `pdf` skill's `pdf_create.py` JSON spec cannot express a key-value identity
block, dual-row signature table, or a hand-laid image attachment — write a small
`reportlab.platypus` script instead. Start from `templates/surat_template.py`
(copy, then edit only the CONFIG block).

## When to Use

- User asks for any Indonesian official letter for themselves or an institution
  (izin sakit, izin tidak masuk kerja, keterangan sehat, keterangan domisili,
  permohonan cuti).
- The letter needs a NIP/jabatan identity block, addressee block, or attachment
  page with evidence.

**Don't use for:** letters issued *by* a clinic or doctor (those are theirs to
issue), English/international letter formats, or plain prose documents — use
the `pdf` skill directly.

## Prerequisites

- Python with `reportlab` and `PIL` (both present in the Hermes venv).
- The `pdf` skill's scripts for verification (`pdf_read.py`,
  `pdf_page_image.py`).
- Google OAuth already authenticated for Drive uploads (see `google-workspace`).

## Procedure

1. **Classify the letter type first** — it decides the addressee, opening verbs,
   and who signs:
   - *Surat permohonan izin* (you ask for leave): `Kepada Yth.` + recipient
     title, opens `Dengan hormat` / `Saya yang bertanda tangan di bawah ini:`,
     states `mengajukan permohonan izin ...`, applicant signs. This is the
     correct type for an employee's own sick-leave slip.
   - *Surat keterangan* (someone certifies a fact): third-person,
     `Dengan ini menerangkan bahwa benar ...`, issued/signed by the authority.
   Done when: the letter type is chosen and stated to the user if ambiguous.
2. **Gather facts, never invent them.** Collect name, NIP, jabatan, instansi,
   and the exact recipient title from the user. Resolve the real date with
   `terminal('date "+%A, %d %B %Y"')` — the conversation start date is often
   stale. Copy NIP character-for-character. Leave unknown institution data
   (alamat, telp, nomor surat, nama+NIP atasan) as visible blanks. If the user
   supplied a medical-record photo, its contents are the source of truth for
   diagnosis/clinic/date. Done when: every literal value in the script is
   user-supplied or computed from the system clock.
3. **Build with the template** (`templates/surat_template.py`): centered bold
   title → `Kepada Yth.` block → penutup → key-value `Table`s for
   identity/detail (`[label, ":", value]`, `2.6*cm/0.5*cm/12*cm`,
   `VALIGN='TOP'`) → closing paragraphs → right-half signature `Table`
   (`8.25*cm` columns) → `PageBreak()` → attachment page. Run via `terminal`.
   Done when: the script exits 0 and prints the output path.
4. **Fit tall attachments.** Size images with both constraints:
   `ratio = min(frame_w/iw, frame_h/ih)`, where `frame_h` leaves room below for
   the `LAMPIRAN` heading (≈22 cm, not the full page). Done when: no
   `LayoutError`.
5. **Verify visually.** `pdf_read.py out.pdf --meta` for page count, then
   `pdf_page_image.py --pages 1-N --dpi 110` and `vision_analyze` on every
   rendered page, asking about overlaps, truncation, placeholder text, and
   signature-block alignment/gap. Done when: every page inspected and clean.
6. **Deliver as a real attachment.** Per standing user preference, send
   documents as `MEDIA:/absolute/path/file.pdf` — never as a `file:///` link or
   bare path (Telegram cannot download those). State which fields remain blank
   for the user to fill (nomor surat, kop address, approver name/NIP).
7. **If Drive upload is requested**, apply the Drive delivery rule below.

## Standing Style Rules (every letter unless the user says otherwise)

- **No kop surat by default.** Default output: title → Kepada Yth. → body →
  right-half signature. Letterhead is opt-in, only when explicitly requested.
- **No `Mengetahui`/`Disetujui` approval block by default.** Two-column
  signature (approver left) is opt-in only; if the user asked for it removed,
  re-adding it is a regression.
- **Never invent administrative details**: school address, phone, email, nomor
  surat, or the approver's name/NIP — omit them and tell the user which fields
  to fill.
- **Copy the NIP exactly as provided**; never regroup digits into
  `XX.XXXX.XX.XXXX.XXXX.XX` (position/gender digits you cannot verify).
- **Use the exact recipient title the user gives** (e.g. `Kepala Tata Usaha`,
  not `Kepala Sekolah`) — their words override convention.
- **Keep clinical fields terse**: the raw diagnosis term only
  (`Acute nasopharyngitis`), no parenthetical translations or lay glosses —
  users strip explanatory text from formal documents.
- **Leave 5–6 blank lines between `Hormat saya,` and the bold name** so a wet
  signature fits; verify the gap visually on the rendered page.
- Formal Indonesian register throughout (`Dengan hormat`,
  `Demikian permohonan ini saya ajukan...`), Times font.

## Drive delivery rule (when upload is requested)

- **Trace a destination folder's parent chain** with `drive get FOLDER_ID`
  (repeat on `parents[0]` until reaching `My Drive`) before using it: month-
  and category-named folders can sit under an unrelated departmental tree
  (e.g. an inventory drive), and dropping a personal letter there is wrong.
- Prefer the folder that already holds sibling documents of the same class.
- **Verify the upload** by searching the chosen parent ID
  (`drive search --raw-query "'<PARENT>' in parents and name contains '<n>'"`)
  and report the `webViewLink`.

## Pitfalls

- **Mixing up permohonan vs keterangan** produces a letter signed by the wrong
  party — an employee requesting sick leave submits a *permohonan izin*; only a
  doctor/clinic issues a *keterangan sakit*.
- **Tall phone screenshots blow the frame**: `Image` keeps its aspect ratio, so
  a 576x1280 screenshot fits the width but overflows the page height, raising
  `LayoutError: Flowable <Image ...> too large on page` — and only at
  `doc.build()`, after everything else is written. Always min() both dimensions
  (step 4), reducing `frame_h` for heading lines already consumed.
- **Page-1 overflow spills before the lampiran `PageBreak`**, producing a stray
  third page with a half-empty middle — assert the page count and trim spacing
  rather than accepting it.
- **Fabricated letterhead details** (address, phone, email, nomor surat, approver
  NIP) make a document unusable and falsely credible — leave them blank.
- **Assuming the date** from the session header yields wrong letter dates; query
  the clock, and match izin duration to the evidence (a visit *yesterday* usually
  means a *today*-only izin).
- **Signature blocks are the misalignment hotspot** — manual `<br/>` spacing
  inside `Table` cells; inspect them at every verification pass. Table column
  widths must sum to the frame width or the block shifts off-center.
- **Placeholders are only visible in the raster** — inspect rendered pages, not
  just the build exit code or extracted text.

## Verification

- `pdf_read.py out.pdf --meta` → expected `page_count`, non-empty metadata title.
- Rendered page images reviewed with `vision_analyze`: no overlap, no clipped
  text, signature gap adequate, no stray placeholder text.
- The reply lists every blank field the user must complete before signing/sending.
