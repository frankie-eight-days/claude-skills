---
name: cover-letter
description: Generate a polished LaTeX cover letter from a resume, a job description, and applicant info. Produces a PDF with three clearly highlighted sections — About Me, Why <Company>, Why I'd Be a Good Fit. Use when the user asks to "write a cover letter", "apply to <company>", "draft a CL", etc.
---

# Cover Letter

Generate a tailored LaTeX cover letter from three inputs: resume, job description, and applicant contact info. Output is a compiled PDF with three highlighted sections.

## Tooling location

- `~/.claude/skills/cover-letter/template.tex` — LaTeX template with `{{PLACEHOLDERS}}`
- `~/.claude/skills/cover-letter/render.py` — substitutes placeholders, compiles via `latexmk -xelatex`
- `~/.claude/skills/cover-letter/count_tokens.py` — estimates token usage for the run

## How to use this skill

1. **Collect inputs.** Ask the user for whatever isn't already in hand:
   - Resume (path to `.tex`, `.md`, `.txt`, or `.pdf`)
   - Job description (path or pasted text — save to a temp `.txt` if pasted)
   - Company name, role title, hiring manager (if known)
   - Applicant name, email, phone, location
   - Output directory (default: current working dir)

2. **Read the resume and JD thoroughly.** Extract:
   - From resume: title, years of experience, top 3-5 concrete achievements, technical skills that overlap the JD
   - From JD: company name, exact role title, top 3 required qualifications, anything distinctive about the company / role / mission

3. **Write the three sections.** First-person, professional register. No corporate-speak boilerplate. Specific over generic. Target lengths:
   - **About Me** — 3-5 sentences. Who I am, what I do, why I'm writing.
   - **Why \<Company\>** — 3-5 sentences. Something specific about the company / role / product. Not "I admire your innovation."
   - **Why I'd Be a Good Fit** — 5-7 sentences. Map 2-3 concrete resume achievements to 2-3 specific JD requirements. Quantify where possible.

4. **Build the data JSON.** Write a JSON file with the substitution values:

   ```json
   {
     "name": "Daniel Walsh",
     "email": "danieldw5555@gmail.com",
     "phone": "+1 (438) 336-2382",
     "location": "Montreal, QC",
     "date": "May 11, 2026",
     "company": "Ciena",
     "company_address": "Ottawa, ON",
     "recipient": "Hiring Manager",
     "role": "Analog/Mixed Signal Design Engineer",
     "about_me": "First section content...",
     "why_company": "Second section content...",
     "why_fit": "Third section content...",
     "closing": "Sincerely"
   }
   ```

   Leave `recipient` as `"Hiring Manager"` if no name is known. `closing` defaults to `"Sincerely"`.

5. **Render the PDF.**

   ```bash
   python3 ~/.claude/skills/cover-letter/render.py data.json --out cover-letter-<company>.pdf
   ```

   The script substitutes into `template.tex`, runs `latexmk -xelatex` in a temp dir, copies the PDF out, and prints a one-line summary.

6. **Report token usage** (optional but recommended):

   ```bash
   python3 ~/.claude/skills/cover-letter/count_tokens.py \
     --resume resume.tex --jd jd.txt --output cover-letter-<company>.tex
   ```

   Prints input/output token estimates and API-equivalent cost at current Claude prices.

7. **Optionally chain into `humanize`.** If the user wants to lower the AI-detector score, hand the rendered `.tex` body (or extract the prose) to the `humanize` skill. **Preserve formal first-person register** — cover letters are professional, not casual.

## Section style

- Use **active voice** and concrete verbs ("designed", "led", "shipped"), not passive ("was responsible for").
- **Numbers carry weight.** "Led power electronics for 4 spacecraft programs" beats "extensive aerospace experience."
- **Don't repeat the resume.** The letter should tell the story the resume can't — motivation, judgment, fit.
- **No "I am writing to apply for…"** as the opener. Start with something interesting.

## Gotchas

- The LaTeX template uses `xelatex` (not `pdflatex`) for nicer font rendering. `render.py` invokes `latexmk -xelatex`.
- Escape LaTeX special characters in user-provided strings before substitution: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`. `render.py` handles this for you.
- If a JD is pasted into the chat, save it to a temp `.txt` file first so `count_tokens.py` can measure it.
- If `latexmk` is missing, the script falls back to running `xelatex` twice. If neither is installed, it emits the `.tex` file and points the user at Overleaf.

## Output report

After rendering, print:

```
Cover letter generated.
- Company:        Ciena
- Role:           Analog/Mixed Signal Design Engineer
- Output:         cover-letter-ciena.pdf  (2 pages, 87KB)
- Body word count: 312
- Input tokens:   ~3,800 (resume + JD + template + instructions)
- Output tokens:  ~520 (3 sections + JSON wrapper)
- Estimated API cost (Sonnet): $0.019
```
