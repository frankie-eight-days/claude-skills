#!/usr/bin/env python3
"""ZeroGPT AI-detection CLI.

Usage:
  humanize.py <file>                 # score a file
  humanize.py --stdin                # score text from stdin
  humanize.py --text "some text"     # score inline text

Prints JSON to stdout. Exit code 0 if under threshold, 1 if over.

Config: expects ~/.claude/skills/humanize/config.json with {"api_key": "...", "threshold": 10}
"""
import argparse, json, os, sys, urllib.request, urllib.error

CONFIG_PATH = os.path.expanduser("~/.claude/skills/humanize/config.json")
ENDPOINT = "https://api.zerogpt.com/api/detect/detectText"


def load_config():
    # 1. Env var takes precedence
    env_key = os.environ.get("ZEROGPT_API_KEY") or os.environ.get("HUMANIZE_API_KEY")
    if env_key:
        return {"api_key": env_key, "threshold": float(os.environ.get("HUMANIZE_THRESHOLD", "10"))}
    # 2. Config file at ~/.claude/skills/humanize/config.json
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
        if cfg.get("api_key") and not cfg["api_key"].startswith("REPLACE_"):
            return cfg
    sys.stderr.write(
        "No ZeroGPT API key found. Set one of:\n"
        "  1. env var ZEROGPT_API_KEY=<key>\n"
        f"  2. {CONFIG_PATH} with {{\"api_key\": \"<key>\", \"threshold\": 10}}\n"
    )
    sys.exit(2)


def score(text, api_key):
    body = json.dumps({"input_text": text}).encode()
    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={"Content-Type": "application/json", "ApiKey": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
    except urllib.error.HTTPError as e:
        sys.stderr.write(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')}\n")
        sys.exit(3)
    return json.loads(raw)


def strip_markdown_chrome(text):
    """Strip markdown headings and heading-like short lines to reduce noise
    from single-word labels that the detector cannot score."""
    lines = text.splitlines()
    kept = [ln for ln in lines if not ln.strip().startswith("#")]
    return "\n".join(kept).strip()


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("file", nargs="?", help="Path to text/markdown file")
    g.add_argument("--stdin", action="store_true")
    g.add_argument("--text", help="Inline text")
    ap.add_argument("--strip-markdown", action="store_true", help="Strip headings before scoring")
    ap.add_argument("--threshold", type=float, help="Override threshold from config")
    ap.add_argument("--full", action="store_true", help="Dump full API response")
    args = ap.parse_args()

    if args.stdin:
        text = sys.stdin.read()
    elif args.text:
        text = args.text
    else:
        with open(args.file) as f:
            text = f.read()

    if args.strip_markdown:
        text = strip_markdown_chrome(text)

    cfg = load_config()
    threshold = args.threshold if args.threshold is not None else cfg.get("threshold", 10)

    result = score(text, cfg["api_key"])

    if args.full:
        print(json.dumps(result, indent=2))
    else:
        d = result.get("data", {})
        ai_pct = d.get("fakePercentage", 0)
        report = {
            "ai_percent": ai_pct,
            "human_percent": d.get("isHuman", 0),
            "words": d.get("textWords", 0),
            "ai_words": d.get("aiWords", 0),
            "flagged_sentences": d.get("specialSentences", []),
            "threshold": threshold,
            "passes": ai_pct <= threshold,
        }
        print(json.dumps(report, indent=2))

    sys.exit(0 if result.get("data", {}).get("fakePercentage", 100) <= threshold else 1)


if __name__ == "__main__":
    main()
