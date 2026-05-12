#!/usr/bin/env python3
"""Estimate token usage for a cover-letter generation run.

Estimates input vs output tokens and converts to API-equivalent cost at
current Claude prices.

Usage:
  count_tokens.py --resume resume.tex --jd jd.txt --output cover-letter.tex
  count_tokens.py --resume resume.tex --jd jd.txt --output cover-letter.tex --model sonnet-4-6
  count_tokens.py --resume resume.tex --jd jd.txt --output cover-letter.tex --json

Methodology:
- Input tokens   = (resume + JD + template + instruction overhead) chars / 4
- Output tokens  = (generated cover letter body) chars / 4
- Char/token of 4 is the rough English average — actual will be within ~15%.
- "Instruction overhead" is a fixed estimate of the SKILL.md guidance Claude
  reads when invoking this skill.

If the `anthropic` SDK is installed and ANTHROPIC_API_KEY is set, the script
uses the official token counter instead of the chars/4 heuristic.
"""
import argparse, json, os, sys

# Pricing in USD per million tokens — update as Anthropic changes prices.
PRICING = {
    "opus-4-7":     {"input": 15.00, "output": 75.00},
    "opus-4-6":     {"input": 15.00, "output": 75.00},
    "sonnet-4-6":   {"input":  3.00, "output": 15.00},
    "sonnet-4-5":   {"input":  3.00, "output": 15.00},
    "haiku-4-5":    {"input":  1.00, "output":  5.00},
}

# Approximate token counts for the fixed parts of a skill invocation.
# (SKILL.md content Claude reads + system prompt overhead.)
INSTRUCTION_OVERHEAD_TOKENS = 1200


def chars_to_tokens(s):
    return max(1, len(s) // 4)


def try_anthropic_count(text, model="claude-sonnet-4-5"):
    try:
        import anthropic
    except ImportError:
        return None
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        client = anthropic.Anthropic()
        r = client.messages.count_tokens(
            model=model,
            messages=[{"role": "user", "content": text}],
        )
        return r.input_tokens
    except Exception:
        return None


def read(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resume", required=True)
    ap.add_argument("--jd", required=True)
    ap.add_argument("--output", required=True, help="Generated cover letter (.tex, .md, or data.json)")
    ap.add_argument("--template", help="Path to LaTeX template (default: skill's template.tex)")
    ap.add_argument("--model", default="sonnet-4-6", choices=list(PRICING.keys()))
    ap.add_argument("--use-api", action="store_true",
                    help="Use anthropic SDK's messages.count_tokens if available")
    ap.add_argument("--budget", type=float, default=30.0, help="Monthly budget USD (default: 30)")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    skill_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = args.template or os.path.join(skill_dir, "template.tex")

    resume_text = read(args.resume)
    jd_text = read(args.jd)
    template_text = read(template_path)
    output_text = read(args.output)

    if args.use_api:
        input_combined = resume_text + "\n\n" + jd_text + "\n\n" + template_text
        in_tok = try_anthropic_count(input_combined) or chars_to_tokens(input_combined)
        out_tok = try_anthropic_count(output_text) or chars_to_tokens(output_text)
        method = "anthropic-sdk" if try_anthropic_count("test") is not None else "chars/4"
    else:
        in_tok = (
            chars_to_tokens(resume_text)
            + chars_to_tokens(jd_text)
            + chars_to_tokens(template_text)
            + INSTRUCTION_OVERHEAD_TOKENS
        )
        out_tok = chars_to_tokens(output_text)
        method = "chars/4"

    price = PRICING[args.model]
    cost = (in_tok / 1_000_000) * price["input"] + (out_tok / 1_000_000) * price["output"]
    letters_per_budget = int(args.budget / cost) if cost > 0 else 0

    report = {
        "model": args.model,
        "method": method,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "input_breakdown": {
            "resume_chars": len(resume_text),
            "jd_chars": len(jd_text),
            "template_chars": len(template_text),
            "instruction_overhead_tokens": INSTRUCTION_OVERHEAD_TOKENS,
        },
        "cost_usd": round(cost, 4),
        "budget_usd": args.budget,
        "letters_per_budget": letters_per_budget,
        "pricing_per_million": price,
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Token usage estimate (method: {method}):")
        print(f"  Model:           {args.model}")
        print(f"  Input tokens:    {in_tok:,}")
        print(f"  Output tokens:   {out_tok:,}")
        print(f"  Cost per run:    ${cost:.4f}")
        print(f"  ${args.budget:.0f} budget:    {letters_per_budget:,} letters")


if __name__ == "__main__":
    main()
