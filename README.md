# Claude Code skills

Three skills for [Claude Code](https://claude.com/claude-code), packaged for sharing.

## Skills

### `cover-letter/`
Generate a one-page LaTeX cover letter from a resume, a job description, and applicant info. Three highlighted sections: About Me, Why \<Company\>, Why I'd Be a Good Fit. Compiles to PDF with `xelatex`.

### `humanize/`
Iteratively rewrite text until [ZeroGPT](https://www.zerogpt.com/)'s AI-detector score falls under a target threshold (default 10%, cap 6 iterations). Pairs naturally with `cover-letter`. Needs a ZeroGPT API key.

### `deai-office/`
Normalize OOXML internals after scripted editing of Microsoft Office files (`.docx`, `.pptx`, `.xlsx`). Strips the generator fingerprints that `python-docx`, `python-pptx`, `openpyxl`, and LibreOffice leave behind. Does **not** change document content — only OOXML metadata.

## Install

```bash
git clone https://github.com/frankie-eight-days/claude-skills.git
mkdir -p ~/.claude/skills
cp -r claude-skills/cover-letter claude-skills/humanize claude-skills/deai-office ~/.claude/skills/
```

For `humanize`, set the ZeroGPT API key one of two ways:
```bash
export ZEROGPT_API_KEY=<your-key>
# or
cp ~/.claude/skills/humanize/config.json.example ~/.claude/skills/humanize/config.json
# then edit it
```

`cover-letter` needs `xelatex` (TeX Live or MacTeX). `deai-office` needs only Python 3.

## Usage

In Claude Code:
- "write a cover letter for \<job\>" → `cover-letter`
- "humanize this draft" → `humanize`
- "clean up the metadata on this .docx" → `deai-office`

See each skill's `SKILL.md` for full flags.

## Cost analysis: cover-letter + humanize on a $30 budget

Real-world run on a 1-page cover letter (Daniel @ Ciena, ~370 words). Prices are Sonnet 4.6 API rates ($3/M input, $15/M output) as a worst-case proxy for a Claude Code subscription, since flat-rate subscriptions don't bill per token.

| Phase                              | Input tok | Output tok | Cost (Sonnet) |
|------------------------------------|----------:|-----------:|--------------:|
| Cover-letter draft (real run)      |    ~3,500 |     ~1,050 |       $0.026  |
| Humanize loop, 1 rewrite (real)    |    ~2,000 |     ~1,000 |       $0.021  |
| **Real total per letter**          |    ~5,500 |     ~2,050 |     **$0.047**|
| Humanize worst case (6 rewrites)   |   ~20,000 |     ~3,000 |       $0.105  |
| **Worst-case total per letter**    |   ~24,000 |     ~4,050 |     **$0.133**|

**$30 capacity:**
- Typical (1 rewrite): ~**640 letters/month**
- Worst case (humanize maxed): ~**225 letters/month**

Translation: even with the humanize loop running to its 6-iteration cap on every single letter, $30 of API-equivalent usage covers ~225 letters. A Claude Code Pro subscription (which doesn't bill per token at all) will tap out on rate limits long before this becomes a cost concern.

Token counts come from `cover-letter/count_tokens.py` using `chars/4` — within ~15% of true counts for English. Pass `--use-api` if the `anthropic` SDK is installed for exact numbers.

## Real-world humanize result (the same Ciena letter)

| Iter | AI% | Words | Em-dashes | Notes |
|-----:|----:|------:|----------:|-------|
|    1 | 9.1 |   382 |         5 | First draft. Passes ZeroGPT (10% threshold) but visibly AI to a human — em-dash heavy, parallel "On the X side / On the Y side" constructions. |
|    2 | 0.0 |   368 |         0 | Rewrite: stripped every em-dash, broke parallel structures, added contractions, varied sentence length. Register stayed formal first-person. |

**Lesson:** ZeroGPT's score is necessary but not sufficient. The detector under-weights several tells humans pick up on instantly — em-dashes most of all. Treat the score as the floor and do one editorial pass for the visible tells before calling it done. See `humanize/SKILL.md` → "ZeroGPT's blind spots" for the full list.
