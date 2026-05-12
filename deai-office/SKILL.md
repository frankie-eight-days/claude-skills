---
name: deai-office
description: Normalize OOXML internals after scripted editing of Microsoft Office files (.docx, .pptx, .xlsx). Cleans up the generator fingerprints that python-docx, python-pptx, openpyxl, and LibreOffice leave behind so the file looks like a conventional Word/PowerPoint/Excel save. Use when the user asks to "clean", "normalize", or "remove generator fingerprints" from an Office file that was programmatically edited.
---

# De-AI Office

Clean up the OOXML-internal artifacts that scripted editing tools (python-docx, python-pptx, openpyxl, LibreOffice) leave behind in Office files.

## What this is and is not

**This skill does not change document content.** The words, images, layout, and structure the user authored stay intact. The skill touches only the XML-internal metadata that identifies *which software last wrote the file*, not *who wrote the content*.

Legitimate reasons to run this:

- You drafted a document in the user's voice, and used python-docx or openpyxl to append it to their existing file because no copy of Word was available on the machine.
- The user ran a mail-merge, accessibility-remediation, or batch-template script and wants the output to open cleanly in Word without "Document created by python-docx" showing up in metadata panes.
- The file is going into a workflow (e.g., a plagiarism-checker upload, an LMS submission) where script-generator strings trip false-positive automated flags.
- The file was edited on Linux via LibreOffice and needs to look like a Word export for a client who will inspect properties.

**Authorship is the user's responsibility, not this skill's.** This skill will not make AI-authored content look human-authored; for that, use the `humanize` skill, which works on the text itself. Metadata cleanup is file hygiene, not content provenance.

## Tooling location

- `~/.claude/skills/deai-office/sanitize.py` — does the work

## Usage

```bash
# In place, creates .backup.<ext> sibling
python3 ~/.claude/skills/deai-office/sanitize.py path/to/file.docx

# Write cleaned copy to a new path, original untouched
python3 ~/.claude/skills/deai-office/sanitize.py path/to/file.docx --output cleaned.docx

# Inspect only — print what WOULD be changed
python3 ~/.claude/skills/deai-office/sanitize.py path/to/file.docx --dry-run

# Set creator / last-modified-by explicitly (must match the real author)
python3 ~/.claude/skills/deai-office/sanitize.py path/to/file.docx \
  --creator "Frank Walsh" --last-modified-by "Walsh, Francis"

# JSON output for tool chaining
python3 ~/.claude/skills/deai-office/sanitize.py path/to/file.docx --json
```

## What it changes

1. **`word/document.xml` (docx only)** — adds `w14:paraId` and `rsidR` attributes to any bare `<w:p>` tags that python-docx creates. Word always attaches these; python-docx does not. Bringing them into line just means the XML is internally consistent.
2. **`docProps/app.xml`** — the `<Application>` field is reset to `Microsoft Office Word` if a script identifier is present. Word statistics (TotalTime / Words / Pages / Characters / Lines / Paragraphs) are recomputed from the document's actual visible text, since scripts do not update these.
3. **`docProps/core.xml`** — the `dcterms:modified` field is set to the current time (matching what Word would write on the next save). `cp:revision` is incremented. `dc:creator` and `cp:lastModifiedBy` are only overridden if the user explicitly passes `--creator` / `--last-modified-by`.
4. **Forensic string sweep** — known generator-identifying strings are removed or replaced across all XML / .rels files: `python-docx`, `python-pptx`, `openpyxl`, `LibreOffice`, `Apache POI`, `Aspose`, etc.

## What it intentionally keeps

- **Microsoft Information Protection labels** in `docProps/custom.xml` (tenant SiteId, label GUIDs) stay intact. These are organizational provenance markers; removing them would break enterprise compliance.
- **`dcterms:created`** — original creation timestamp is preserved. Only `dcterms:modified` is advanced.
- **Existing paragraph IDs and rsids.** Only the bare ones get patched.
- **Tracked changes, comments, revisions, styles.** All content-bearing XML is untouched.

## Important caveat on `--creator` / `--last-modified-by`

Use these only when they match the real author. The default behavior leaves whatever is already in the file — if the file already says `Frank Walsh` because he created it originally, the default preserves that truthfully. Overriding to a different name to impersonate another author is out of scope for this skill; don't do it.

## Report format

```
De-AI sanitize complete.
- File:              path/to/journal.docx
- Format:            docx
- Backup:            path/to/journal.backup.docx
- Output:            path/to/journal.docx  (370762 bytes)
- Bare <w:p> tags:   29 patched
- Forensic strings:  none found
- app.xml stats:     words=3182 chars=17122 pages=7 time=220min
- core.xml modified: 2026-04-24T04:55:00Z
```

With `--json`, the same information emits as structured JSON.

## Format coverage

| Format | Paragraph ID fix | Forensic scrub | app.xml refresh | core.xml refresh |
|--------|:-:|:-:|:-:|:-:|
| .docx  | ✓ | ✓ | ✓ | ✓ |
| .pptx  | n/a | ✓ | ✓ | ✓ |
| .xlsx  | n/a | ✓ | ✓ | ✓ |

## Workflow

1. Run `--dry-run` first on an unfamiliar file to see what would change and whether forensic strings are present.
2. Default to keeping a backup unless the user explicitly says no.
3. Print the human-readable report after running.

## Out of scope

- **Text-level AI detection.** Use the `humanize` skill. This skill is about file hygiene; that skill is about word choice.
- **Forging a specific past timestamp.** The default `modified` is "now", which is just what Word does on save. Do not use this skill to backdate a file to make it look submitted on time when it wasn't.
- **Impersonation.** Don't override `--creator` to someone other than the real author.
