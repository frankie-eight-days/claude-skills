---
name: humanize
description: Iteratively rewrite text until a ZeroGPT AI-detector score falls under a target threshold (default 10%). Works on paths, markdown snippets, or inline strings. Use when the user asks to "humanize", "de-AI", "soften", or lower an AI-detector score on written content. Always report the final score and flagged sentences.
---

# Humanize

A ZeroGPT-backed ralph loop. Claude rewrites the text, the skill scores it, Claude rewrites again, loop until the score falls under the configured threshold.

## Tooling location

- `~/.claude/skills/humanize/humanize.py` — CLI wrapper around the ZeroGPT API
- `~/.claude/skills/humanize/config.json` (user-created) OR env var `ZEROGPT_API_KEY` — holds the API key. The config file is optional; the env var wins if both are set.
- `~/.claude/skills/humanize/config.json.example` — template

## First-time setup

If no config / env var is present, the script exits with setup instructions. User creates either:

```bash
# Option 1: env var (recommended — doesn't persist)
export ZEROGPT_API_KEY=<key>

# Option 2: config file (persists across sessions)
cat > ~/.claude/skills/humanize/config.json <<'EOF'
{"api_key": "<key>", "threshold": 10}
EOF
```

## Usage

```bash
# Score a file
python3 ~/.claude/skills/humanize/humanize.py path/to/draft.md

# Score stdin
cat draft.md | python3 ~/.claude/skills/humanize/humanize.py --stdin

# Inline text
python3 ~/.claude/skills/humanize/humanize.py --text "some sentence to score"

# Strip markdown headings before scoring (reduces noise from short labels)
python3 ~/.claude/skills/humanize/humanize.py --strip-markdown path/to/draft.md

# Custom threshold (default 10)
python3 ~/.claude/skills/humanize/humanize.py --threshold 5 path/to/draft.md

# Full raw API response
python3 ~/.claude/skills/humanize/humanize.py --full path/to/draft.md
```

Output is JSON:
```json
{
  "ai_percent": 6.7,
  "human_percent": 100,
  "words": 1006,
  "ai_words": 109,
  "flagged_sentences": [],
  "threshold": 10,
  "passes": true
}
```

Exit code is 0 if under threshold, 1 if over.

## Ralph loop (how Claude should use this)

1. Score the initial draft. Note `ai_percent` and any `flagged_sentences`.
2. If under threshold → stop, report final score.
3. If over threshold → rewrite. Focus the rewrite on:
   - The `flagged_sentences` if any are returned.
   - Breaking balanced / parallel sentence constructions.
   - Reducing essay-style transitions ("Furthermore", "Moreover", "In addition").
   - Adding rougher transitions ("On top of that", "Honestly", "Turns out").
   - Using more contractions where the register permits.
   - Mixing short fragments with longer sentences.
   - **Stripping em-dashes (`—`).** ZeroGPT under-weights them, but they are the single most visible AI tell to a human reviewer. Replace with periods, commas, or restructure entirely.
4. Re-score. Loop.
5. Stop once under threshold OR after 6 iterations (report best score and ask the user for direction).

## Output report

After the loop terminates, always print a short report like:

```
Humanize complete.
- Final score: 4.9% AI / 100% human
- Words: 215
- Flagged sentences: (none)
- Iterations: 3
- File: path/to/draft.md
```

## Tone preservation

Sometimes humanization pulls the text too far toward casual. If the user specified formal / academic / professional register, preserve it. Do not substitute casual slang for formal phrasing just to drive down the score. If casual changes are needed for the score, flag that trade-off in the report.

## Gotchas

- Very short text (<50 words) scores unreliably.
- Single-word "sentences" (section headings, bullet labels) are sometimes flagged but are not real AI tells — they just can't be scored.
- Bullet lists tend to score higher than flowing prose. If the content can be prose, prefer prose.
- Markdown headings count as "sentences" to the detector. Use `--strip-markdown` when scoring a markdown document to avoid noise.
- ZeroGPT rate-limits free-tier keys. Space out calls if scoring many files in a row.

## ZeroGPT's blind spots

ZeroGPT's score is necessary but not sufficient. A draft can pass the 10% threshold and still read as AI to a human reviewer. The detector under-weights several tells that humans pick up on instantly:

- **Em-dashes (`—`)** — *the* dead giveaway in 2025/2026 LLM output. The detector barely penalises them; humans clock them immediately. Default to zero em-dashes unless one is genuinely the cleanest punctuation choice.
- **Perfectly balanced parallel structures** — "On the analog side... On the digital side..." / "Not only... but also..." / triplets that fall into rhythm. Real human writing varies more.
- **Smooth connector phrases** — "maps directly onto", "lines up tightly with", "happens to be", "exactly the kind of". They polish too cleanly.
- **Cliché commitment verbs** — "genuinely excited", "deeply passionate", "thrilled to" — universally read as AI in cover letters and similar professional writing.

**Workflow:** treat the ZeroGPT score as the floor, not the ceiling. Even when a draft scores under threshold on iteration 1, do one editorial pass for the tells above before reporting it as done. If the rewrite changes the score, log both. If it doesn't, the rewrite was still worth doing — humans aren't running a detector.
