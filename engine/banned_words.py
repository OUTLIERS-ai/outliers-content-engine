"""
banned_words.py  --  YOUR banned words, from your-voice/banned_words.json.

These are different from the machine-filler list in rule_tables.py. That list is general. This
one is personal: words and phrases you have cut from drafts more than once and never want to see
again. It ships empty. You fill it.

THE FILE (your-voice/banned_words.json)
    hard_words       a draft containing one of these fails the check
    soft_words       reported for you to look at, never a fail
    allowed_phrases  phrases that are fine even though they contain a banned word
                     (ban "pivot", allow "pivot table")
    replace_with     optional, word -> what to say instead, shown in the message

HOW MATCHING WORKS
    - Case does not matter. "Synergy" matches "synergy".
    - Whole words and phrases only. Banning "art" does not catch "start".
    - A * at the end matches any ending: "leverag*" catches leverage, leveraged, leveraging.
    - Allowed phrases are blanked out before the scan, so a banned word inside one is not reported.

Why context carve-outs and not a flat sweep: a check that fires on ordinary English gets
ignored, which is worse than no check. If a word is fine in one sense, add that sense to
allowed_phrases rather than taking the word off the list.

Run:  python engine/banned_words.py <draft.md> [...]
      python engine/banned_words.py --selftest
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kitconfig  # noqa: E402

_loaded = None


def _strings(v):
    return [x.strip() for x in (v or []) if isinstance(x, str) and x.strip()]


def load(path=None):
    """Read the banned words file. A missing file means no personal bans, with a warning."""
    global _loaded
    if path is None and _loaded is not None:
        return _loaded
    p = Path(path) if path else kitconfig.resolve(kitconfig.BANNED_WORDS_FILE)
    data = {"hard_words": [], "soft_words": [], "allowed_phrases": [], "replace_with": {}}
    if p.exists():
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit("%s is not valid JSON: %s" % (kitconfig.rel(p), exc))
        data["hard_words"] = _strings(raw.get("hard_words"))
        data["soft_words"] = _strings(raw.get("soft_words"))
        data["allowed_phrases"] = _strings(raw.get("allowed_phrases"))
        rw = raw.get("replace_with") or {}
        data["replace_with"] = {str(k).lower(): str(v) for k, v in rw.items()
                                if isinstance(v, (str, list))}
    else:
        print("note: %s not found, so no personal banned words are checked."
              % kitconfig.rel(p), file=sys.stderr)
    if path is None:
        _loaded = data
    return data


def _pattern(entry):
    """A word or phrase -> a whole-word regex. Trailing * matches any word ending."""
    wild = entry.endswith("*")
    core = entry.rstrip("*").strip()
    parts = [re.escape(w) for w in core.split()]
    rx = r"\s+".join(parts)
    if wild:
        rx += r"\w*"
    return re.compile(r"(?<!\w)" + rx + r"(?!\w)", re.I)


def _blank_allowed(text, allowed):
    """Replace allowed phrases with spaces of the same length, so positions stay put."""
    for phrase in allowed:
        rx = _pattern(phrase)
        text = rx.sub(lambda m: " " * len(m.group(0)), text)
    return text


def _suggest(entry, data):
    alt = data["replace_with"].get(entry.lower())
    if isinstance(alt, list):
        alt = ", ".join(str(x) for x in alt)
    return (" -- say instead: %s" % alt) if alt else ""


def scan(text, data=None):
    """Return (hard, soft) messages."""
    data = data if data is not None else load()
    visible = _blank_allowed(text, data["allowed_phrases"])
    hard, soft = [], []
    for entry in data["hard_words"]:
        for m in _pattern(entry).finditer(visible):
            hard.append("BANNED WORD (your list): %r%s" % (m.group(0), _suggest(entry, data)))
    for entry in data["soft_words"]:
        for m in _pattern(entry).finditer(visible):
            soft.append("word on your watch list: %r%s" % (m.group(0), _suggest(entry, data)))
    return hard, soft


def selftest():
    data = {
        "hard_words": ["synergy", "circle back", "crush*"],
        "soft_words": ["honestly"],
        "allowed_phrases": ["crush the garlic"],
        "replace_with": {"synergy": "say what the two teams actually did together"},
    }
    cases = [
        ("We found real synergy.", True, "hard word"),
        ("Let's circle   back on Friday.", True, "phrase across extra spaces"),
        ("She was crushing it.", True, "wildcard ending"),
        ("First crush the garlic.", False, "allowed phrase"),
        ("The synergistic plan.", False, "whole words only, no wildcard"),
        ("Honestly, it was fine.", False, "soft word is not a fail"),
        ("A start is an art.", False, "no match inside other words"),
    ]
    out, good = [], True
    for text, want, why in cases:
        hard, _ = scan(text, data)
        ok = bool(hard) == want
        good = good and ok
        out.append("%s %-40r %s" % ("pass:" if ok else "FAIL:", text, why))
    hard, soft = scan("Honestly, synergy.", data)
    ok = bool(soft) and "say instead" in hard[0]
    good = good and ok
    out.append("%s soft words reported and replacement shown" % ("pass:" if ok else "FAIL:"))
    out.append("SELFTEST %s (%d checks)" % ("PASSED" if good else "FAILED", len(cases) + 1))
    return "\n".join(out), good


def main(argv):
    kitconfig.utf8_console()
    if "--selftest" in argv:
        text, good = selftest()
        print(text)
        return 0 if good else 1
    if len(argv) < 2:
        print(kitconfig.for_this_computer(__doc__))
        return 2
    if "-h" in argv or "--help" in argv:
        print(kitconfig.for_this_computer(__doc__))
        return 0
    worst = 0
    for a in argv[1:]:
        if a.startswith("-"):
            print("refused: unknown option %r. Valid options: --selftest, --help. "
                  "Otherwise give file paths to scan." % a)
            return 2
        if not Path(a).is_file():
            print("%s: not found" % a)
            worst = 2
            continue
        hard, soft = scan(Path(a).read_text(encoding="utf-8", errors="replace"))
        print("\n=== %s: %s" % (a, "BANNED WORD PRESENT" if hard else "clean"))
        for h in hard:
            print("  HARD:", h)
        for s in soft:
            print("  flag:", s)
        if hard:
            worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv))
