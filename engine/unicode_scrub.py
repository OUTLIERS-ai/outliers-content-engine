"""
unicode_scrub.py  --  find and remove invisible characters in a draft.

WHAT IT IS FOR
    Text that passes through AI tools and clipboards picks up characters that show as nothing:
    zero-width spaces, soft hyphens, word joiners, direction marks, byte-order marks, and spaces
    that are not ordinary spaces (no-break, thin, ideographic). You cannot see them in an editor,
    a preview or the LinkedIn composer. They survive into the published post, where they break
    search and copy-paste.

HOW IT IS WIRED
    - post_checks.py calls scan() and reports them as a FLAG, never a fail: the fix is
      mechanical and loses nothing, so it is no reason to rewrite a draft.
    - Before you paste a post into LinkedIn, run this file with --fix to clean the draft.

WHAT IT LEAVES ALONE
    Anything you can see. Em dashes, curly quotes, accents and emoji are untouched. The emoji
    presentation selectors (U+FE0E, U+FE0F) are kept too, because removing them can turn a
    coloured emoji into a plain one. Pass --strip-presentation to remove them anyway.

Run:  python engine/unicode_scrub.py <draft.md>          scan (exit 1 if anything found)
      python engine/unicode_scrub.py <draft.md> --fix    clean the file in place (safe write)
      python engine/unicode_scrub.py --text "..."        scan some text
      python engine/unicode_scrub.py --selftest
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402

PRESENTATION_SELECTORS = frozenset({0xFE0E, 0xFE0F})

# Removed outright. Any other "format" character (Unicode category Cf) is removed as well.
STRIP = frozenset({
    0x00AD, 0x034F, 0x061C, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x180E,
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064,
    0x2066, 0x2067, 0x2068, 0x2069, 0x206A, 0x206B, 0x206C, 0x206D, 0x206E, 0x206F,
    0x3164, 0xFEFF, 0xFFA0,
})

# Replaced with an ordinary space.
SPACES = {cp: " " for cp in (0x00A0, 0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005,
                             0x2006, 0x2007, 0x2008, 0x2009, 0x200A, 0x202F, 0x205F, 0x3000)}


def _label(ch: str) -> str:
    return f"U+{ord(ch):04X} {unicodedata.name(ch, 'UNKNOWN')}"


def _classify(cp: int, ch: str, strip_presentation: bool):
    if cp in PRESENTATION_SELECTORS:
        return "strip" if strip_presentation else None
    if 0xE0000 <= cp <= 0xE007F:          # tag characters
        return "strip"
    if cp in STRIP:
        return "strip"
    if cp in SPACES:
        return "space"
    if unicodedata.category(ch) == "Cf":
        return "strip"
    return None


def scan(text: str, *, strip_presentation: bool = False) -> dict:
    """Report invisible characters and odd spaces. Changes nothing."""
    buckets: dict = {}
    for i, ch in enumerate(text):
        kind = _classify(ord(ch), ch, strip_presentation)
        if kind:
            buckets.setdefault((ord(ch), kind), []).append(i)
    hits = [
        {"codepoint": f"U+{cp:04X}", "name": unicodedata.name(chr(cp), "UNKNOWN"),
         "kind": kind, "count": len(offs), "first_offsets": offs[:5]}
        for (cp, kind), offs in sorted(buckets.items(), key=lambda x: (-len(x[1]), x[0][0]))
    ]
    return {"clean": not hits, "total": sum(h["count"] for h in hits), "hits": hits}


def clean(text: str, *, strip_presentation: bool = False):
    """Return (cleaned text, stats). Visible characters are never changed."""
    removed: Counter = Counter()
    replaced: Counter = Counter()
    out = []
    for ch in text:
        kind = _classify(ord(ch), ch, strip_presentation)
        if kind == "strip":
            removed[_label(ch)] += 1
            continue
        if kind == "space":
            replaced[_label(ch)] += 1
            out.append(" ")
            continue
        out.append(ch)
    return "".join(out), {"removed": dict(removed), "replaced": dict(replaced),
                          "removed_count": sum(removed.values()),
                          "replaced_count": sum(replaced.values())}


def fix_file(path: Path, *, strip_presentation: bool = False) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    cleaned, stats = clean(text, strip_presentation=strip_presentation)
    if cleaned != text:
        kitconfig.atomic_write_text(path, cleaned)
    stats["changed"] = cleaned != text
    return stats


def selftest():
    dirty = "Hello\u200b world\u00a0today\u00ad. Caf\u00e9 \u2014 ok \U0001F44D\ufe0f"
    out = []
    r = scan(dirty)
    out.append("pass: finds 3 invisible characters" if r["total"] == 3 else
               "FAIL: expected 3, found %d" % r["total"])
    cleaned, stats = clean(dirty)
    out.append("pass: cleaned text is as expected"
               if cleaned == "Hello world today. Caf\u00e9 \u2014 ok \U0001F44D\ufe0f"
               else "FAIL: clean output %r" % cleaned)
    out.append("pass: visible characters kept (accent, em dash, emoji)"
               if "\u00e9" in cleaned and "\u2014" in cleaned and "\ufe0f" in cleaned
               else "FAIL: visible character changed")
    out.append("pass: a clean text scans clean" if scan("Plain words.")["clean"]
               else "FAIL: clean text reported dirty")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "draft.md"
        p.write_text(dirty, encoding="utf-8")
        s = fix_file(p)
        out.append("pass: --fix rewrites the file safely"
                   if s["changed"] and scan(p.read_text(encoding="utf-8"))["clean"]
                   else "FAIL: file fix")
    good = not any(x.startswith("FAIL") for x in out)
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(out)))
    return "\n".join(out), good


def main() -> int:
    kitconfig.utf8_console()
    ap = argparse.ArgumentParser(description="Find and remove invisible characters.")
    ap.add_argument("path", nargs="?", help="a draft .md to scan")
    ap.add_argument("--text", help="raw text instead of a file")
    ap.add_argument("--fix", action="store_true", help="clean the file in place")
    ap.add_argument("--strip-presentation", action="store_true",
                    help="also remove U+FE0E/U+FE0F (changes how some emoji look)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        text, good = selftest()
        print(text)
        return 0 if good else 1

    if args.fix:
        if not args.path:
            print("--fix needs a file path")
            return 2
        stats = fix_file(Path(args.path), strip_presentation=args.strip_presentation)
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0

    if args.text is not None:
        text = args.text
    elif args.path:
        text = Path(args.path).read_text(encoding="utf-8", errors="replace")
    else:
        text = sys.stdin.read()

    r = scan(text, strip_presentation=args.strip_presentation)
    if args.json:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        print(f"invisible or odd characters: {r['total']}")
        for h in r["hits"]:
            print(f"  [{h['kind']}] {h['codepoint']} {h['name']} x{h['count']} at {h['first_offsets']}")
        if r["clean"]:
            print("clean")
        else:
            print("fix with: python engine/unicode_scrub.py <file> --fix")
    return 0 if r["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
