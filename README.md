# Claude Code skills

Two skills for [Claude Code](https://claude.com/claude-code), packaged for sharing.

## Skills

### `humanize/`
Iteratively rewrite text until [ZeroGPT](https://www.zerogpt.com/)'s AI-detector score falls under a target threshold (default 10%). Claude rewrites, the skill scores it, Claude rewrites again — loop until the score is low enough.

Needs a ZeroGPT API key.

### `deai-office/`
Normalize OOXML internals after scripted editing of Microsoft Office files (`.docx`, `.pptx`, `.xlsx`). Cleans up the generator fingerprints that `python-docx`, `python-pptx`, `openpyxl`, and LibreOffice leave behind so the file looks like a conventional Word / PowerPoint / Excel save.

Does **not** change document content — only OOXML metadata. For text-level cleanup, use `humanize`.

## Install

Drop the folders into `~/.claude/skills/`:

```bash
git clone https://github.com/frankie-eight-days/claude-skills.git
mkdir -p ~/.claude/skills
cp -r claude-skills/humanize ~/.claude/skills/
cp -r claude-skills/deai-office ~/.claude/skills/
```

For `humanize`, set up a config file or env var with your ZeroGPT API key:

```bash
# Option 1: env var
export ZEROGPT_API_KEY=<your-key>

# Option 2: config file
cp ~/.claude/skills/humanize/config.json.example ~/.claude/skills/humanize/config.json
# then edit config.json to put your key in
```

`deai-office` needs no configuration — just Python 3.

## Usage

After install, in Claude Code:

- "humanize this draft" → triggers the `humanize` skill
- "clean up the metadata on this .docx" → triggers `deai-office`

See each skill's `SKILL.md` for the full description and CLI flags.
