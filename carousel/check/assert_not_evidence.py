"""assert_not_evidence: catches lines that tell the reader where a claim came from.

THE RULE
    Where a claim came from matters while you write it. It does not belong on the slide.
    "Twelve clients switched in a month" is a claim. "Twelve clients switched, verified against my
    records" spends words defending the claim instead of making it, and reads as defensive.

WHAT THIS DOES NOT BAN
    Specific numbers, dates and scenes. Those are the substance. It only catches the clause whose
    one job is to point at the source.

Hard fails are clear sourcing clauses. Flags are phrasings that are sometimes fine, so a person
decides.

Usage:  python assert_not_evidence.py --selftest
Standard library only. Python 3.9+.
"""
from __future__ import annotations

import re
import sys

# ---- HARD: the clause exists only to source the claim to the reader --------------------------
PROVENANCE_HARD = [
    (re.compile(r"\bon (?:a |the )?recorded calls?\b", re.I),
     "'on recorded calls' tells the reader the source. State the point instead."),
    (re.compile(r"\bon (?:the )?record\b(?!\s+(?:label|player))", re.I),
     "'on record' narrates the source to the reader."),
    (re.compile(r"\bon tape\b", re.I),
     "'on tape' narrates the source to the reader."),
    (re.compile(r"\bcame off (?:the )?calls?\b", re.I),
     "'came off calls' defends where the material came from instead of delivering it."),
    (re.compile(r"\bverified against\b", re.I),
     "'verified against ...' belongs in your notes, not on the slide."),
    (re.compile(r"\bthe record (?:shows|says|does not show|doesn't show)\b", re.I),
     "'the record shows' is courtroom language. Make the point directly."),
    (re.compile(r"\b(?:i )?went back through\b", re.I),
     "'went back through' narrates the research, not the finding."),
    (re.compile(r"\bif you (?:go |went )?(?:back )?(?:and )?check\b", re.I),
     "inviting the reader to check the claim. That checking is your job, done before posting."),
]

# ---- FLAG: counting-the-evidence frames; fine sometimes, a warning sign in bulk ---------------
PROVENANCE_FLAGS = [
    (re.compile(r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+times\s+in\s+"
                r"(?:a|one|two|three|four|five|six|seven|eight|nine|ten|\d+)?\s*"
                r"(?:days?|weeks?|months?|years?)\b", re.I),
     "an 'X times in Y weeks' frame counts evidence at the reader. Keep it only if the count is "
     "the point, not the proof."),
    (re.compile(r"\b\d+\s+(?:saved\s+)?(?:commits?|changes|edits|revisions)\b", re.I),
     "a count of edits or changes describes the work log. Say what the work produced."),
    (re.compile(r"\b(?:according to|per) (?:my|the) (?:notes|log|records?|transcripts?)\b", re.I),
     "citing your own records inside the copy."),
]


def scan(text: str):
    """Return (hard, flags) for a piece of reader-facing copy."""
    hard, flags = [], []
    if not text:
        return hard, flags
    for rx, msg in PROVENANCE_HARD:
        m = rx.search(text)
        if m:
            hard.append(f"SOURCING ON THE SLIDE: {m.group(0)!r}. {msg}")
    for rx, msg in PROVENANCE_FLAGS:
        m = rx.search(text)
        if m:
            flags.append(f"sourcing phrase: {m.group(0)!r}. {msg}")
    return hard, flags


def scan_slides(slides):
    """Scan every reader-facing field on every slide and report the slide number."""
    hard, flags = [], []
    fields = ("title", "does", "got", "kicker", "kicker_top", "lead", "cta", "idx")
    for s in slides or []:
        blob = " ".join(str(s.get(k) or "") for k in fields)
        h, f = scan(blob)
        n = s.get("n", "?")
        hard += [f"slide {n}: {x}" for x in h]
        flags += [f"slide {n}: {x}" for x in f]
    return hard, flags


def selftest() -> bool:
    # Invented sentences. (expected hard count, expected flag count)
    cases = [
        ("Four times in two weeks, on recorded calls, the owner said the same.", 1, 1),
        ("This came off calls, verified against the invoices.", 2, 0),
        ("Late invoices fell from 41 days to 19 in one quarter.", 0, 0),
        ("At that price, the boring answer is the right one.", 0, 0),
        ("I went back through 40 changes to the budget sheet.", 1, 1),
    ]
    ok = True
    for text, eh, ef in cases:
        h, f = scan(text)
        got = (len(h), len(f))
        good = got == (eh, ef)
        ok = ok and good
        print(f"{'ok  ' if good else 'FAIL'} {got} expected ({eh}, {ef}) :: {text[:60]}")
    print("assert_not_evidence selftest", "PASSED" if ok else "FAILED")
    return ok


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(0 if selftest() else 1)
    if len(sys.argv) > 1:
        h, f = scan(" ".join(sys.argv[1:]))
        print("\n".join(h + f) or "clean")
        sys.exit(1 if h else 0)
    # A Mac has `python3` and no plain `python`; Windows prints exactly as before.
    print(__doc__ if sys.platform != "darwin"
          else re.sub(r"(?<![\w./-])python(?= )", "python3", __doc__))
