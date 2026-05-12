#!/usr/bin/env python3
"""Render a cover letter from a JSON data file + the LaTeX template.

Usage:
  render.py data.json                            # writes cover-letter.pdf next to data.json
  render.py data.json --out path/to/letter.pdf   # explicit output path
  render.py data.json --tex-only                 # emit only the .tex file, no compile
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(SKILL_DIR, "template.tex")

# LaTeX special characters that need escaping in user-provided text.
LATEX_ESCAPE = {
    "\\": r"\textbackslash{}",
    "&":  r"\&",
    "%":  r"\%",
    "$":  r"\$",
    "#":  r"\#",
    "_":  r"\_",
    "{":  r"\{",
    "}":  r"\}",
    "~":  r"\textasciitilde{}",
    "^":  r"\textasciicircum{}",
}

REQUIRED_FIELDS = [
    "name", "email", "phone", "location", "date",
    "company", "company_address", "recipient", "role",
    "about_me", "why_company", "why_fit",
]


def escape_latex(s):
    if s is None:
        return ""
    # Escape backslashes first, then other specials.
    out = []
    for ch in str(s):
        out.append(LATEX_ESCAPE.get(ch, ch))
    return "".join(out)


def fill_template(template, data):
    """Replace <<KEY>> placeholders. Missing keys raise."""
    def repl(m):
        key = m.group(1).lower()
        if key not in data:
            raise KeyError(f"template uses <<{m.group(1)}>> but data lacks key '{key}'")
        return escape_latex(data[key])
    return re.sub(r"<<([A-Z_]+)>>", repl, template)


def compile_pdf(tex_path, workdir):
    """Try latexmk; fall back to xelatex twice; return path to PDF or None."""
    tex_dir = os.path.dirname(tex_path)
    tex_name = os.path.basename(tex_path)

    if shutil.which("latexmk"):
        cmd = ["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_name]
    elif shutil.which("xelatex"):
        cmd = ["xelatex", "-interaction=nonstopmode", "-halt-on-error", tex_name]
    else:
        return None, "no latexmk or xelatex on PATH"

    runs = 1 if cmd[0] == "latexmk" else 2
    last_log = ""
    for _ in range(runs):
        r = subprocess.run(cmd, cwd=tex_dir, capture_output=True, text=True)
        last_log = r.stdout + r.stderr
        if r.returncode != 0:
            return None, last_log

    pdf = tex_path[:-4] + ".pdf" if tex_path.endswith(".tex") else None
    if pdf and os.path.exists(pdf):
        return pdf, last_log
    return None, last_log


def word_count(data):
    body = " ".join(data.get(k, "") for k in ("about_me", "why_company", "why_fit"))
    return len(body.split())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data", help="JSON file with substitution values")
    ap.add_argument("--out", help="Output PDF path (default: <data-stem>.pdf alongside JSON)")
    ap.add_argument("--tex-only", action="store_true", help="Emit .tex only, do not compile")
    args = ap.parse_args()

    with open(args.data) as f:
        data = json.load(f)

    missing = [k for k in REQUIRED_FIELDS if k not in data]
    if missing:
        sys.stderr.write(f"data JSON missing required fields: {missing}\n")
        sys.exit(2)
    data.setdefault("closing", "Sincerely")

    with open(TEMPLATE_PATH) as f:
        template = f.read()
    tex_out = fill_template(template, data)

    data_path = os.path.abspath(args.data)
    stem = os.path.splitext(os.path.basename(data_path))[0]
    out_pdf = args.out or os.path.join(os.path.dirname(data_path), f"{stem}.pdf")
    out_pdf = os.path.abspath(out_pdf)

    if args.tex_only:
        tex_path = os.path.splitext(out_pdf)[0] + ".tex"
        with open(tex_path, "w") as f:
            f.write(tex_out)
        print(f"Wrote {tex_path}")
        return

    with tempfile.TemporaryDirectory(prefix="cover-letter-") as work:
        tex_path = os.path.join(work, f"{stem}.tex")
        with open(tex_path, "w") as f:
            f.write(tex_out)
        pdf, log = compile_pdf(tex_path, work)
        if not pdf:
            # Drop the .tex next to the intended PDF so user can compile manually.
            fallback = os.path.splitext(out_pdf)[0] + ".tex"
            shutil.copy2(tex_path, fallback)
            sys.stderr.write(
                f"PDF compile failed. The .tex was saved to {fallback}.\n"
                f"Last 30 lines of LaTeX output:\n"
                + "\n".join(log.splitlines()[-30:])
                + "\n"
            )
            sys.exit(1)
        shutil.copy2(pdf, out_pdf)

    size_kb = os.path.getsize(out_pdf) // 1024
    print(
        f"Cover letter generated.\n"
        f"- Company:        {data.get('company')}\n"
        f"- Role:           {data.get('role')}\n"
        f"- Output:         {out_pdf}  ({size_kb}KB)\n"
        f"- Body words:     {word_count(data)}"
    )


if __name__ == "__main__":
    main()
